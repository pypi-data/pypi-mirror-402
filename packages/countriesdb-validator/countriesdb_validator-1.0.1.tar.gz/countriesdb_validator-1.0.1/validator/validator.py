"""
Validation client for CountriesDB backend API

IMPORTANT: This package only provides validation methods.
Data fetching is frontend-only and must be done through frontend packages.
"""

import json
from typing import List, Optional, Union
import requests
from .types import (
    ValidationResult,
    ValidationOptions,
    SubdivisionValidationOptions,
    CountriesDBBackendConfig,
)


class CountriesDBValidator:
    """Validator for CountriesDB country and subdivision codes"""

    def __init__(self, config: CountriesDBBackendConfig):
        """
        Initialize the validator

        Args:
            config: Configuration dictionary with 'api_key' and optional 'backend_url'
        """
        if not config.get("api_key"):
            raise ValueError("API key is required")

        self.api_key = config["api_key"]
        self.backend_url = (
            config.get("backend_url")
            or "https://api.countriesdb.com"
        )
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        })

    def validate_country(
        self, code: str, follow_upward: bool = False
    ) -> ValidationResult:
        """
        Validate a single country code

        Args:
            code: ISO 3166-1 alpha-2 country code
            follow_upward: Check if country is referenced in a subdivision

        Returns:
            ValidationResult with 'valid' boolean and optional 'message'
        """
        if not code or not isinstance(code, str) or len(code) != 2:
            return {
                "valid": False,
                "message": "Invalid country code.",
            }

        try:
            response = self.session.post(
                f"{self.backend_url}/api/validate/country",
                json={
                    "code": code.upper(),
                    "follow_upward": follow_upward,
                },
            )

            if not response.ok:
                try:
                    error_data = response.json()
                    return {
                        "valid": False,
                        "message": error_data.get("message") or f"HTTP Error: {response.status_code}",
                    }
                except (json.JSONDecodeError, ValueError):
                    return {
                        "valid": False,
                        "message": f"HTTP Error: {response.status_code}",
                    }

            return response.json()
        except requests.RequestException as e:
            return {
                "valid": False,
                "message": str(e),
            }

    def validate_countries(
        self, codes: List[str]
    ) -> List[ValidationResult]:
        """
        Validate multiple country codes

        Args:
            codes: List of ISO 3166-1 alpha-2 country codes

        Returns:
            List of ValidationResult objects, each with 'code', 'valid', and optional 'message'
        """
        if not isinstance(codes, list):
            raise ValueError("Codes must be a list")

        if len(codes) == 0:
            return []

        try:
            response = self.session.post(
                f"{self.backend_url}/api/validate/country",
                json={
                    "code": [c.upper() for c in codes],
                    "follow_upward": False,  # Disabled for multi-select
                },
            )

            if not response.ok:
                try:
                    error_data = response.json()
                    raise ValueError(
                        error_data.get("message") or f"HTTP Error: {response.status_code}"
                    )
                except (json.JSONDecodeError, ValueError):
                    raise ValueError(f"HTTP Error: {response.status_code}")

            data = response.json()
            return data.get("results", [])
        except requests.RequestException as e:
            raise ValueError(f"Failed to validate countries: {str(e)}")

    def validate_subdivision(
        self,
        code: Optional[str],
        country: str,
        follow_related: bool = False,
        allow_parent: bool = False,
    ) -> ValidationResult:
        """
        Validate a single subdivision code

        Args:
            code: Subdivision code (e.g., 'US-CA') or None/empty string
            country: ISO 3166-1 alpha-2 country code
            follow_related: Check if subdivision redirects to another country
            allow_parent: Allow selecting parent subdivisions

        Returns:
            ValidationResult with 'valid' boolean and optional 'message'
        """
        if not country or not isinstance(country, str) or len(country) != 2:
            return {
                "valid": False,
                "message": "Invalid country code.",
            }

        try:
            response = self.session.post(
                f"{self.backend_url}/api/validate/subdivision",
                json={
                    "code": code or "",
                    "country": country.upper(),
                    "follow_related": follow_related,
                    "allow_parent_selection": allow_parent,
                },
            )

            if not response.ok:
                try:
                    error_data = response.json()
                    return {
                        "valid": False,
                        "message": error_data.get("message") or f"HTTP Error: {response.status_code}",
                    }
                except (json.JSONDecodeError, ValueError):
                    return {
                        "valid": False,
                        "message": f"HTTP Error: {response.status_code}",
                    }

            return response.json()
        except requests.RequestException as e:
            return {
                "valid": False,
                "message": str(e),
            }

    def validate_subdivisions(
        self,
        codes: List[Optional[str]],
        country: str,
        allow_parent: bool = False,
    ) -> List[ValidationResult]:
        """
        Validate multiple subdivision codes

        Args:
            codes: List of subdivision codes or None/empty strings
            country: ISO 3166-1 alpha-2 country code
            allow_parent: Allow selecting parent subdivisions

        Returns:
            List of ValidationResult objects, each with 'code', 'valid', and optional 'message'
        """
        if not isinstance(codes, list):
            raise ValueError("Codes must be a list")

        if len(codes) == 0:
            return []

        # Basic type check for country - format validation handled by backend
        if not isinstance(country, str):
            raise ValueError("Country must be a string")

        try:
            response = self.session.post(
                f"{self.backend_url}/api/validate/subdivision",
                json={
                    "code": [c or "" for c in codes],
                    "country": country.upper(),
                    "follow_related": False,  # Disabled for multi-select
                    "allow_parent_selection": allow_parent,
                },
            )

            if not response.ok:
                try:
                    error_data = response.json()
                    raise ValueError(
                        error_data.get("message") or f"HTTP Error: {response.status_code}"
                    )
                except (json.JSONDecodeError, ValueError):
                    raise ValueError(f"HTTP Error: {response.status_code}")

            data = response.json()
            return data.get("results", [])
        except requests.RequestException as e:
            raise ValueError(f"Failed to validate subdivisions: {str(e)}")

