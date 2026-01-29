# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from ..._models import BaseModel

__all__ = ["CheckInResponse"]


class CheckInResponse(BaseModel):
    checked_in_at: datetime

    estimated_wait: int
    """Estimated wait time in minutes"""

    position: int
    """Position in queue"""

    queue_length: int
    """Total people in queue"""

    store_id: str
