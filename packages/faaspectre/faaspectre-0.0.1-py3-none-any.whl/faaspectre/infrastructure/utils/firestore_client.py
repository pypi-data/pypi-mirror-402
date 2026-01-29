"""Firestore client wrapper for infrastructure layer."""

from typing import Optional
from google.cloud import firestore

from ...utils.singleton import Singleton


class FirestoreClient(metaclass=Singleton):
    """Firestore client singleton for Telemetric Reporter.

    Wraps google.cloud.firestore.Client with singleton pattern.
    """

    _client: firestore.Client

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore client.

        Args:
            project_id: Google Cloud project ID (optional)
        """
        self._client = firestore.Client(project=project_id)

    @property
    def client(self) -> firestore.Client:
        """Get Firestore client instance."""
        return self._client

    def upsert(
        self,
        collection_name: str,
        doc_id: str,
        data: dict,
    ) -> None:
        """Update or insert document to Firestore.

        Args:
            collection_name: Collection name
            doc_id: Document ID
            data: Data dictionary to insert/update

        Raises:
            Exception: If Firestore operation fails
        """
        self._client.collection(collection_name).document(doc_id).set(data, merge=True)
