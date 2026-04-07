"""Firestore user store implementation."""
from typing import Optional, List
from google.cloud import firestore

class FirestoreUserStore:
    def __init__(self, collection_name: str = "users"):
        self.client = firestore.Client(database="hunterviz-db")
        self.collection = self.client.collection(collection_name)

    def list_users(self) -> List[dict]:
        docs = self.collection.stream()
        users = []
        for doc in docs:
            user = doc.to_dict()
            user["id"] = doc.id
            if "password_hash" in user:
                del user["password_hash"]
            users.append(user)
        return users

    def get_by_id(self, user_id: str) -> Optional[dict]:
        doc = self.collection.document(user_id).get()
        if doc.exists:
            user = doc.to_dict()
            user["id"] = doc.id
            return user
        return None

    def save(self, user: dict) -> None:
        user_id = user.get("id")
        if not user_id:
            raise ValueError("User must have an 'id'")
        self.collection.document(user_id).set(user)
