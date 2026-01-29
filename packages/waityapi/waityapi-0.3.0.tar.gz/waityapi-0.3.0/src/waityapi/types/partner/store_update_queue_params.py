# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["StoreUpdateQueueParams"]


class StoreUpdateQueueParams(TypedDict, total=False):
    queue_length: int
    """Number of people waiting"""

    status: Literal["open", "closed"]
    """Queue status (open or closed)"""

    wait_minutes: int
    """Current estimated wait time"""
