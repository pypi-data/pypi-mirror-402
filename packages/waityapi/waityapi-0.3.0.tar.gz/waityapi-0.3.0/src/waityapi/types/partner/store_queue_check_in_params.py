# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["StoreQueueCheckInParams"]


class StoreQueueCheckInParams(TypedDict, total=False):
    name: str
    """Optional customer name"""

    party_size: int
    """Number of people in party"""

    phone: str
    """Optional phone for notifications"""
