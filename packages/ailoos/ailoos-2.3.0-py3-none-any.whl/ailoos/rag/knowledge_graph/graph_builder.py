"""
Knowledge Graph Builder

This module provides functionality for constructing and maintaining
knowledge graphs from various data sources for RAG applications.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import re

import spacy
from spacy.lang.en import English

from .neo4j_graph import Neo4jGraph
from .graph_embeddings import GraphEmbeddings, GraphAnalytics

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builder for knowledge graphs from text and structured data.

    This class provides methods to extract entities, relationships, and
    concepts from documents and build comprehensive knowledge graphs.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the graph builder.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - graph_config: Configuration for the underlying graph database
                - entity_patterns: Regex patterns for entity extraction
                - relationship_patterns: Patterns for relationship extraction
                - embedding_model: Model for semantic similarity
        """
        self.config = config
        self.graph_config = config.get('graph_config', {})
        self.entity_patterns = config.get('entity_patterns', {})
        self.relationship_patterns = config.get('relationship_patterns', {})

        # Initialize graph database
        self.graph = Neo4jGraph(self.graph_config)

        # Initialize NLP model for entity extraction
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Spacy model not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Initialize advanced components
        self.embedding_model = None
        self.graph_embeddings = GraphEmbeddings(self.graph, self.embedding_model)
        self.graph_analytics = GraphAnalytics(self.graph)

    def build_from_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build knowledge graph from a collection of documents.

        Args:
            documents (List[Dict[str, Any]]): Documents to process
        """
        logger.info(f"Building knowledge graph from {len(documents)} documents")

        for doc in documents:
            try:
                self._process_document(doc)
            except Exception as e:
                logger.error(f"Error processing document {doc.get('id', 'unknown')}: {str(e)}")
                continue

        logger.info("Knowledge graph building completed")

    def _process_document(self, document: Dict[str, Any]) -> None:
        """
        Process a single document to extract entities and relationships.

        Args:
            document (Dict[str, Any]): Document to process
        """
        doc_id = document.get('id', 'unknown')
        content = document.get('content', document.get('text', ''))

        if not content:
            return

        # Extract entities
        entities = self._extract_entities(content)

        # Add document node
        self.graph.add_entity(
            entity_id=f"doc_{doc_id}",
            labels=['Document'],
            properties={
                'id': doc_id,
                'content': content[:1000],  # Truncate for storage
                'title': document.get('title', ''),
                'source': document.get('source', '')
            }
        )

        # Add entities and relationships
        for entity in entities:
            self._add_entity_and_relationships(entity, doc_id, content)

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using NLP and pattern matching.

        Args:
            text (str): Text to analyze

        Returns:
            List[Dict[str, Any]]: Extracted entities
        """
        entities = []

        # NLP-based entity extraction using spaCy
        doc = self.nlp(text)
        for ent in doc.ents:
            # Map spaCy entity types to our custom types
            entity_type = self._map_spacy_entity_type(ent.label_)
            if entity_type:
                entities.append({
                    'text': ent.text,
                    'type': entity_type,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.9,  # Higher confidence for NLP extraction
                    'source': 'nlp'
                })

        # Pattern-based entity extraction (fallback/supplement)
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        'text': match.group(),
                        'type': entity_type,
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.7,  # Lower confidence for pattern matching
                        'source': 'pattern'
                    })

        # Remove duplicates (prefer NLP over pattern matching)
        seen = {}
        for entity in entities:
            key = (entity['text'].lower(), entity['type'])
            if key not in seen or (seen[key]['source'] == 'pattern' and entity['source'] == 'nlp'):
                seen[key] = entity

        return list(seen.values())

    def _map_spacy_entity_type(self, spacy_label: str) -> Optional[str]:
        """
        Map spaCy entity labels to our custom entity types.

        Args:
            spacy_label (str): spaCy entity label

        Returns:
            Optional[str]: Mapped entity type or None if not mapped
        """
        mapping = {
            'PERSON': 'Person',
            'ORG': 'Organization',
            'GPE': 'Location',  # Geo-political entity
            'LOC': 'Location',
            'MONEY': 'Money',
            'DATE': 'Date',
            'TIME': 'Time',
            'PERCENT': 'Percentage',
            'CARDINAL': 'Number',
            'ORDINAL': 'Ordinal',
            'QUANTITY': 'Quantity',
            'PRODUCT': 'Product',
            'EVENT': 'Event',
            'WORK_OF_ART': 'WorkOfArt',
            'LAW': 'Law',
            'LANGUAGE': 'Language',
            'NORP': 'Group'  # Nationalities, religious or political groups
        }
        return mapping.get(spacy_label)

    def _extract_dependency_relationships(self, source_token, sent_entities, sentence) -> List[Dict[str, Any]]:
        """
        Extract relationships based on dependency parsing.

        Args:
            source_token: spaCy token of the source entity
            sent_entities: List of spaCy entity spans in the sentence
            sentence: spaCy sentence span

        Returns:
            List[Dict[str, Any]]: Extracted relationships
        """
        relationships = []

        # Find relationships through dependency tree
        for child in source_token.children:
            # Check for prepositional relationships
            if child.dep_ == 'prep':
                for grandchild in child.children:
                    if grandchild.dep_ == 'pobj':
                        # Find if grandchild is an entity
                        for ent in sent_entities:
                            if grandchild.text in ent.text or ent.text in grandchild.text:
                                entity_type = self._map_spacy_entity_type(ent.label_) or 'Entity'
                                target_id = f"{entity_type}_{ent.text.replace(' ', '_').lower()}"
                                rel_type = f"RELATED_TO_{child.text.upper()}"
                                relationships.append({
                                    'target_id': target_id,
                                    'type': rel_type,
                                    'properties': {
                                        'context': sentence.text[:200],
                                        'method': 'dependency',
                                        'preposition': child.text
                                    }
                                })

            # Check for direct object relationships
            elif child.dep_ in ['dobj', 'iobj']:
                for ent in sent_entities:
                    if child.text in ent.text or ent.text in child.text:
                        entity_type = self._map_spacy_entity_type(ent.label_) or 'Entity'
                        target_id = f"{entity_type}_{ent.text.replace(' ', '_').lower()}"
                        rel_type = 'ACTS_ON' if child.dep_ == 'dobj' else 'INTERACTS_WITH'
                        relationships.append({
                            'target_id': target_id,
                            'type': rel_type,
                            'properties': {
                                'context': sentence.text[:200],
                                'method': 'dependency',
                                'dependency': child.dep_
                            }
                        })

        return relationships

    def _add_entity_and_relationships(self, entity: Dict[str, Any], doc_id: str, content: str) -> None:
        """
        Add entity to graph and create relationships.

        Args:
            entity (Dict[str, Any]): Entity information
            doc_id (str): Document ID
            content (str): Full document content
        """
        entity_id = f"{entity['type']}_{entity['text'].replace(' ', '_').lower()}"

        # Add entity node
        self.graph.add_entity(
            entity_id=entity_id,
            labels=[entity['type'], 'Entity'],
            properties={
                'name': entity['text'],
                'type': entity['type'],
                'confidence': entity['confidence']
            }
        )

        # Add relationship to document
        self.graph.add_relationship(
            from_id=f"doc_{doc_id}",
            to_id=entity_id,
            relationship_type='CONTAINS',
            properties={'position': entity['start']}
        )

        # Extract relationships between entities
        # This is a simplified implementation
        relationships = self._extract_relationships(content, entity, entity_id)
        for rel in relationships:
            self.graph.add_relationship(
                from_id=entity_id,
                to_id=rel['target_id'],
                relationship_type=rel['type'],
                properties=rel.get('properties', {})
            )

    def _extract_relationships(self, content: str, source_entity: Dict[str, Any],
                              source_id: str) -> List[Dict[str, Any]]:
        """
        Extract relationships involving the source entity using NLP.

        Args:
            content (str): Document content
            source_entity (Dict[str, Any]): Source entity
            source_id (str): Source entity ID

        Returns:
            List[Dict[str, Any]]: Extracted relationships
        """
        relationships = []
        source_text = source_entity['text']

        # Process content with spaCy for dependency parsing
        doc = self.nlp(content)

        # Find sentences containing the source entity
        for sent in doc.sents:
            if source_text in sent.text:
                # Extract entities from this sentence
                sent_entities = []
                for ent in sent.ents:
                    if ent.text != source_text:
                        sent_entities.append(ent)

                # Use dependency parsing to find relationships
                for token in sent:
                    if token.text == source_text or source_text in token.text:
                        # Find relationships based on dependency tree
                        rels = self._extract_dependency_relationships(token, sent_entities, sent)
                        relationships.extend(rels)

                # Fallback: co-occurrence relationships
                for ent in sent_entities:
                    target_id = f"{self._map_spacy_entity_type(ent.label_) or 'Entity'}_{ent.text.replace(' ', '_').lower()}"
                    relationships.append({
                        'target_id': target_id,
                        'type': 'MENTIONED_WITH',
                        'properties': {'context': sent.text[:200], 'method': 'cooccurrence'}
                    })

        # Pattern-based relationships (legacy support)
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                sentences = re.split(r'[.!?]+', content)
                for sentence in sentences:
                    if source_text in sentence:
                        other_entities = self._extract_entities(sentence)
                        for other in other_entities:
                            if other['text'] != source_text:
                                target_id = f"{other['type']}_{other['text'].replace(' ', '_').lower()}"
                                relationships.append({
                                    'target_id': target_id,
                                    'type': rel_type,
                                    'properties': {'context': sentence[:200], 'method': 'pattern'}
                                })

        # Remove duplicates
        seen = set()
        unique_relationships = []
        for rel in relationships:
            key = (source_id, rel['target_id'], rel['type'])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

        return unique_relationships

    def add_semantic_relationships(self, entities: List[Dict[str, Any]]) -> None:
        """
        Add semantic relationships based on embedding similarity.

        Args:
            entities (List[Dict[str, Any]]): Entities to analyze
        """
        if not entities:
            return

        # Get entity IDs
        entity_ids = [f"{e['type']}_{e['text'].replace(' ', '_').lower()}" for e in entities]

        # Compute embeddings using graph embeddings
        embeddings = self.graph_embeddings.compute_node_embeddings(entity_ids)

        # Find similar entities and add relationships
        similarity_threshold = self.config.get('similarity_threshold', 0.8)

        for i, entity1 in enumerate(entities):
            entity1_id = entity_ids[i]

            # Find similar entities using embeddings
            if entity1_id in embeddings:
                similar_entities = self.graph_embeddings.find_similar_nodes(entity1_id, top_k=5)

                for similar_id, similarity in similar_entities:
                    if similarity >= similarity_threshold:
                        # Find corresponding entity
                        entity2_idx = entity_ids.index(similar_id) if similar_id in entity_ids else -1
                        if entity2_idx >= 0:
                            entity2 = entities[entity2_idx]

                            self.graph.add_relationship(
                                from_id=entity1_id,
                                to_id=similar_id,
                                relationship_type='SEMANTICALLY_SIMILAR',
                                properties={
                                    'similarity': similarity,
                                    'embedding_based': True
                                }
                            )

    def _compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Compute cosine similarity between embeddings."""
        import numpy as np
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

    def get_build_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph building process."""
        graph_stats = self.graph.get_graph_stats()
        centrality = self.graph_analytics.calculate_centrality('degree', limit=20)

        return {
            'graph_stats': graph_stats,
            'entity_patterns': list(self.entity_patterns.keys()),
            'relationship_patterns': list(self.relationship_patterns.keys()),
            'top_central_entities': dict(sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]),
            'embedding_stats': {
                'nodes_embedded': len(self.graph_embeddings.node_embeddings),
                'edges_embedded': len(self.graph_embeddings.edge_embeddings)
            }
        }

    def get_centrality_analysis(self, centrality_type: str = 'degree') -> Dict[str, float]:
        """Get centrality analysis for the graph."""
        return self.graph_analytics.calculate_centrality(centrality_type)

    def get_communities(self) -> Dict[str, List[str]]:
        """Get community detection results."""
        return self.graph_analytics.detect_communities()

    def find_similar_entities(self, entity_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find entities similar to the given entity."""
        return self.graph_embeddings.find_similar_nodes(entity_id, top_k)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.graph.close()