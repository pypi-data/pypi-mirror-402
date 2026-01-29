# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import List

from ..._models import BaseModel

__all__ = ["QueueHistory", "Data", "Period"]


class Data(BaseModel):
    avg_wait_minutes: int

    busiest_hour: int

    date: datetime.date

    peak_wait_minutes: int

    total_visitors: int


class Period(BaseModel):
    end: datetime.datetime

    start: datetime.datetime


class QueueHistory(BaseModel):
    data: List[Data]

    period: Period

    store_id: str
