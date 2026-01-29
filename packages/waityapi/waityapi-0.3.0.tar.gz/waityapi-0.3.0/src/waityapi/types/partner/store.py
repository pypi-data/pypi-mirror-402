# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["Store"]


class Store(BaseModel):
    """Store/location information.

    All optional fields are always present (null if not set).
    """

    id: str

    address: Optional[str] = None

    category: Optional[str] = None

    city: Optional[str] = None

    country: Optional[str] = None

    is_virtual: bool
    """True if business has no physical location"""

    latitude: Optional[float] = None

    logo_url: Optional[str] = None

    longitude: Optional[float] = None

    name: str

    phone: Optional[str] = None

    postal_code: Optional[str] = None

    state: Optional[str] = None

    timezone: Optional[str] = None
    """IANA timezone identifier (e.g., America/New_York)"""

    website: Optional[str] = None
