from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Transaction
from schemas import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionResponse,
)

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create and persist a transaction.
    """

    # Check for duplicate transaction ID.
    result = await db.execute(
        select(Transaction).where(
            Transaction.transaction_id
            == transaction_data.transaction_id
        )
    )

    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction already exists",
        )

    transaction = Transaction(
        transaction_id=transaction_data.transaction_id,
        account_id=transaction_data.account_id,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        description=transaction_data.description,
    )

    db.add(transaction)

    try:
        await db.commit()
        await db.refresh(transaction)

    except IntegrityError:
        await db.rollback()

        # Protect against race conditions where another
        # request inserted the same transaction_id.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction already exists",
        )

    return transaction


@router.get(
    "",
    response_model=PaginatedTransactions,
)
async def get_transactions(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    account_id: str | None = Query(
        default=None,
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Return paginated transaction history.
    """

    # Base query
    query = select(Transaction)

    if account_id:
        query = query.where(
            Transaction.account_id == account_id
        )

    # Get total count.
    count_query = select(
        func.count()
    ).select_from(Transaction)

    if account_id:
        count_query = count_query.where(
            Transaction.account_id == account_id
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Calculate pagination.
    offset = (page - 1) * page_size

    query = (
        query
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)

    transactions = result.scalars().all()

    total_pages = ceil(total / page_size) if total else 0

    return PaginatedTransactions(
        items=transactions,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )