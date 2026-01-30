# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .flat_price_output import FlatPriceOutput
from .package_price_output import PackagePriceOutput

__all__ = [
    "RateCatalogListRatesResponse",
    "Rate",
    "RateFixed",
    "RateFixedPrice",
    "RateUsageBased",
    "RateUsageBasedSimpleUsageBasedRateInterface",
    "RateUsageBasedSimpleUsageBasedRateInterfacePrice",
    "RateUsageBasedDimensionalUsageBasedRateInterface",
    "RateUsageBasedDimensionalUsageBasedRateInterfaceDimension",
    "RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrix",
    "RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrixCell",
    "RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrixCellPrice",
]

RateFixedPrice: TypeAlias = Annotated[
    Union[FlatPriceOutput, PackagePriceOutput], PropertyInfo(discriminator="price_type")
]


class RateFixed(BaseModel):
    id: str

    code: str

    description: Optional[str] = None

    name: str

    price: RateFixedPrice
    """Flat price is a price that linearly scales with the quantity."""


RateUsageBasedSimpleUsageBasedRateInterfacePrice: TypeAlias = Annotated[
    Union[FlatPriceOutput, PackagePriceOutput], PropertyInfo(discriminator="price_type")
]


class RateUsageBasedSimpleUsageBasedRateInterface(BaseModel):
    id: str

    code: str

    description: Optional[str] = None

    included_units: int

    name: str

    price: RateUsageBasedSimpleUsageBasedRateInterfacePrice
    """Flat price is a price that linearly scales with the quantity."""

    pricing_metric_id: str

    usage_based_rate_type: Optional[Literal["simple"]] = None


class RateUsageBasedDimensionalUsageBasedRateInterfaceDimension(BaseModel):
    description: Optional[str] = None

    key: str

    values: List[str]


RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrixCellPrice: TypeAlias = Annotated[
    Union[FlatPriceOutput, PackagePriceOutput], PropertyInfo(discriminator="price_type")
]


class RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrixCell(BaseModel):
    dimension_coordinates: Dict[str, str]

    price: RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrixCellPrice
    """Flat price is a price that linearly scales with the quantity."""


class RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrix(BaseModel):
    cells: List[RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrixCell]


class RateUsageBasedDimensionalUsageBasedRateInterface(BaseModel):
    id: str

    code: str

    description: Optional[str] = None

    dimensions: List[RateUsageBasedDimensionalUsageBasedRateInterfaceDimension]

    included_units: int

    name: str

    pricing_matrix: RateUsageBasedDimensionalUsageBasedRateInterfacePricingMatrix

    pricing_metric_id: str

    usage_based_rate_type: Optional[Literal["dimensional"]] = None


RateUsageBased: TypeAlias = Annotated[
    Union[RateUsageBasedSimpleUsageBasedRateInterface, RateUsageBasedDimensionalUsageBasedRateInterface, None],
    PropertyInfo(discriminator="usage_based_rate_type"),
]


class Rate(BaseModel):
    id: str

    interval: Literal["monthly", "yearly"]

    rate_catalog_id: str

    type: Literal["fixed", "usage_based"]

    fixed: Optional[RateFixed] = None

    usage_based: Optional[RateUsageBased] = None


class RateCatalogListRatesResponse(BaseModel):
    has_more: bool

    rates: List[Rate]
