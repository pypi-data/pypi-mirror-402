# getfactormodels: https://github.com/x512/getfactormodels
# Copyright (C) 2025-2026 S. Martin <x512@pm.me>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Distributed WITHOUT ANY WARRANTY. See LICENSE for full terms.
import pyarrow as pa
import pyarrow.compute as pc
from getfactormodels.models.base import CompositeModel, RegionMixin
from getfactormodels.utils.utils import read_from_fred


def read_from_abs(flow_id: str, params: str, measure_val: int | str, col_name: str, client=None) -> pa.Table:
    """Sleek ABS reader for specific measures."""
    base_url = "https://data.api.abs.gov.au/rest/data"
    url = f"{base_url}/{flow_id}/{params}?detail=dataonly&format=csv"
    
    _client = client if client else _HttpClient()
    data = _client.download(url) # Uses your new streaming/get logic
    
    table = pv.read_csv(BytesIO(data))
    
    # Filter by the specific measure (e.g., 10 for ERP, 'C' for Wages)
    mask = pc.equal(table.column("MEASURE"), pa.scalar(measure_val))
    table = table.filter(mask).select(["TIME_PERIOD", "OBS_VALUE"])
    
    table = table.rename_columns(["date", col_name])
    return parse_quarterly_dates(table)

class ConditionalCAPM(CompositeModel, RegionMixin):
    """Conditional CAPM (CCAPM) of Jaganathan & Wang (1996).

    An implementations of the 'Premium-Labour', or 'Human Capital'
    CCAPM of Jaganathan and Wang (1996).

    - LBR: Smooth growth in per-capita labor income.
    - PREM: Lagged yield spread (Baa - Aaa) as a conditioning variable.

    References:
        R. Jagannathan and Z. Wang (1996). The conditional CAPM
        and the cross-section of expected returns. The Journal of
        Finance 51: 3–53.

    """
    @property 
    def _regions(self) -> list[str]: return ['usa']
    
    def __init__(self, frequency='m', **kwargs):
        super().__init__(**kwargs)
        self.frequency = frequency.lower()
        self.region = kwargs.get('region', 'usa')

    @property
    def _precision(self) -> int: return 8

    @property
    def _frequencies(self) -> list[str]: return ['m', 'q', 'y']

    @property
    def schema(self) -> pa.Schema:
        return pa.Schema([
            ('date', pa.date32()),
            ('LBR', pa.float64()),
            ('PREM', pa.float64()),
        ])

    def _construct(self, client) -> pa.Table:
        # 1. Define ABS series
        # Format: FlowID: (ColName, SDMX_Filter)
        abs_series = {
            "ABS,ERP_COMP_Q,1.0.0": ("pop", ".AUS.Q"),
            "ABS,ANA_INC,1.0.0": ("income", ".COE_WSS....Q"),
        }
        
        # 2. Get Quarterly data from ABS
        q_table = read_from_abs(abs_series, frequency='q', client=client)
        
        # 3. Scale values (Wages are usually in $M, Pop in 000s)
        # Assuming you want raw numbers for the ratio
        q_table = q_table.set_column(1, "pop", pc.multiply(q_table.column("pop"), 1000.0))
        
        # 4. Interpolate to Monthly
        # Since spread is monthly, we interpolate income/pop to match
        m_income = self._interpolate_q_to_m(q_table.select(["income"]))
        m_pop = self._interpolate_q_to_m(q_table.select(["pop"]))

    def _resample(self, table: pa.Table) -> pa.Table:
        """Downsample monthly to Q or Y by taking the last available month."""
        if self.frequency == 'm':
            return table
        months = pc.month(table.column("date"))

        if self.frequency == 'q':
            mask = pc.is_in(months, value_set=pa.array([3, 6, 9, 12]))
        elif self.frequency == 'y':
            mask = pc.equal(months, 12)
        else:
            return table

        return table.filter(mask).combine_chunks()


    def _jw_calc(self, table: pa.Table) -> pa.Table:
        """Calculate JW factors.

        - R_LBR(t): (L(t-1) + L(t-2)) / (L(t-2) + L(t-3)) - 1
        - PREM(t): Lagged spread (Baa - Aaa) at t-1
        """
        # Per Capita Labor Income (L)
        l_pc = pc.divide(table.column("income"), table.column("pop"))
        
        # Credit spread/default risk (Baa - Aaa), pct to decimal here
        spread = pc.divide(pc.subtract(table.column("baa"), table.column("aaa")), 100.0)

        n_total = table.num_rows
        # 3 lags for LBR calculation (t-1, t-2, t-3). Result starts at index 3.
        n_final = n_total - 3
        if n_final <= 0:
            raise ValueError("Insufficient data to calculate lags.")

        # Calculate R_LBR:
        # slice for the formula
        l_tm1 = l_pc.slice(2, n_final)
        l_tm2 = l_pc.slice(1, n_final)
        l_tm3 = l_pc.slice(0, n_final)

        # calc: (l_tm1 + l_tm2) / (l_tm2 + l_tm3) - 1
        r_lbr = pc.subtract(pc.divide(pc.add(l_tm1, l_tm2), pc.add(l_tm2, l_tm3)), 1.0)

        # PREM is the spread at t-1. Return period t at index 3, t-1 is index 2
        prem_lagged = spread.slice(2, n_final)

        dates = table.column("date").slice(3, n_final)

        return pa.Table.from_arrays(
            [dates, r_lbr, prem_lagged],
            names=["date", "LBR", "PREM"],
        )

    def _downsample(self, table: pa.Table) -> pa.Table:
        """Efficiently downsample monthly factors to Q or Y by filtering for EOP months."""
        if self.frequency == 'm':
            return table
        
        months = pc.month(table.column("date")) # extract the month only!
        
        if self.frequency == 'q':
            mask = pc.is_in(months, value_set=pa.array([3, 6, 9, 12]))
            table = table.filter(mask)
        
        elif self.frequency == 'y':
            # December only
            mask = pc.equal(months, 12)
            table = table.filter(mask)
            
        return table.combine_chunks()


    def _interpolate_q_to_m(self, table: pa.Table, col) -> pa.Table:
        income = table.column("income")

        q_prev = income.slice(0, len(income) - 1)
        q_curr = income.slice(1)

        # growth = (curr / prev) ^ (1/3)
        ratio = pc.divide(q_curr, q_prev)
        growth_rate = pc.power(ratio, 1/3)

        # m1 = prev / 3.0  or 1.0 if it's an index.
        m1 = pc.divide(q_prev, 3.0)
        m2 = pc.multiply(m1, growth_rate)
        m3 = pc.multiply(m2, growth_rate)

        # 3. The "Zip" Step: Interleave
        # We create a constant indices array: [0, 1, 2, 0, 1, 2, ...]
        # Since we can't use numpy, we build it via Arrow's repeat/concat logic
        num_quarters = len(m1)

        # Create the pattern [0, 1, 2]
        pattern = pa.array([0, 1, 2], type=pa.int8())

        # Repeat the pattern for every quarter and flatten
        # Note: Using a list comprehension here is okay for small arrays,
        # but for pure performance we use interleave_arrays
        indices = pa.concat_arrays([pattern] * num_quarters)

        # This "zips" m1, m2, and m3 into one long array
        monthly_income = pc.interleave_arrays([m1, m2, m3], indices)

        # return from arrays? or table?
        return pa.Table.from_arrays([monthly_income], names=["income"])
    





    # ignore this ------------------------------------------------------------------------
    def _abs_to_table(self) -> pa.Table:
        ...

    def _download_aus_erp(self, client=None) -> pa.Table:
        """Downloads population data from ABS.

        Downloads the "Population and components of change - national"
        dataset from the ABS. Quarterly data.

        Data:
        Data Item:
        """
        # ABS REST - AUS: Quarterly (Q): Estimated Resident Population (ERP)
        base_url = "https://data.api.abs.gov.au/rest/data"
        url = f"{base_url}/ABS,ERP_COMP_Q,1.0.0/.AUS.Q?detail=dataonly&format=csv"

        _client = client if client else _HttpClient()

        data = _client.stream(url, cache_ttl=20000)

        table = pv.read_csv(io.BytesIO(data))

        # ERP (MEASURE = 10)
        mask = pc.equal(table.column("MEASURE"), 10)
        pop_t = table.filter(mask)

        pop_t = pop_t.select(["TIME_PERIOD", "OBS_VALUE"])
        pop_t = pop_t.rename_columns(["date", "pop"])

        # Data's in units of 000's
        abs_pop_table = pop_t.set_column(
            1, "pop", pc.multiply(pop_table.column("pop"), 1000.0),
        )
        # parse qtrly, offset
        abs_pop_table = parse_quarterly_dates(abs_pop_table)
        table = offset_period_eom(abs_pop_table)

        table.validate()

        print(table)


    def _download_aus_wages(self, client=None) -> pa.Table:
        """Downloads wage date from ABS.

        Quarterly data.

        Data: Australian National Accounts – Income from Gross Domestic Product
        Data Item: Compensation of employees - Wages and salaries
        """
        url = "https://data.api.abs.gov.au/rest/data/ABS,ANA_INC,1.0.0/.COE_WSS....Q?detail=dataonly&format=csv"
        _client = client if client else _HttpClient()

        data = _client.stream(url, cache_ttl=20000)
        table = pv.read_csv(io.BytesIO(data))

        mask = pc.and_(
            pc.equal(raw_table.column("TSEST"), pa.scalar(20)),
            pc.equal(raw_table.column("MEASURE"), pa.scalar("C")),
        )

        table = table.filter(mask)

        # 3. Now select and rename
        table = table.select(["TIME_PERIOD", "OBS_VALUE"])
        table = table.rename_columns(["date", "income"])

        # 4. Process dates (YYYY-QX -> Date32)
        #d_str = table.column("date").cast(pa.string())
        #years = pc.utf8_slice_codeunits(d_str, start=0, stop=4)
        #q_nums = pc.utf8_slice_codeunits(d_str, start=6, stop=7)
        #m_map = pa.array(["03", "06", "09", "12"])
        #m_idx = pc.subtract(q_nums.cast(pa.int32()), 1)
        #months = pc.take(m_map, m_idx)
        #iso_dates = pc.binary_join_element_wise(pc.binary_join_element_wise(years, months, "-"), pa.scalar("01"), "-")
        
        table = parse_quarterly_dates(table)
        table = offset_period_eom(table)

        #table = table.set_column(0, "date")
        #table = table.rename_columns([0, 'date'])
        table = table.sort_by("date")

        table





