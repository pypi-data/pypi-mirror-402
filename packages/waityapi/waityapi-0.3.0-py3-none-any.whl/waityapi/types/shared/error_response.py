# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["ErrorResponse", "Error"]


class Error(BaseModel):
    code: str

    message: str

    retry_after: Optional[int] = None
    """Present on rate limit errors"""


class ErrorResponse(BaseModel):
    error: Error
