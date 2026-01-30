# getfactormodels: https://github.com/x512/getfactormodels
# Copyright (C) 2025-2026 S. Martin <x512@pm.me>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Distributed WITHOUT ANY WARRANTY. See LICENSE for full terms.
from io import BytesIO
import pyarrow as pa
from python_calamine import CalamineWorkbook
from getfactormodels.models.base import FactorModel
from getfactormodels.models.fama_french import FamaFrenchFactors
from getfactormodels.utils.arrow_utils import (
    scale_to_decimal,
    select_table_columns,
)
from getfactormodels.utils.date_utils import offset_period_eom

#WIP NOT WORKING

class STVFactors(FactorModel):
    """Download the STV of Ung, Gebka and Anderson (2024).

    Data from Dec 1968 - Dec 2023. 

    This is the 'updated' calculation, "using the latest 
    available data (31st May 2024) from Professor Wurgler's website."

    Not implemented yet: accessing the 2016, and 2022 calculations. TODO

    References:
        Sze Nie Ung, Bartosz Gebka & Robert D. J. Anderson, 2024. 
        An enhanced investor sentiment index*. The European 
        Journal of Finance, 30:8, 827-864.

    Source:
        Ung, Gebka and Anderson, University of Manchester Figshare, 
        26 Mar 2025, DOI: 10.48420/28445081.v1, 
        https://figshare.manchester.ac.uk/articles/dataset/Enhanced_Investor_Sentiment_Index_STV_/28445081/1 Dataset
    """
    @property
    def _frequencies(self) -> list[str]:
        return ["m"]

    @property
    def _precision(self) -> int: 
        return 10  #11 is bad, but there's 14 undecimalized. [TODO: new system to enforce precision...]

    @property
    def schema(self) -> pa.Schema:
        schema = [ 
            ("Date", pa.string()),
            ("Enhanced Investor Sentiment Index (STV)\nDec 1968 - Dec 2023", pa.float64()), 
        ]
        return pa.schema(schema)

    def _get_url(self):
        return "https://figshare.manchester.ac.uk/ndownloader/files/52498529"

    # TODO: make reader a func xlsx models can use (maybe not AQR)
    def _read(self, data: bytes) -> pa.Table:
        workbook = CalamineWorkbook.from_filelike(BytesIO(data))
        
        rows = workbook.get_sheet_by_index(2).to_python()  # just 3rd sheet for now (2024 calc)
        if not rows: 
            return None

        headers = rows[0]
        data_rows = rows[1:]

        table_data = {}
        for i, header in enumerate(headers):
            clean_header = str(header).strip().replace('\n', ' ')

            column_values = []
            for row in data_rows:
                val = row[i] if i < len(row) else None
                if val == "" or val == "None":
                    val = None
                column_values.append(val)
            table_data[clean_header] = column_values

        table = pa.Table.from_pydict(table_data)
        table = table.rename_columns(['date', 'STV'])

        table = offset_period_eom(table, self.frequency) 
        table = scale_to_decimal(table)
        table.validate(full=True)

        # Make func. Can't get mkt-rf and RF like this. Precision messing up too. Just RF for now...
        _ff = FamaFrenchFactors(model='3', frequency=self.frequency).load()
        _ff = select_table_columns(_ff.data, ['RF']) # RF's ok because of the hard precision on it

        return table.join(_ff, keys="date", join_type="inner").combine_chunks()
