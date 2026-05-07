"""Firestore-backed CompanyRepository implementation."""
from typing import Optional
from google.cloud import firestore
from app.core.application.ports import CompanyRepository


class FirestoreCompanyStore(CompanyRepository):
    def __init__(self, collection_name: str = "companies"):
        # Explicitly use the same database as UserStore
        self.client = firestore.Client(database="hunterviz-db-native")
        self.collection = self.client.collection(collection_name)

    def get_by_id(self, company_id: str) -> Optional[dict]:
        doc = self.collection.document(company_id).get()
        if doc.exists:
            company = doc.to_dict()
            company["id"] = doc.id
            return company
        return None

    def list_by_owner(self, owner_id: str) -> list[dict]:
        query = self.collection.where("owner_id", "==", owner_id).stream()
        companies = []
        for doc in query:
            c = doc.to_dict()
            c["id"] = doc.id
            companies.append(c)
        return companies

    def list_by_member_email(self, email: str) -> list[dict]:
        # Firestore query for members.{email} exists
        # Since we use email as key in the members map
        # We can't use where("members." + email, "!=", None) easily in some versions
        # But we can try to query where the map contains the key.
        # Alternatively, we can use a list of member emails for easier querying.
        # Let's use a separate 'member_emails' list for efficient querying.
        query = self.collection.where("member_emails", "array_contains", email).stream()
        companies = []
        for doc in query:
            c = doc.to_dict()
            c["id"] = doc.id
            companies.append(c)
        return companies

    def save(self, company: dict) -> None:
        company_id = company.get("id")
        # Ensure member_emails is kept in sync with members map keys
        if "members" in company:
            company["member_emails"] = list(company["members"].keys())
        
        if not company_id:
            # Create new
            doc_ref = self.collection.document()
            company["id"] = doc_ref.id
            doc_ref.set(company)
        else:
            self.collection.document(company_id).set(company)
