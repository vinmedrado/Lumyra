from services.whatsapp_service import normalize_phone, render_template

def test_normalize_phone_br():
    assert normalize_phone('(11) 99999-9999') == '5511999999999'

def test_render_template():
    assert render_template('Olá {nome} {link}', nome='Ana', guest_link='x') == 'Olá Ana x'
