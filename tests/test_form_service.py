from repositories.database import init_db
from services.form_service import create_form, add_field, list_fields

def test_form_field_crud_smoke():
    init_db()
    fid = create_form(1, 'Teste pytest', True)
    add_field(fid, 'Vai?', 'boolean', False, '')
    df = list_fields(fid)
    assert not df.empty
