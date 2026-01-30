# getfactormodels: https://github.com/x512/getfactormodels
# Copyright (C) 2025-2026 S. Martin <x512@pm.me>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Distributed WITHOUT ANY WARRANTY. See LICENSE for full terms.
import logging
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

#import warnings

log = logging.getLogger(__name__) #TODO: consistent logging.

"""Model utils. Model map, aliases, lookup and typing."""

ModelKey: TypeAlias = Literal[
    "3", "4", "5", "6", "Q", "Qclassic", "HMLDevil", "QMJ", "BAB", 
    "Mispricing", "Liquidity", "ICR", "DHS", "BarillasShanken", "VME", "AQR6", "SimpleCAPM",
]

_MODEL_ALIASES: Final[dict[ModelKey, list[str]]] = {
    "3": ["3", "ff3", "famafrench3"],
    "4": ["4", "ff4", "carhart", "car"],
    "5": ["5", "ff5", "famafrench5"],
    "6": ["6", "ff6", "famafrench6"],
    "Q": ["q", "qfactors", "q-factors", "q_factors", "q5", "hmxz"],
    "Qclassic": ["q4", "qclassic", "q-classic", "q_classic", "classic_q"],
    "HMLDevil": ["hmld", "hmldevil", "hml_devil", "devil"],
    "QMJ": ["qmj", "quality", "qualityminusjunk"],
    "BAB": ["bab", "betting", "bettingainstbeta"],
    "Mispricing": ["mispricing", "mis", "misp"],
    "Liquidity": ["liq", "liquidity"],
    "ICR": ["icr", "intermediary", "hkm"],
    "DHS": ["dhs", "behavioural", "behaviour"],
    "BarillasShanken": ["bs", "bs6", "barillasshanken", "barillas-shanken"],
    "VME": ["vme", "valmom", "valueandmomentumeverywhere"],
    "AQR6": ["aqr6", "aqr", "aqrfactors"],
    "SimpleCAPM": ['capm'],
}

# Inverted Index: O(1) lookup
# This creates a flat dict: {'ff3': '3', 'carhart': '4', ...}
_LOOKUP = MappingProxyType({
    alias.lower(): key 
    for key, aliases in _MODEL_ALIASES.items() 
    for alias in [key] + aliases  # don't forget the key itself
})
_VALID_INPUTS: Final[frozenset[str]] = frozenset(_LOOKUP.keys())

def get_model_key(user_input: str | int) -> str:
    """Converts user input to the model key.

    >>> _get_model_key('3')
    '3'
    >>> _get_model_key('ff6')
    '6'
    >>> _get_model_key('q5')
    'Q'
    """
    if not user_input:
        return ""

    val = str(user_input).lower().strip()
    #return _LOOKUP.get(val, val)
    match = _LOOKUP.get(val, val)
    log.debug(f"Input '{user_input}' ('{val}'), resolved: '{match}'") 
    return match

def get_available_models() -> tuple[ModelKey, ...]:
    return tuple(_MODEL_ALIASES.keys())



