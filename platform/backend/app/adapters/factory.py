"""
Adapter factory and dependency injection providers.
"""
from app.core.config import settings
from app.adapters.base import IMember1Adapter, IMember2Adapter
from app.adapters.member1_adapter import HttpMember1Adapter, MockMember1Adapter
from app.adapters.member2_adapter import HttpMember2Adapter, MockMember2Adapter

_member1_instance: IMember1Adapter = None
_member2_instance: IMember2Adapter = None

def get_member1_adapter() -> IMember1Adapter:
    global _member1_instance
    if _member1_instance is None:
        if settings.USE_MOCK_ML:
            _member1_instance = MockMember1Adapter()
        else:
            _member1_instance = HttpMember1Adapter()
    return _member1_instance

def get_member2_adapter() -> IMember2Adapter:
    global _member2_instance
    if _member2_instance is None:
        if settings.USE_MOCK_ML:
            _member2_instance = MockMember2Adapter()
        else:
            _member2_instance = HttpMember2Adapter()
    return _member2_instance
