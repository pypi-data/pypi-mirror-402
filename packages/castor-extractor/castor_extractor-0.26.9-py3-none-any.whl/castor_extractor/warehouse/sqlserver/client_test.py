from ...utils import ExtractionQuery
from .client import MSSQLClient


class FakeConnection:
    closed = False

    def execute(self, *_args, **_kwargs):
        return [{"ok": 1}]

    def close(self):
        self.closed = True


class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()

    def connect(self):
        return self.connection

    def dispose(self):
        pass


def test_build_uri_and_database_resolution(monkeypatch):
    """
    Single test covering:
    - default_db present / absent
    - query.database present / absent
    - ensuring the correct DB is used in the final engine URI
    """

    created_uris: list[str] = []

    def fake_create_engine(uri, **_kwargs):
        created_uris.append(uri)
        return FakeEngine()

    # Patch create_engine where it is used (inside client.py)
    monkeypatch.setattr(
        "source.packages.extractor.castor_extractor.warehouse.sqlserver.client.create_engine",
        fake_create_engine,
    )

    base_credentials = {
        "host": "sql.example.local",
        "port": 1433,
        "user": "user",
        "password": "password",
    }

    # Case 1: no default_db, no query.database → base URI
    client = MSSQLClient(base_credentials)
    list(client.execute(ExtractionQuery("SELECT 1", params={}, database=None)))
    assert created_uris[-1] == client._uri

    # Case 2: default_db provided, no query.database → default_db used
    client = MSSQLClient({**base_credentials, "default_db": "default_db"})
    list(client.execute(ExtractionQuery("SELECT 1", params={}, database=None)))
    assert created_uris[-1].endswith("/default_db")

    # Case 3: default_db provided, query.database provided → query.database wins
    client = MSSQLClient({**base_credentials, "default_db": "default_db"})
    list(
        client.execute(
            ExtractionQuery("SELECT 1", params={}, database="explicit_db")
        )
    )
    assert created_uris[-1].endswith("/explicit_db")

    # Case 4: no default_db, query.database provided → query.database used
    client = MSSQLClient(base_credentials)
    list(
        client.execute(
            ExtractionQuery("SELECT 1", params={}, database="explicit_db")
        )
    )
    assert created_uris[-1].endswith("/explicit_db")
