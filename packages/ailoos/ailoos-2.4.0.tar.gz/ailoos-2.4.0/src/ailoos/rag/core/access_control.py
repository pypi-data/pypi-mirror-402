"""
Document Level Access Control (DLAC) for RAG Systems
====================================================

Este módulo implementa control de acceso a nivel de documento para sistemas RAG,
permitiendo filtrar documentos basados en permisos de usuario, roles, y políticas
de acceso antes de que sean devueltos por el retriever.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Niveles de acceso disponibles."""
    PUBLIC = "public"          # Acceso público
    INTERNAL = "internal"      # Solo usuarios internos
    CONFIDENTIAL = "confidential"  # Información confidencial
    RESTRICTED = "restricted"  # Acceso restringido
    SECRET = "secret"          # Información secreta


class AccessDecision(Enum):
    """Decisiones de acceso posibles."""
    ALLOW = "allow"            # Permitir acceso
    DENY = "deny"             # Denegar acceso
    MASK = "mask"             # Permitir pero enmascarar contenido sensible
    REDACT = "redact"         # Permitir pero redactar información


@dataclass
class AccessPolicy:
    """Política de acceso para documentos."""
    name: str
    description: str = ""
    access_level: AccessLevel = AccessLevel.PUBLIC
    allowed_roles: Set[str] = field(default_factory=set)
    allowed_users: Set[int] = field(default_factory=set)
    denied_users: Set[int] = field(default_factory=set)
    conditions: List[Callable[[Dict[str, Any], Dict[str, Any]], bool]] = field(default_factory=list)
    decision: AccessDecision = AccessDecision.ALLOW

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la política a diccionario."""
        return {
            "name": self.name,
            "description": self.description,
            "access_level": self.access_level.value,
            "allowed_roles": list(self.allowed_roles),
            "allowed_users": list(self.allowed_users),
            "denied_users": list(self.denied_users),
            "decision": self.decision.value
        }


@dataclass
class UserContext:
    """Contexto de usuario para evaluación de acceso."""
    user_id: Optional[int] = None
    roles: Set[str] = field(default_factory=set)
    groups: Set[str] = field(default_factory=set)
    clearance_level: AccessLevel = AccessLevel.PUBLIC
    attributes: Dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        """Verifica si el usuario tiene un rol específico."""
        return role in self.roles

    def has_any_role(self, roles: Set[str]) -> bool:
        """Verifica si el usuario tiene al menos uno de los roles."""
        return bool(self.roles.intersection(roles))

    def is_user_allowed(self, allowed_users: Set[int]) -> bool:
        """Verifica si el usuario está en la lista de permitidos."""
        return self.user_id is not None and self.user_id in allowed_users

    def is_user_denied(self, denied_users: Set[int]) -> bool:
        """Verifica si el usuario está en la lista de denegados."""
        return self.user_id is not None and self.user_id in denied_users


@dataclass
class DocumentMetadata:
    """Metadata de documento para control de acceso."""
    document_id: str
    access_level: AccessLevel = AccessLevel.PUBLIC
    owner_id: Optional[int] = None
    allowed_users: Set[int] = field(default_factory=set)
    allowed_roles: Set[str] = field(default_factory=set)
    denied_users: Set[int] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    custom_policies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte metadata a diccionario."""
        return {
            "document_id": self.document_id,
            "access_level": self.access_level.value,
            "owner_id": self.owner_id,
            "allowed_users": list(self.allowed_users),
            "allowed_roles": list(self.allowed_roles),
            "denied_users": list(self.denied_users),
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "custom_policies": self.custom_policies
        }