#### MOVED HERE FOR A BIT

# getfactormodels: https://github.com/x512/getfactormodels
# Copyright (C) 2025-2026 S. Martin <x512@pm.me>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Distributed WITHOUT ANY WARRANTY. See LICENSE for full terms.
import io
import pyarrow as pa
import pyarrow.csv as pv
from getfactormodels.models.base import CompositeModel, RegionMixin
from getfactormodels.utils.date_utils import (
    offset_period_eom,
    parse_quarterly_dates,
)
from getfactormodels.utils.http_client import _HttpClient


# might rename PremiumLabourCCAPM
#class PremiumLabourCAPM(CompositeModel, RegionMixin):
class ConditionalCAPM(CompositeModel, RegionMixin):
    """Conditional CAPM (CCAPM) of Jaganathan & Wang (1996).

    An implementations of the 'Premium-Labour', or 'Human Capital' 
    CCAPM of Jaganathan and Wang (1996). 

    Data from FRED. Monthly, except income, 

    - LBR: Smooth growth in per-capita labor income.
    - PREM: Lagged yield spread (Baa - Aaa) as a conditioning variable.

    References:
        R. Jagannathan and Z. Wang (1996). The conditional CAPM
        and the cross-section of expected returns. The Journal of 
        Finance 51: 3–53.

    """
    _regions = ["usa", "aus"]
    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        super().__init__(**kwargs)
        self.region = region

    @property
    def _frequencies(self) -> list[str]:
        return ['m', 'q', 'y']

    @property 
    def _precision(self) -> int:
        return 8

    @property
    def _regions(self) -> list[str]:
        return ['aus', 'usa'] #testin

    @property 
    def schema(self) -> pa.Schema:
        return pa.Schema([
            ('date', pa.date32()),
            ('LBR', pa.float64()),
            ('PREM', pa.float64()),
        ])


    def _construct(self, client) -> pa.Table:
        m_series = {
            "POPTHM": "pop",
            "BAA": "baa",
            "AAA": "aaa",
        } if self.region == 'usa' else {
            # Testing something...
            "POPTOTAUA647NWDB": "pop",
            "IR3TBB01AUM156N": "baa",
            "IRLTLT01AUM156N": "aaa",
        }
        
        m_table = read_from_fred(series=m_series, frequency='m', client=client)
        m_table = offset_period_eom(m_table, 'm')
        
        # Income data from FRED (COE) is quarterly.
        q_id = "LCWRTT01AUQ661N" if self.region == 'aus' else "COE"

        q_table = read_from_fred(series={q_id: "income"}, frequency='q', client=client)
        q_table = offset_period_eom(q_table, frequency='q').combine_chunks()

        # helper: quarterly COE to monthly 
        inc_table = self._q_wages_to_m(q_table)

        data_table = m_table.join(inc_table, keys="date", join_type="inner")
        data_table = data_table.sort_by("date").combine_chunks()

        jw_table = self._jw_calc(data_table)

        # scale PREM, not importing scale_to_decimal just for this
        prem_dec = pc.divide(jw_table.column("PREM"), 100.0)

        table = jw_table.set_column(2, "PREM", prem_dec).combine_chunks()
        return self._downsample(table)
    
        #ff = FamaFrenchFactors(model='3', frequency=self.frequency).load(client=client)
        #mkt = select_table_columns(ff.data, ['Mkt-RF', 'RF'])
        #return jw_table.join(mkt, keys="date", join_type="inner").combine_chunks()


    def _jw_calc(self, table: pa.Table) -> pa.Table:
        """J&W (1996) factor construction logic."""
        # Per Capita Labor Income (L)
        l_pc = pc.divide(table.column("income"), table.column("pop"))
        spread = pc.subtract(table.column("baa"), table.column("aaa"))
        
        n_total = table.num_rows
        n_final = n_total - 3 # We lose 3 rows due to t-3 lag
        
        if n_final <= 0:
            raise ValueError("Insufficient data rows for ConditionalCAPM lags.")

        # Slices: All must have length = n_final
        # t is index 3...t-3 is index 0.
        l_tm1 = l_pc.slice(2, n_final)
        l_tm2 = l_pc.slice(1, n_final)
        l_tm3 = l_pc.slice(0, n_final)
        
        # JW's R_LBR: (L_t-1 + L_t-2) / (L_t-2 + L_t-3) - 1
        num = pc.add(l_tm1, l_tm2)
        den = pc.add(l_tm2, l_tm3)

        r_labor = pc.subtract(pc.divide(num, den), 1.0)
        
        # PREM (t-1 spread)
        prem_lagged = spread.slice(2, n_final)

        dates = table.column("date").slice(3, n_final)

        return pa.Table.from_arrays(
            [dates, r_labor, prem_lagged],
            names=["date", "LBR", "PREM"],
        ).combine_chunks()


