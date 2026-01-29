# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel
from .amount_typed_dict import AmountTypedDict

__all__ = ["PackagePriceTypedDict"]


class PackagePriceTypedDict(BaseModel):
    amount: AmountTypedDict

    package_units: int

    price_type: Literal["package"]

    rounding_behavior: Literal["round_up", "round_down"]
