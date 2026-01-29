# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["StoreUpdateQueueResponse"]


class StoreUpdateQueueResponse(BaseModel):
    queue_length: int

    status: Literal["open", "closed"]

    store_id: str

    updated_at: datetime

    wait_minutes: int
