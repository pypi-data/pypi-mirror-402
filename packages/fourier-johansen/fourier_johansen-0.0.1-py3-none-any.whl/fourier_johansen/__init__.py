"""
Fourier-Johansen: Johansen-type Cointegration Tests with a Fourier Function

This library implements the Johansen-Fourier cointegration tests that extend
the pioneering Johansen (1991) cointegration test to allow for structural 
breaks in a cointegration system using Fourier functions.

Reference:
    Pascalau, R., Lee, J., Nazlioglu, S., Lu, Y. O. (2022).
    "Johansen-type Cointegration Tests with a Fourier Function".
    Journal of Time Series Analysis 43(5): 828-852.
    DOI: 10.1111/jtsa.12640

Author: Dr Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/fourierjohansen
"""

__version__ = "0.0.1"
__author__ = "Dr Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

from .johansen import johansen, JohansenResult
from .johansen_fourier import johansen_fourier, JohansenFourierResult
from .sc_vecm import sc_vecm, SCVECMResult
from .sbc_test import sbc_test, SBCResult
from .union_test import union_test, UnionResult
from .output import format_results, to_latex, to_markdown

__all__ = [
    # Main test functions
    "johansen",
    "johansen_fourier",
    "sc_vecm",
    "sbc_test",
    "union_test",
    # Result classes
    "JohansenResult",
    "JohansenFourierResult",
    "SCVECMResult",
    "SBCResult",
    "UnionResult",
    # Output utilities
    "format_results",
    "to_latex",
    "to_markdown",
]
