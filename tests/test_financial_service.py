from repositories.database import init_db
from services.financial_service import add_vendor, add_expense, list_expenses, summary

def test_financial_smoke():
    init_db()
    v = add_vendor(1, 'Fornecedor Pytest', 'outro')
    add_expense(1, v, 'Despesa Pytest', 100, 'pending')
    assert not list_expenses(1).empty
    assert summary(1)['total_contratado'] >= 100
