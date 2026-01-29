# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["StoreQueueHistoryParams"]


class StoreQueueHistoryParams(TypedDict, total=False):
    days: int
    """Number of days of history (max 30)."""
