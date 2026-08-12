from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    transaction_id: str = Field(
        min_length=1,
        max_length=100,
    )

    account_id: str = Field(
        min_length=1,
        max_length=100,
    )

    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
        max_digits=18,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        return value.upper()


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    account_id: str
    amount: Decimal
    currency: str
    description: str | None
    created_at: datetime


class PaginatedTransactions(BaseModel):
    items: list[TransactionResponse]
    page: int
    page_size: int
    total: int
    total_pages: int