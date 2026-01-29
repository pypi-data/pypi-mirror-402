from .client import Client
from .exceptions import GenderApiError, InvalidArgumentError, ApiError
from .models import (
    SingleNameResult,
    MultipleNamesResult,
    FullNameResult,
    EmailResult,
    CountryOfOriginResult,
    StatsResult
)

__all__ = [
    "Client",
    "GenderApiError",
    "InvalidArgumentError",
    "ApiError",
    "SingleNameResult",
    "MultipleNamesResult",
    "FullNameResult",
    "EmailResult",
    "CountryOfOriginResult",
    "StatsResult",
]
