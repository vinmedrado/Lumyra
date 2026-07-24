from __future__ import annotations
from fastapi import APIRouter, Depends
from backend.middleware.auth import current_tenant, require_roles
from services.workflow_service import create_rule, list_rules, run_due_rules
router=APIRouter(prefix='/automation', tags=['automation'])
@router.get('/rules')
def rules(tenant_id:int=Depends(current_tenant)):
    return {'ok': True, 'data': list_rules(tenant_id)}
@router.post('/rules', dependencies=[Depends(require_roles('ADMIN'))])
def add_rule(trigger_type:str, action_type:str, event_id:int|None=None, condition_json:str='{}', action_json:str='{}', tenant_id:int=Depends(current_tenant)):
    return {'ok': True, 'data': {'id': create_rule(tenant_id, trigger_type, action_type, event_id, condition_json, action_json)}}
@router.post('/run', dependencies=[Depends(require_roles('ADMIN'))])
def run(tenant_id:int=Depends(current_tenant)):
    return {'ok': True, 'data': run_due_rules(tenant_id)}
