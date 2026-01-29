from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, AliasPath, field_validator


class ResultDetails(BaseModel):
    credits_used: int
    samples: int
    country: Optional[str] = None
    first_name_sanitized: Optional[str] = None
    duration: str


class BaseResult(BaseModel):
    """Base model for API results."""
    # We use a custom init or properties to flatten details for easier access if desired,
    # but strictly following the API response structure is safer (nested).
    # However, for a "pythonic" client, users might prefer `result.credits_used` over `result.details.credits_used`.
    
    input: Dict[str, Any]
    details: ResultDetails
    result_found: bool
    probability: float
    gender: str

    @property
    def accuracy(self) -> int:
        """Compatibility alias for probability displayed as percentage integer."""
        return int(self.probability * 100)
    
    @property
    def samples(self) -> int:
        return self.details.samples
        
    @property
    def country(self) -> Optional[str]:
        return self.details.country

    @property
    def credits_used(self) -> int:
        return self.details.credits_used

    @property
    def duration(self) -> str:
        return self.details.duration


class SingleNameResult(BaseResult):
    first_name: str


class MultipleNamesResult(BaseModel):
    # The API returns a list of results directly for the multiple endpoint?
    # No, `ResultModelMultiple` is `type: array`.
    # So the client method should return `List[SingleNameResult]`.
    # But for specialized parsing, we might wrap it.
    # Actually, the user will expect a list.
    pass


class FullNameResult(BaseResult):
    first_name: str
    last_name: Optional[str] = None


class EmailResult(BaseResult):
    email: Optional[str] = None
    last_name: Optional[str] = None
    first_name: str


class CountryOfOriginItem(BaseModel):
    country_name: str
    country: str
    probability: float
    continental_region: Optional[str] = None
    statistical_region: Optional[str] = None


class CountryOfOriginResult(BaseModel):
    input: Dict[str, Any]
    details: ResultDetails
    result_found: bool
    country_of_origin: List[CountryOfOriginItem]
    country_of_origin_map_url: Optional[str] = None
    first_name: str
    probability: float
    gender: str


class StatsResult(BaseModel):
    is_limit_reached: bool
    remaining_credits: int
    details: Dict[str, Any]
    usage_last_month: Optional[Dict[str, Any]] = None
