from typing import Optional, Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
