# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["AmountTypedDict"]


class AmountTypedDict(BaseModel):
    currency_code: str

    value: str
