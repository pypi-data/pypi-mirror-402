"""
Type definitions for CountriesDB Python package
"""

from typing import TypedDict, List, Optional


class ValidationResult(TypedDict, total=False):
    """Result of a validation operation"""
    valid: bool
    message: Optional[str]
    code: Optional[str]  # Present in multi-value results


class ValidationOptions(TypedDict, total=False):
    """Options for country validation"""
    follow_upward: bool


class SubdivisionValidationOptions(TypedDict, total=False):
    """Options for subdivision validation"""
    follow_related: bool
    allow_parent_selection: bool


class CountriesDBBackendConfig(TypedDict, total=False):
    """Configuration for CountriesDBValidator"""
    api_key: str
    backend_url: Optional[str]









