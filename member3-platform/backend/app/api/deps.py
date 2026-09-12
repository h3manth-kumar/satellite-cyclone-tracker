"""
API dependency injection module.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.adapters.base import IMember1Adapter, IMember2Adapter
from app.adapters.factory import get_member1_adapter, get_member2_adapter

def get_db_session() -> AsyncSession:
    return Depends(get_db)

def get_m1() -> IMember1Adapter:
    return get_member1_adapter()

def get_m2() -> IMember2Adapter:
    return get_member2_adapter()
