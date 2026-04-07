"""Firestore-backed UserRepository implementation."""
from typing import Optional
from google.cloud import firestore
from app.core.application.ports import UserRepository
from app.core.domain.value_objects import Email, UserId

class FirestoreUserStore(UserRepository):
    def __init__(self, collection_name: str = "users"):
        self.client = firestore.Client()
        self.collection = self.client.collection(collection_name)

    def get_by_id(self, user_id: UserId) -> Optional[dict]:
        doc = self.collection.document(str(user_id)).get()
        if doc.exists:
            user = doc.to_dict()
            user["id"] = doc.id
            if "password_hash" in user:
                del user["password_hash"]
            return user
        return None

    def get_by_email(self, email: Email) -> Optional[dict]:
        query = self.collection.where("email", "==", str(email)).limit(1).stream()
        for doc in query:
            user = doc.to_dict()
            user["id"] = doc.id
            if "password_hash" in user:
                del user["password_hash"]
            return user
        return None

    def get_by_email_with_password(self, email: Email) -> Optional[dict]:
        query = self.collection.where("email", "==", str(email)).limit(1).stream()
        for doc in query:
            user = doc.to_dict()
            user["id"] = doc.id
            return user
        return None

    def save(self, user: dict) -> None:
        user_id = user.get("id")
        if not user_id:
            raise ValueError("User must have an 'id'")
        self.collection.document(str(user_id)).set(user)
