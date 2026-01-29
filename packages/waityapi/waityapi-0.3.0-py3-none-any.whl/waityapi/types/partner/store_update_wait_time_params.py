# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["StoreUpdateWaitTimeParams"]


class StoreUpdateWaitTimeParams(TypedDict, total=False):
    queue_length: int
    """Number of people waiting"""

    wait_minutes: int
    """Current wait time in minutes"""