class AccessControlEngine:
    """
    Motor de control de acceso que evalúa permisos de usuario contra documentos.

    Este motor implementa una lógica de evaluación de políticas que determina
    si un usuario puede acceder a un documento específico.
    """

    def __init__(self, policies: Optional[List[AccessPolicy]] = None):
        """
        Inicializa el motor de control de acceso.

        Args:
            policies: Lista de políticas de acceso
        """
        self.policies = policies or []
        self.audit_log: List[Dict[str, Any]] = []
        logger.info("AccessControlEngine inicializado")

    def add_policy(self, policy: AccessPolicy) -> None:
        """Agrega una política de acceso."""
        self.policies.append(policy)
        logger.info(f"Política agregada: {policy.name}")

    def evaluate_access(self, user_context: UserContext,
                       document_metadata: DocumentMetadata) -> AccessDecision:
        """
        Evalúa el acceso de un usuario a un documento.

        Args:
            user_context: Contexto del usuario
            document_metadata: Metadata del documento

        Returns:
            Decisión de acceso
        """
        # Verificar expiración
        if document_metadata.expires_at and datetime.now() > document_metadata.expires_at:
            self._log_access(user_context, document_metadata, AccessDecision.DENY, "Documento expirado")
            return AccessDecision.DENY

        # Verificar usuario denegado explícitamente
        if user_context.is_user_denied(document_metadata.denied_users):
            self._log_access(user_context, document_metadata, AccessDecision.DENY, "Usuario denegado")
            return AccessDecision.DENY

        # Verificar propietario
        if document_metadata.owner_id == user_context.user_id:
            self._log_access(user_context, document_metadata, AccessDecision.ALLOW, "Propietario del documento")
            return AccessDecision.ALLOW

        # Verificar usuarios permitidos explícitamente
        if user_context.is_user_allowed(document_metadata.allowed_users):
            self._log_access(user_context, document_metadata, AccessDecision.ALLOW, "Usuario permitido")
            return AccessDecision.ALLOW

        # Verificar roles permitidos
        if document_metadata.allowed_roles and user_context.has_any_role(document_metadata.allowed_roles):
            self._log_access(user_context, document_metadata, AccessDecision.ALLOW, "Rol permitido")
            return AccessDecision.ALLOW

        # Verificar nivel de acceso
        if self._check_clearance_level(user_context.clearance_level, document_metadata.access_level):
            self._log_access(user_context, document_metadata, AccessDecision.ALLOW, "Nivel de acceso suficiente")
            return AccessDecision.ALLOW

        # Aplicar políticas personalizadas
        for policy_name in document_metadata.custom_policies:
            policy = self._get_policy_by_name(policy_name)
            if policy:
                decision = self._evaluate_policy(policy, user_context, document_metadata)
                if decision != AccessDecision.ALLOW:  # Si no es allow, aplicar la decisión
                    self._log_access(user_context, document_metadata, decision, f"Política: {policy_name}")
                    return decision

        # Aplicar políticas globales
        for policy in self.policies:
            decision = self._evaluate_policy(policy, user_context, document_metadata)
            if decision != AccessDecision.ALLOW:
                self._log_access(user_context, document_metadata, decision, f"Política global: {policy.name}")
                return decision

        # Denegar por defecto
        self._log_access(user_context, document_metadata, AccessDecision.DENY, "Acceso denegado por defecto")
        return AccessDecision.DENY

    def _check_clearance_level(self, user_level: AccessLevel, doc_level: AccessLevel) -> bool:
        """Verifica si el nivel de clearance del usuario es suficiente."""
        level_hierarchy = {
            AccessLevel.PUBLIC: 0,
            AccessLevel.INTERNAL: 1,
            AccessLevel.CONFIDENTIAL: 2,
            AccessLevel.RESTRICTED: 3,
            AccessLevel.SECRET: 4
        }
        return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(doc_level, 0)

    def _evaluate_policy(self, policy: AccessPolicy, user_context: UserContext,
                        document_metadata: DocumentMetadata) -> AccessDecision:
        """Evalúa una política específica."""
        # Verificar condiciones de la política
        for condition in policy.conditions:
            try:
                if not condition(user_context.__dict__, document_metadata.__dict__):
                    continue  # Condición no cumplida, pasar a siguiente
            except Exception as e:
                logger.warning(f"Error evaluando condición de política {policy.name}: {e}")
                continue

        # Verificar usuario denegado
        if user_context.is_user_denied(policy.denied_users):
            return AccessDecision.DENY

        # Verificar usuarios permitidos
        if policy.allowed_users and user_context.is_user_allowed(policy.allowed_users):
            return policy.decision

        # Verificar roles
        if policy.allowed_roles and user_context.has_any_role(policy.allowed_roles):
            return policy.decision

        # Verificar nivel de acceso
        if self._check_clearance_level(user_context.clearance_level, policy.access_level):
            return policy.decision

        return AccessDecision.ALLOW  # No aplica la política

    def _get_policy_by_name(self, name: str) -> Optional[AccessPolicy]:
        """Obtiene una política por nombre."""
        return next((p for p in self.policies if p.name == name), None)

    def _log_access(self, user_context: UserContext, document_metadata: DocumentMetadata,
                   decision: AccessDecision, reason: str) -> None:
        """Registra un evento de acceso en el audit log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_context.user_id,
            "document_id": document_metadata.document_id,
            "decision": decision.value,
            "reason": reason,
            "user_roles": list(user_context.roles),
            "document_access_level": document_metadata.access_level.value
        }
        self.audit_log.append(log_entry)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Obtiene el log de auditoría."""
        return self.audit_log.copy()

    def clear_audit_log(self) -> None:
        """Limpia el log de auditoría."""
        self.audit_log.clear()


