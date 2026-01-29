# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["RateCatalogRetrieveResponse"]


class RateCatalogRetrieveResponse(BaseModel):
    id: str

    description: str

    name: str

    rate_count: int
