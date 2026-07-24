from repositories.database import init_db
from services.event_insights import analyze_event

def test_insights_shape():
    init_db()
    data = analyze_event(1)
    assert isinstance(data, list)
    assert {'severity','title','message','action','related_page','count'}.issubset(data[0].keys())
