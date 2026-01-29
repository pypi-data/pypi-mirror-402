# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .store import Store
from ..._models import BaseModel

__all__ = ["StoreListResponse"]


class StoreListResponse(BaseModel):
    stores: List[Store]

    total: int
