# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel
from .amount_typed_dict import AmountTypedDict

__all__ = ["FlatPriceTypedDict"]


class FlatPriceTypedDict(BaseModel):
    amount: AmountTypedDict

    price_type: Literal["flat"]
