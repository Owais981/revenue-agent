from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountOut, AccountUpdate
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
def list_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Account)
    total = query.count()
    items = query.order_by(Account.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [AccountOut.model_validate(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Account not found", "error_code": "ACCOUNT_NOT_FOUND"},
        )
    return account


@router.put("/{account_id}", response_model=AccountOut)
def update_account(account_id: str, payload: AccountUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Account not found", "error_code": "ACCOUNT_NOT_FOUND"},
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account
