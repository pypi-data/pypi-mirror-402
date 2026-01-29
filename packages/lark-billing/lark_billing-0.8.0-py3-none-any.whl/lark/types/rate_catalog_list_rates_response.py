# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .amount_output import AmountOutput
from .flat_price_typed_dict import FlatPriceTypedDict
from .package_price_typed_dict import PackagePriceTypedDict

__all__ = [
    "RateCatalogListRatesResponse",
    "Rate",
    "RateFixed",
    "RateFixedCreditGrant",
    "RateFixedCreditGrantExpiration",
    "RateFixedCreditGrantExpirationCreditGrantDurationExpirationModel",
    "RateFixedCreditGrantExpirationCreditGrantDateTimeExpirationModel",
    "RateFixedCreditGrantSchedule",
    "RateFixedCreditGrantScheduleCreditGrantScheduleOneTimeModel",
    "RateFixedCreditGrantScheduleCreditGrantScheduleRateCycleStartModel",
    "RateFixedCreditGrantSubjectGrantingConfig",
    "RateFixedPrice",
    "RateUsageBased",
    "RateUsageBasedSimpleUsageBasedRateTypedDict",
    "RateUsageBasedSimpleUsageBasedRateTypedDictPrice",
    "RateUsageBasedDimensionalUsageBasedRateTypedDict",
    "RateUsageBasedDimensionalUsageBasedRateTypedDictDimension",
    "RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrix",
    "RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrixCell",
    "RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrixCellPrice",
]


class RateFixedCreditGrantExpirationCreditGrantDurationExpirationModel(BaseModel):
    duration: int

    unit: Literal["hours", "days", "weeks", "months", "years"]

    expiration_type: Optional[Literal["duration"]] = None


class RateFixedCreditGrantExpirationCreditGrantDateTimeExpirationModel(BaseModel):
    date: str

    expiration_type: Optional[Literal["date"]] = None


RateFixedCreditGrantExpiration: TypeAlias = Annotated[
    Union[
        RateFixedCreditGrantExpirationCreditGrantDurationExpirationModel,
        RateFixedCreditGrantExpirationCreditGrantDateTimeExpirationModel,
        None,
    ],
    PropertyInfo(discriminator="expiration_type"),
]


class RateFixedCreditGrantScheduleCreditGrantScheduleOneTimeModel(BaseModel):
    scheduled_at: str

    schedule_type: Optional[Literal["one_time"]] = None


class RateFixedCreditGrantScheduleCreditGrantScheduleRateCycleStartModel(BaseModel):
    rate_cycle_start_at: str

    schedule_type: Optional[Literal["rate_cycle_start"]] = None


RateFixedCreditGrantSchedule: TypeAlias = Annotated[
    Union[
        RateFixedCreditGrantScheduleCreditGrantScheduleOneTimeModel,
        RateFixedCreditGrantScheduleCreditGrantScheduleRateCycleStartModel,
        None,
    ],
    PropertyInfo(discriminator="schedule_type"),
]


class RateFixedCreditGrantSubjectGrantingConfig(BaseModel):
    apply_to_children: bool

    apply_to_self: bool


class RateFixedCreditGrant(BaseModel):
    amount: AmountOutput

    expiration: Optional[RateFixedCreditGrantExpiration] = None

    metadata: Dict[str, str]

    name: str

    schedule: Optional[RateFixedCreditGrantSchedule] = None

    subject_granting_config: Optional[RateFixedCreditGrantSubjectGrantingConfig] = None


RateFixedPrice: TypeAlias = Annotated[
    Union[FlatPriceTypedDict, PackagePriceTypedDict], PropertyInfo(discriminator="price_type")
]


class RateFixed(BaseModel):
    id: str

    code: Optional[str] = None

    credit_grants: List[RateFixedCreditGrant]

    description: Optional[str] = None

    name: str

    price: RateFixedPrice

    quantity_code: Optional[str] = None


RateUsageBasedSimpleUsageBasedRateTypedDictPrice: TypeAlias = Annotated[
    Union[FlatPriceTypedDict, PackagePriceTypedDict], PropertyInfo(discriminator="price_type")
]


class RateUsageBasedSimpleUsageBasedRateTypedDict(BaseModel):
    id: str

    code: str

    description: Optional[str] = None

    included_units: int

    name: str

    price: RateUsageBasedSimpleUsageBasedRateTypedDictPrice

    pricing_metric_id: str

    usage_based_rate_type: Literal["simple"]


class RateUsageBasedDimensionalUsageBasedRateTypedDictDimension(BaseModel):
    description: Optional[str] = None

    key: str

    values: List[str]


RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrixCellPrice: TypeAlias = Annotated[
    Union[FlatPriceTypedDict, PackagePriceTypedDict], PropertyInfo(discriminator="price_type")
]


class RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrixCell(BaseModel):
    dimension_coordinates: Dict[str, str]

    price: RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrixCellPrice


class RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrix(BaseModel):
    cells: List[RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrixCell]


class RateUsageBasedDimensionalUsageBasedRateTypedDict(BaseModel):
    id: str

    code: str

    description: Optional[str] = None

    dimensions: List[RateUsageBasedDimensionalUsageBasedRateTypedDictDimension]

    included_units: int

    name: str

    pricing_matrix: RateUsageBasedDimensionalUsageBasedRateTypedDictPricingMatrix

    pricing_metric_id: str

    usage_based_rate_type: Literal["dimensional"]


RateUsageBased: TypeAlias = Union[
    RateUsageBasedSimpleUsageBasedRateTypedDict, RateUsageBasedDimensionalUsageBasedRateTypedDict, None
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
