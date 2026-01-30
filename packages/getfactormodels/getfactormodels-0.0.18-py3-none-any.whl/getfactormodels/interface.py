# NEW -- REFACTOR FROM main.py and get_factors to Models. 
import logging
from typing import Any
import pyarrow as pa
from getfactormodels import models as factor_models
from getfactormodels.models.registry import resolve_model_key
from getfactormodels.utils.arrow_utils import (
    print_table_preview,
    rearrange_columns,
)

log = logging.getLogger(__name__)

class Models:
    """Interface to instantiate and join multiple factor models."""
    def __init__(self, model_ids: str | list[str], **kwargs):
        self._input_ids = [model_ids] if isinstance(model_ids, (str, int)) else model_ids
        self.params = kwargs
        self._data: pa.Table | None = None

    def _get_model_class(self, key: str):
        """Maps registry keys to concrete Python classes."""
        mapping = {
            "3": "FamaFrenchFactors", "5": "FamaFrenchFactors", "6": "FamaFrenchFactors",
            "4": "CarhartFactors", "Q": "QFactors", "Qclassic": "QFactors",
            "HMLDevil": "HMLDevilFactors",
        }
        class_name = mapping.get(key, f"{key}Factors")
        
        if not hasattr(factor_models, class_name):
            raise ValueError(f"Class '{class_name}' not found in factor_models.")
        return getattr(factor_models, class_name)

    def load(self, client=None) -> "Models":
        """The coordination step: triggers worker loads and joins them."""
        tables = []
        
        for mid in self._input_ids:
            key = resolve_model_key(mid)
            cls = self._get_model_class(key)
            
            # Inject model-specific params into the kwargs
            inst_params = self.params.copy()
            if key in ("3", "5", "6"): inst_params["model"] = key
            if key == "Qclassic": inst_params["classic"] = True
            
            # This calls the Worker's load()
            instance = cls(**inst_params).load(client=client)
            tables.append(instance.data)

        if not tables:
            raise RuntimeError("No data could be loaded.")

        # Join Logic: combine multiple tables into one
        combined = tables[0]
        for next_table in tables[1:]:
            # Drop overlapping columns to avoid duplicate factor names (SMB, HML, etc)
            overlap = set(combined.column_names) & set(next_table.column_names)
            overlap.discard('date')
            if overlap:
                next_table = next_table.drop(list(overlap))
                
            combined = combined.join(next_table, keys='date', join_type='left outer')

        self._data = rearrange_columns(combined)
        return self

    @property
    def data(self) -> pa.Table:
        if self._data is None: 
            self.load()
        return self._data

    def to_pandas(self):
        return self.data.to_pandas().set_index('date')

    def __str__(self):
        if self._data is None: return "Models(Not Loaded)"
        header = f"Joined Factor Models: {', '.join(map(str, self._input_ids))}\n"
        return header + print_table_preview(self._data)
