"""
RAG module over marketing playbooks using Chroma (local only).

Security note:
- We exclusively use chromadb.PersistentClient (embedded mode).
- We never start or expose the Chroma HTTP server.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings, get_logger
from knowledge.loader import load_playbooks

logger = get_logger(__name__)


class KnowledgeBase:
    """
    Simple RAG over marketing playbooks.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or str(settings.chroma_persist_dir)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "marketing_playbooks"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Marketing playbooks for Eleva"}
        )
        logger.info(f"KnowledgeBase ready (persist_dir={self.persist_dir})")

    def index_playbooks(self, force_reload: bool = False) -> int:
        """
        Load playbooks from YAML and index them into Chroma.
        Returns the number of documents indexed.
        """
        if self.collection.count() > 0 and not force_reload:
            logger.info("Playbooks already indexed. Skipping.")
            return self.collection.count()

        playbooks = load_playbooks()
        if not playbooks:
            logger.warning("No playbooks found to index.")
            return 0

        documents = []
        metadatas = []
        ids = []

        for i, pb in enumerate(playbooks):
            # Create a searchable text representation
            text = self._playbook_to_text(pb)
            documents.append(text)
            metadatas.append({
                "technique": pb.get("Technique", "Unknown"),
                "source_file": pb.get("_source_file", ""),
            })
            ids.append(f"playbook_{i}")

        # Clear existing if force reload
        if force_reload and self.collection.count() > 0:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(self.collection_name)

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Indexed {len(documents)} playbooks")
        return len(documents)

    def retrieve(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant playbooks for a query.
        """
        if self.collection.count() == 0:
            logger.warning("Knowledge base is empty. Call index_playbooks() first.")
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )

        retrieved = []
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            retrieved.append({
                "content": doc,
                "metadata": meta,
                "distance": distance
            })
        return retrieved

    def _playbook_to_text(self, pb: Dict[str, Any]) -> str:
        """Convert a playbook dict into a single searchable string."""
        parts = [
            f"Technique: {pb.get('Technique', '')}",
            f"Goal: {pb.get('Goal', '')}",
            f"When to use: {pb.get('When to use', '')}",
        ]
        actions = pb.get("Recommended Actions", [])
        if actions:
            parts.append("Recommended Actions: " + " | ".join(actions))
        kpis = pb.get("KPIs", [])
        if kpis:
            parts.append("KPIs: " + ", ".join(kpis))
        return "\n".join(parts)