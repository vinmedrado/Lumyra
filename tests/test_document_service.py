from io import BytesIO
from repositories.database import init_db
from services.document_service import save_document, list_documents

class Upload(BytesIO):
    name = 'teste.txt'
    def getvalue(self):
        return super().getvalue()

def test_document_smoke():
    init_db()
    f = Upload(b'abc')
    save_document(1, f, 'Doc Pytest', 'outro')
    assert not list_documents(1).empty
