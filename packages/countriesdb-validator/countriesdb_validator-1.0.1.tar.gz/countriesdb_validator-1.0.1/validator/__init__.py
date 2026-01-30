"""
CountriesDB Python Backend Package

Backend validation package for CountriesDB.
Provides server-side validation for country and subdivision codes.

IMPORTANT: This package only provides validation methods.
Data fetching is frontend-only and must be done through frontend packages.
"""

from .validator import CountriesDBValidator

__version__ = "0.1.0"
__all__ = ["CountriesDBValidator"]









