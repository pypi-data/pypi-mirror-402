"""
API Layer para el Grafo de Conocimiento AILOOS.
Proporciona interfaces REST y GraphQL para operaciones CRUD, consultas e inferencias.
"""

from .rest_api import KnowledgeGraphRESTAPI
from .graphql_api import KnowledgeGraphGraphQLAPI

__all__ = [
    'KnowledgeGraphRESTAPI',
    'KnowledgeGraphGraphQLAPI'
]