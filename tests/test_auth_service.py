from services import auth_service

def test_roles_defined():
    assert {'ADMIN','CLIENT','STAFF'}.issubset(set(auth_service.ROLES))
