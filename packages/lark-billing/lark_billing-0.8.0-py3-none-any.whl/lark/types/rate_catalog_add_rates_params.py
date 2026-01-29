# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .flat_price_input_param import FlatPriceInputParam
from .package_price_input_param import PackagePriceInputParam

__all__ = [
    "RateCatalogAddRatesParams",
    "FixedRate",
    "FixedRatePrice",
    "UsageBasedRate",
    "UsageBasedRateCreateSimpleUsageBasedRateRequest",
    "UsageBasedRateCreateSimpleUsageBasedRateRequestPrice",
    "UsageBasedRateCreateDimensionalUsageBasedRateRequest",
    "UsageBasedRateCreateDimensionalUsageBasedRateRequestDimension",
    "UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrix",
    "UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrixCell",
    "UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrixCellPrice",
]


class RateCatalogAddRatesParams(TypedDict, total=False):
    billing_interval: Required[Literal["monthly", "yearly"]]
    """How often the customer will be billed for these rates."""

    fixed_rates: Iterable[FixedRate]
    """The fixed rate to create in the catalog."""

    usage_based_rates: Iterable[UsageBasedRate]
    """The usage based rates to create in the catalog."""


FixedRatePrice: TypeAlias = Union[FlatPriceInputParam, PackagePriceInputParam]


class FixedRate(TypedDict, total=False):
    code: Required[str]
    """Code of this rate to be used for setting quantity and price multipliers.

    This code must be unique within the rate card.
    """

    name: Required[str]
    """The name of the rate displayed to the customer."""

    price: Required[FixedRatePrice]
    """Flat price is a price that linearly scales with the quantity."""

    description: Optional[str]
    """The description of the rate displayed to the customer."""


UsageBasedRateCreateSimpleUsageBasedRateRequestPrice: TypeAlias = Union[FlatPriceInputParam, PackagePriceInputParam]


class UsageBasedRateCreateSimpleUsageBasedRateRequest(TypedDict, total=False):
    code: Required[str]
    """Code of this rate to be used for price multipliers.

    This code must be unique within the rate card.
    """

    name: Required[str]
    """The name of the rate displayed to the customer."""

    price: Required[UsageBasedRateCreateSimpleUsageBasedRateRequestPrice]
    """Flat price is a price that linearly scales with the quantity."""

    pricing_metric_id: Required[str]
    """The ID of the pricing metric to use for this rate."""

    usage_based_rate_type: Required[Literal["simple"]]

    description: Optional[str]
    """The description of the rate displayed to the customer."""

    included_units: int
    """The number of units included in the rate before the price is applied."""


class UsageBasedRateCreateDimensionalUsageBasedRateRequestDimension(TypedDict, total=False):
    key: Required[str]
    """The name of the dimension.

    This is used to identify the dimension in the pricing matrix.
    """

    values: Required[SequenceNotStr[str]]
    """A list of possible values for the dimension."""

    description: Optional[str]
    """The description of the dimension."""


UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrixCellPrice: TypeAlias = Union[
    FlatPriceInputParam, PackagePriceInputParam
]


class UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrixCell(TypedDict, total=False):
    dimension_coordinates: Required[Dict[str, str]]
    """
    A key-value mapping of dimension keys and values to identify the price for a
    given set of dimension values.
    """

    price: Required[UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrixCellPrice]
    """The price for the cell."""


class UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrix(TypedDict, total=False):
    """The pricing matrix of the rate."""

    cells: Required[Iterable[UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrixCell]]


class UsageBasedRateCreateDimensionalUsageBasedRateRequest(TypedDict, total=False):
    code: Required[str]
    """Code of this rate to be used for price multipliers.

    This code must be unique within the rate card.
    """

    dimensions: Required[Iterable[UsageBasedRateCreateDimensionalUsageBasedRateRequestDimension]]
    """The dimensions of the rate."""

    name: Required[str]
    """The name of the rate displayed to the customer."""

    pricing_matrix: Required[UsageBasedRateCreateDimensionalUsageBasedRateRequestPricingMatrix]
    """The pricing matrix of the rate."""

    pricing_metric_id: Required[str]
    """The ID of the pricing metric to use for this rate."""

    usage_based_rate_type: Required[Literal["dimensional"]]

    description: Optional[str]
    """The description of the rate displayed to the customer."""

    included_units: int
    """The number of units included in the rate before the price is applied."""


UsageBasedRate: TypeAlias = Union[
    UsageBasedRateCreateSimpleUsageBasedRateRequest, UsageBasedRateCreateDimensionalUsageBasedRateRequest
]
