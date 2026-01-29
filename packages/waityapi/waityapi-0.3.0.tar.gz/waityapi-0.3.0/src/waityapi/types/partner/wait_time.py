# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["WaitTime"]


class WaitTime(BaseModel):
    current_wait_minutes: int

    queue_length: int

    status: Literal["low", "moderate", "busy", "very_busy"]

    store_id: str

    updated_at: datetime

    average_service_time_minutes: Optional[float] = None
    """Average time to serve one customer (minutes)"""
