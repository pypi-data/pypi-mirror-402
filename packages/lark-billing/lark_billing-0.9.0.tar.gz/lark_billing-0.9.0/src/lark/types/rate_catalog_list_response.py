# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["RateCatalogListResponse", "RateCatalog"]


class RateCatalog(BaseModel):
    id: str

    description: str

    name: str

    rate_count: int


class RateCatalogListResponse(BaseModel):
    has_more: bool

    rate_catalogs: List[RateCatalog]
