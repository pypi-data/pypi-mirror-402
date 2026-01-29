from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from .semantic_versioning import SemanticVersion


@dataclass
class VersionEntry:
    """Entrada de versión en el historial."""
    version: SemanticVersion
    model_data: Dict[str, Any]
    metadata: Dict[str, Any]
    parent_version: Optional[SemanticVersion] = None
    branch: str = "main"
    created_at: datetime = field(default_factory=datetime.now)
    commit_message: str = ""
    tags: Set[str] = field(default_factory=set)


@dataclass
class Branch:
    """Rama de versiones."""
    name: str
    head_version: Optional[SemanticVersion] = None
    created_from: Optional[SemanticVersion] = None
    created_at: datetime = field(default_factory=datetime.now)


class VersionManager:
    """
    Gestor de versiones con soporte para rollback y branching.
    Maneja múltiples ramas de desarrollo y permite operaciones avanzadas de versionado.
    """

    def __init__(self):
        self.versions: Dict[str, VersionEntry] = {}  # version_str -> VersionEntry
        self.branches: Dict[str, Branch] = {}
        self.current_branch = "main"
        self._initialize_main_branch()

    def _initialize_main_branch(self):
        """Inicializa la rama principal."""
        self.branches["main"] = Branch(name="main")

    def create_version(self,
                      model_data: Dict[str, Any],
                      metadata: Dict[str, Any],
                      commit_message: str = "",
                      branch: Optional[str] = None,
                      increment_type: str = "patch") -> SemanticVersion:
        """
        Crea una nueva versión del modelo.

        Args:
            model_data: Datos del modelo
            metadata: Metadatos adicionales
            commit_message: Mensaje del commit
            branch: Rama donde crear la versión (usa current_branch si None)
            increment_type: Tipo de incremento ('major', 'minor', 'patch')

        Returns:
            Nueva versión creada
        """
        target_branch = branch or self.current_branch

        if target_branch not in self.branches:
            raise ValueError(f"Rama '{target_branch}' no existe")

        branch_info = self.branches[target_branch]
        parent_version = branch_info.head_version

        if parent_version is None:
            # Primera versión
            new_version = SemanticVersion((1, 0, 0))
        else:
            parent_entry = self.versions[str(parent_version)]
            if increment_type == "major":
                new_version = parent_version.increment_major()
            elif increment_type == "minor":
                new_version = parent_version.increment_minor()
            elif increment_type == "patch":
                new_version = parent_version.increment_patch()
            else:
                raise ValueError(f"Tipo de incremento inválido: {increment_type}")

        # Crear entrada de versión
        version_entry = VersionEntry(
            version=new_version,
            model_data=model_data,
            metadata=metadata,
            parent_version=parent_version,
            branch=target_branch,
            commit_message=commit_message
        )

        self.versions[str(new_version)] = version_entry
        branch_info.head_version = new_version

        return new_version

    def rollback_to_version(self, target_version: SemanticVersion, create_new_version: bool = True) -> SemanticVersion:
        """
        Hace rollback a una versión anterior.

        Args:
            target_version: Versión a la que hacer rollback
            create_new_version: Si crear una nueva versión o solo cambiar head

        Returns:
            Versión resultante
        """
        if str(target_version) not in self.versions:
            raise ValueError(f"Versión {target_version} no existe")

        target_entry = self.versions[str(target_version)]
        current_branch = self.branches[self.current_branch]

        if create_new_version:
            # Crear nueva versión basada en la target
            new_version = self.create_version(
                model_data=target_entry.model_data.copy(),
                metadata=target_entry.metadata.copy(),
                commit_message=f"Rollback to {target_version}",
                branch=self.current_branch
            )
            return new_version
        else:
            # Solo cambiar el head de la rama
            current_branch.head_version = target_version
            return target_version

    def create_branch(self, branch_name: str, from_version: Optional[SemanticVersion] = None) -> Branch:
        """
        Crea una nueva rama desde una versión específica.

        Args:
            branch_name: Nombre de la nueva rama
            from_version: Versión desde la que crear la rama (usa head actual si None)

        Returns:
            Nueva rama creada
        """
        if branch_name in self.branches:
            raise ValueError(f"Rama '{branch_name}' ya existe")

        source_version = from_version or self.branches[self.current_branch].head_version

        if source_version and str(source_version) not in self.versions:
            raise ValueError(f"Versión fuente {source_version} no existe")

        new_branch = Branch(
            name=branch_name,
            head_version=source_version,
            created_from=source_version
        )

        self.branches[branch_name] = new_branch
        return new_branch

    def merge_branch(self, source_branch: str, target_branch: str = None,
                    commit_message: str = "") -> SemanticVersion:
        """
        Fusiona una rama en otra.

        Args:
            source_branch: Rama a fusionar
            target_branch: Rama destino (usa current_branch si None)
            commit_message: Mensaje del commit de fusión

        Returns:
            Nueva versión creada por la fusión
        """
        target = target_branch or self.current_branch

        if source_branch not in self.branches or target not in self.branches:
            raise ValueError("Rama fuente o destino no existe")

        source_head = self.branches[source_branch].head_version
        target_head = self.branches[target].head_version

        if not source_head:
            raise ValueError(f"Rama '{source_branch}' no tiene versiones")

        # Para simplificar, asumimos fusión fast-forward o creamos nueva versión
        source_entry = self.versions[str(source_head)]

        # Cambiar a rama destino
        old_branch = self.current_branch
        self.current_branch = target

        try:
            # Crear nueva versión en rama destino con datos de source
            new_version = self.create_version(
                model_data=source_entry.model_data.copy(),
                metadata={**source_entry.metadata, "merged_from": source_branch},
                commit_message=commit_message or f"Merge branch '{source_branch}' into {target}",
                branch=target
            )
            return new_version
        finally:
            self.current_branch = old_branch

    def switch_branch(self, branch_name: str):
        """Cambia a una rama diferente."""
        if branch_name not in self.branches:
            raise ValueError(f"Rama '{branch_name}' no existe")

        self.current_branch = branch_name

    def get_version_history(self, branch: Optional[str] = None, limit: Optional[int] = None) -> List[VersionEntry]:
        """
        Obtiene el historial de versiones de una rama.

        Args:
            branch: Rama a consultar (usa current_branch si None)
            limit: Número máximo de versiones a retornar

        Returns:
            Lista de entradas de versión en orden cronológico inverso
        """
        target_branch = branch or self.current_branch

        if target_branch not in self.branches:
            return []

        branch_info = self.branches[target_branch]
        if not branch_info.head_version:
            return []

        # Recorrer el historial desde head hacia atrás
        history = []
        current = branch_info.head_version

        while current and (limit is None or len(history) < limit):
            if str(current) in self.versions:
                entry = self.versions[str(current)]
                if entry.branch == target_branch:  # Solo versiones de esta rama
                    history.append(entry)
                current = entry.parent_version
            else:
                break

        return history

    def tag_version(self, version: SemanticVersion, tag: str):
        """Agrega un tag a una versión."""
        if str(version) not in self.versions:
            raise ValueError(f"Versión {version} no existe")

        self.versions[str(version)].tags.add(tag)

    def get_version_by_tag(self, tag: str) -> Optional[SemanticVersion]:
        """Obtiene la versión asociada a un tag."""
        for version_str, entry in self.versions.items():
            if tag in entry.tags:
                return entry.version
        return None

    def get_current_version(self, branch: Optional[str] = None) -> Optional[SemanticVersion]:
        """Obtiene la versión actual (head) de una rama."""
        target_branch = branch or self.current_branch
        branch_info = self.branches.get(target_branch)
        return branch_info.head_version if branch_info else None

    def list_branches(self) -> List[Branch]:
        """Lista todas las ramas."""
        return list(self.branches.values())

    def delete_branch(self, branch_name: str):
        """Elimina una rama (excepto main)."""
        if branch_name == "main":
            raise ValueError("No se puede eliminar la rama main")

        if branch_name not in self.branches:
            raise ValueError(f"Rama '{branch_name}' no existe")

        # Verificar que no sea la rama actual
        if branch_name == self.current_branch:
            raise ValueError("No se puede eliminar la rama actual")

        del self.branches[branch_name]