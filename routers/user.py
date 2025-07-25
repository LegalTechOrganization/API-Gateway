from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from db import get_session

router = APIRouter()

@router.post("/users/")
async def create_user(email: str, full_name: str, session: AsyncSession = Depends(get_session)):
    user = User(email=email, full_name=full_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name}

@router.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "full_name": user.full_name} 