from __future__ import annotations
from fastapi import APIRouter
from services.health_service import system_health
router=APIRouter(tags=['health'])
@router.get('/health')
def health():
    return {'ok': True, 'data': system_health()}
