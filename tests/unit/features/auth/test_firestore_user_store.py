from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
google_module = types.ModuleType("google")
cloud_module = types.ModuleType("google.cloud")
firestore_module = types.ModuleType("google.cloud.firestore")
firestore_module.Client = object
cloud_module.firestore = firestore_module
google_module.cloud = cloud_module
sys.modules.setdefault("google", google_module)
sys.modules["google.cloud"] = cloud_module
sys.modules["google.cloud.firestore"] = firestore_module

from app.core.domain.value_objects import Email, UserId
from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore


class _FakeDoc:
    def __init__(self, doc_id: str, data: dict, exists: bool = True):
        self.id = doc_id
        self._data = data
        self.exists = exists

    def to_dict(self) -> dict:
        return dict(self._data)


class _FakeQuery:
    def __init__(self, docs):
        self._docs = docs

    def limit(self, _count: int):
        return self

    def stream(self):
        return iter(self._docs)


class _FakeCollection:
    def __init__(self, docs):
        self._docs = docs

    def where(self, _field: str, _op: str, value: str):
        matching = [doc for doc in self._docs if doc.to_dict().get("email") == value]
        return _FakeQuery(matching)

    def document(self, doc_id: str):
        for doc in self._docs:
            if doc.id == doc_id:
                return type("_DocRef", (), {"get": lambda _self: doc})()
        missing = _FakeDoc(doc_id, {}, exists=False)
        return type("_DocRef", (), {"get": lambda _self: missing})()


class FirestoreUserStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = FirestoreUserStore.__new__(FirestoreUserStore)
        self.store.collection = _FakeCollection(
            [
                _FakeDoc(
                    "user-123",
                    {
                        "email": "user@example.com",
                        "password_hash": "hashed-secret",
                        "company_name": "Acme",
                    },
                )
            ]
        )

    def test_get_by_email_returns_password_hash_for_login_verification(self):
        user = self.store.get_by_email(Email("user@example.com"))

        self.assertIsNotNone(user)
        self.assertEqual(user["id"], "user-123")
        self.assertEqual(user["password_hash"], "hashed-secret")

    def test_get_by_id_omits_password_hash_for_non_auth_reads(self):
        user = self.store.get_by_id(UserId("user-123"))

        self.assertIsNotNone(user)
        self.assertEqual(user["id"], "user-123")
        self.assertNotIn("password_hash", user)


if __name__ == "__main__":
    unittest.main()