class DocumentAccessFilter:
    """
    Filtro de acceso a documentos que integra DLAC con el retriever de RAG.

    Este componente filtra los resultados del retriever basándose en las políticas
    de acceso, asegurando que solo se devuelvan documentos a los que el usuario
    tiene permiso de acceso.
    """

    def __init__(self, access_engine: Optional[AccessControlEngine] = None):
        """
        Inicializa el filtro de acceso.

        Args:
            access_engine: Motor de control de acceso
        """
        self.access_engine = access_engine or AccessControlEngine()
        self.document_metadata_cache: Dict[str, DocumentMetadata] = {}
        logger.info("DocumentAccessFilter inicializado")

    def filter_results(self, user_context: UserContext,
                      search_results: List[Tuple[Dict[str, Any], float]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Filtra resultados de búsqueda basados en permisos de acceso.

        Args:
            user_context: Contexto del usuario
            search_results: Resultados de búsqueda (documento, score)

        Returns:
            Resultados filtrados
        """
        filtered_results = []

        for document, score in search_results:
            doc_id = document.get('id') or document.get('document_id')
            if not doc_id:
                logger.warning("Documento sin ID encontrado, omitiendo")
                continue

            # Obtener metadata del documento
            metadata = self._get_document_metadata(doc_id, document)

            # Evaluar acceso
            decision = self.access_engine.evaluate_access(user_context, metadata)

            if decision == AccessDecision.ALLOW:
                filtered_results.append((document, score))
            elif decision == AccessDecision.MASK:
                masked_doc = self._mask_document(document)
                filtered_results.append((masked_doc, score))
            elif decision == AccessDecision.REDACT:
                redacted_doc = self._redact_document(document)
                filtered_results.append((redacted_doc, score))
            # DENY: simplemente no incluir en resultados

        logger.info(f"Filtrado completado: {len(search_results)} -> {len(filtered_results)} documentos")
        return filtered_results

    def _get_document_metadata(self, doc_id: str, document: Dict[str, Any]) -> DocumentMetadata:
        """Obtiene metadata de documento desde cache o documento."""
        if doc_id in self.document_metadata_cache:
            return self.document_metadata_cache[doc_id]

        # Extraer metadata del documento
        metadata = DocumentMetadata(document_id=doc_id)

        # Intentar extraer campos de metadata del documento
        if 'access_level' in document:
            metadata.access_level = AccessLevel(document['access_level'])
        if 'owner_id' in document:
            metadata.owner_id = document['owner_id']
        if 'allowed_users' in document:
            metadata.allowed_users = set(document['allowed_users'])
        if 'allowed_roles' in document:
            metadata.allowed_roles = set(document['allowed_roles'])
        if 'denied_users' in document:
            metadata.denied_users = set(document['denied_users'])
        if 'tags' in document:
            metadata.tags = set(document['tags'])
        if 'custom_policies' in document:
            metadata.custom_policies = document['custom_policies']

        # Cachear metadata
        self.document_metadata_cache[doc_id] = metadata
        return metadata

    def _mask_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Enmascara contenido sensible del documento."""
        masked = document.copy()
        # Implementar lógica de enmascaramiento según necesidades
        # Por ejemplo, reemplazar campos sensibles con placeholders
        return masked

    def _redact_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Redacta información sensible del documento."""
        redacted = document.copy()
        # Implementar lógica de redacción
        return redacted

    def update_document_metadata(self, doc_id: str, metadata: DocumentMetadata) -> None:
        """Actualiza metadata de documento en cache."""
        self.document_metadata_cache[doc_id] = metadata

    def clear_metadata_cache(self) -> None:
        """Limpia la cache de metadata."""
        self.document_metadata_cache.clear()