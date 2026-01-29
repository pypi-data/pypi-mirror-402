# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from ..._models import BaseModel

__all__ = ["CheckOutResponse"]


class CheckOutResponse(BaseModel):
    queue_length: int
    """Remaining people in queue"""

    served: int
    """Number of people marked as served"""

    store_id: str

    updated_at: datetime
