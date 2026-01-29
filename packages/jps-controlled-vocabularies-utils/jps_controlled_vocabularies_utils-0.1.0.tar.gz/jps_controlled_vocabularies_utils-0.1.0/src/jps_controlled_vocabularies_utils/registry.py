"""
Registry model for managing loaded vocabularies.
"""

from typing import Any

from pydantic import BaseModel, Field

from jps_controlled_vocabularies_utils.exceptions import NotFoundError
from jps_controlled_vocabularies_utils.record import Record
from jps_controlled_vocabularies_utils.vocabulary import Vocabulary


class Registry(BaseModel):
    """In-memory registry of loaded controlled vocabularies.

    The registry provides indexed access to vocabularies and their terms,
    supporting efficient retrieval by vocabulary ID and term key.

    Attributes:
        vocabularies: Dictionary mapping vocabulary_id to Vocabulary objects.
        metadata: Additional registry-level metadata.
    """

    vocabularies: dict[str, Vocabulary] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def list_vocabulary_ids(self) -> list[str]:
        """Return list of all vocabulary IDs in the registry.

        Returns:
            List of vocabulary IDs.
        """
        return list(self.vocabularies.keys())

    def get_vocabulary(self, vocabulary_id: str) -> Vocabulary:
        """Retrieve a vocabulary by its ID.

        Args:
            vocabulary_id: The unique identifier for the vocabulary.

        Returns:
            The Vocabulary object.

        Raises:
            NotFoundError: If the vocabulary_id is not found.
        """
        if vocabulary_id not in self.vocabularies:
            raise NotFoundError(
                f"Vocabulary '{vocabulary_id}' not found",
                context={"vocabulary_id": vocabulary_id},
            )
        return self.vocabularies[vocabulary_id]

    def list_terms(self, vocabulary_id: str) -> list[Record]:
        """List all terms in a vocabulary.

        Args:
            vocabulary_id: The unique identifier for the vocabulary.

        Returns:
            List of Record objects.

        Raises:
            NotFoundError: If the vocabulary_id is not found.
        """
        vocab = self.get_vocabulary(vocabulary_id)
        return vocab.terms

    def get_term(self, vocabulary_id: str, term_key: str) -> Record:
        """Retrieve a term by its key within a vocabulary.

        Args:
            vocabulary_id: The unique identifier for the vocabulary.
            term_key: The term's key (or normalized name).

        Returns:
            The Record object.

        Raises:
            NotFoundError: If the vocabulary or term is not found.
        """
        vocab = self.get_vocabulary(vocabulary_id)
        for term in vocab.terms:
            if term.key == term_key:
                return term
        raise NotFoundError(
            f"Term '{term_key}' not found in vocabulary '{vocabulary_id}'",
            context={"vocabulary_id": vocabulary_id, "term_key": term_key},
        )

    def search_terms(
        self,
        vocabulary_id: str,
        query: str,
        case_sensitive: bool = False,
        search_mode: str = "contains",
    ) -> list[Record]:
        """Search terms within a vocabulary by name, key, or synonyms.

        Args:
            vocabulary_id: The unique identifier for the vocabulary.
            query: The search query string.
            case_sensitive: Whether to perform case-sensitive search.
            search_mode: Search mode - 'prefix', 'contains', or 'exact'.

        Returns:
            List of matching Record objects.

        Raises:
            NotFoundError: If the vocabulary_id is not found.
        """
        vocab = self.get_vocabulary(vocabulary_id)
        results: list[Record] = []

        query_str = query if case_sensitive else query.lower()

        for term in vocab.terms:
            # Search in name
            name_str = term.name if case_sensitive else term.name.lower()
            key_str = term.key if case_sensitive else (term.key or "").lower()

            matches = False
            if search_mode == "exact":
                matches = name_str == query_str or key_str == query_str
            elif search_mode == "prefix":
                matches = name_str.startswith(query_str) or key_str.startswith(query_str)
            else:  # contains
                matches = query_str in name_str or query_str in key_str

            # Also search in synonyms
            if not matches and term.synonyms:
                for synonym in term.synonyms:
                    syn_str = synonym if case_sensitive else synonym.lower()
                    if search_mode == "exact":
                        matches = syn_str == query_str
                    elif search_mode == "prefix":
                        matches = syn_str.startswith(query_str)
                    else:  # contains
                        matches = query_str in syn_str
                    if matches:
                        break

            if matches:
                results.append(term)

        return results

    model_config = {
        "extra": "allow",
    }
