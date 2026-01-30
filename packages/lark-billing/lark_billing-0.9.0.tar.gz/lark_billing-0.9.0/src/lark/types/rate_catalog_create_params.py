# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["RateCatalogCreateParams"]


class RateCatalogCreateParams(TypedDict, total=False):
    description: Required[str]
    """The description of the catalog."""

    name: Required[str]
    """The name of the catalog."""
