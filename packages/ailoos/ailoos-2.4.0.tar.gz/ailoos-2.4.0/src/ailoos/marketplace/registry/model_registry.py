"""
Model Registry para AILOOS Marketplace.
Gestiona registro, versionado y linaje de modelos federados con validación criptográfica.
"""

import asyncio
import json
import time
import hashlib
import zlib
import pickle
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiosqlite
from pathlib import Path

from ...core.logging import get_logger
from ...federated.weight_compression import WeightCompressor

logger = get_logger(__name__)


class ModelStatus(Enum):
    """Estados posibles de un modelo."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class VersionType(Enum):
    """Tipos de versiones."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class ModelMetadata:
    """Metadatos de un modelo."""
    model_id: str
    name: str
    description: str
    version: str
    publisher_address: str
    status: ModelStatus
    architecture: str
    framework: str
    dataset_info: Dict[str, Any]
    performance_metrics: Dict[str, float]
    created_at: float
    updated_at: float
    tags: List[str]
    license: str
    ipfs_cid: Optional[str] = None
    model_hash: Optional[str] = None


@dataclass
class FederatedLineage:
    """Linaje completo de un modelo federado."""
    model_id: str
    contributors: List[Dict[str, Any]]  # [{'address': str, 'contribution_weight': float, 'rounds': List[int]}]
    datasets: List[Dict[str, Any]]      # [{'dataset_id': str, 'samples': int, 'quality_score': float}]
    training_rounds: List[Dict[str, Any]]  # [{'round_id': int, 'participants': List[str], 'aggregator': str}]
    privacy_measures: Dict[str, Any]    # {'differential_privacy': bool, 'noise_multiplier': float, etc.}
    federated_metrics: Dict[str, Any]   # {'convergence_rate': float, 'communication_cost': int}


@dataclass
class VersionInfo:
    """Información de versión git-like."""
    version_id: str
    model_id: str
    version_tag: str
    parent_version: Optional[str]
    branch: str
    commit_message: str
    author: str
    timestamp: float
    diff_hash: Optional[str] = None
    compressed_diff: Optional[bytes] = None


class ModelRegistry:
    """
    Registry completo para modelos de ML federados.
    Incluye validación criptográfica, versionado git-like, linaje federado y persistencia.
    """

    def __init__(self, db_path: str = "./data/model_registry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.compressor = WeightCompressor()
        self._initialized = False

    async def initialize(self):
        """Inicializar base de datos y tablas."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # Tabla de modelos
            await db.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    model_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT NOT NULL,
                    publisher_address TEXT NOT NULL,
                    status TEXT NOT NULL,
                    architecture TEXT,
                    framework TEXT,
                    dataset_info TEXT,  -- JSON
                    performance_metrics TEXT,  -- JSON
                    created_at REAL,
                    updated_at REAL,
                    tags TEXT,  -- JSON
                    license TEXT,
                    ipfs_cid TEXT,
                    model_hash TEXT
                )
            ''')

            # Tabla de versiones (git-like)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS versions (
                    version_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    version_tag TEXT NOT NULL,
                    parent_version TEXT,
                    branch TEXT NOT NULL,
                    commit_message TEXT,
                    author TEXT NOT NULL,
                    timestamp REAL,
                    diff_hash TEXT,
                    compressed_diff BLOB,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            ''')

            # Tabla de linaje federado
            await db.execute('''
                CREATE TABLE IF NOT EXISTS federated_lineage (
                    model_id TEXT PRIMARY KEY,
                    contributors TEXT,  -- JSON
                    datasets TEXT,      -- JSON
                    training_rounds TEXT,  -- JSON
                    privacy_measures TEXT, -- JSON
                    federated_metrics TEXT, -- JSON
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            ''')

            # Tabla de firmas criptográficas
            await db.execute('''
                CREATE TABLE IF NOT EXISTS signatures (
                    signature_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    version_id TEXT,
                    signer_address TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    message_hash TEXT NOT NULL,
                    signed_at REAL,
                    is_valid BOOLEAN DEFAULT 1,
                    FOREIGN KEY (model_id) REFERENCES models (model_id),
                    FOREIGN KEY (version_id) REFERENCES versions (version_id)
                )
            ''')

            # Índices para optimización
            await db.execute('CREATE INDEX IF NOT EXISTS idx_models_publisher ON models (publisher_address)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_models_status ON models (status)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_versions_model ON versions (model_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_versions_branch ON versions (model_id, branch)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_signatures_model ON signatures (model_id)')

            await db.commit()
            self._initialized = True

        logger.info(f"🗄️ Model Registry initialized at {self.db_path}")

    async def register_model(self, model_data: Dict[str, Any], publisher_private_key: str) -> Dict[str, Any]:
        """
        Registra un nuevo modelo con validación criptográfica de firma.

        Args:
            model_data: Datos del modelo incluyendo metadatos, pesos, etc.
            publisher_private_key: Clave privada para firmar el registro

        Returns:
            Dict con resultado del registro
        """
        try:
            await self.initialize()

            # Extraer metadatos
            metadata = ModelMetadata(
                model_id=model_data['model_id'],
                name=model_data['name'],
                description=model_data.get('description', ''),
                version='1.0.0',
                publisher_address=model_data['publisher_address'],
                status=ModelStatus.DRAFT,
                architecture=model_data.get('architecture', 'unknown'),
                framework=model_data.get('framework', 'unknown'),
                dataset_info=model_data.get('dataset_info', {}),
                performance_metrics=model_data.get('performance_metrics', {}),
                created_at=time.time(),
                updated_at=time.time(),
                tags=model_data.get('tags', []),
                license=model_data.get('license', 'MIT'),
                ipfs_cid=model_data.get('ipfs_cid'),
                model_hash=self._calculate_model_hash(model_data.get('weights', {}))
            )

            # Validar metadatos
            validation_result = self._validate_metadata(metadata)
            if not validation_result['valid']:
                return {'success': False, 'error': f'Invalid metadata: {validation_result["errors"]}'}

            # Crear firma criptográfica
            message = f"{metadata.model_id}:{metadata.name}:{metadata.version}:{metadata.created_at}"
            signature = self._create_signature(message, publisher_private_key)

            # Verificar firma
            if not self._verify_signature(message, signature, metadata.publisher_address):
                return {'success': False, 'error': 'Invalid signature'}

            # Procesar linaje federado si existe
            lineage = None
            if 'federated_lineage' in model_data:
                lineage = FederatedLineage(
                    model_id=metadata.model_id,
                    contributors=model_data['federated_lineage'].get('contributors', []),
                    datasets=model_data['federated_lineage'].get('datasets', []),
                    training_rounds=model_data['federated_lineage'].get('training_rounds', []),
                    privacy_measures=model_data['federated_lineage'].get('privacy_measures', {}),
                    federated_metrics=model_data['federated_lineage'].get('federated_metrics', {})
                )

            # Persistir en BD
            async with aiosqlite.connect(self.db_path) as db:
                # Insertar modelo
                await db.execute('''
                    INSERT INTO models (
                        model_id, name, description, version, publisher_address, status,
                        architecture, framework, dataset_info, performance_metrics,
                        created_at, updated_at, tags, license, ipfs_cid, model_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata.model_id, metadata.name, metadata.description, metadata.version,
                    metadata.publisher_address, metadata.status.value, metadata.architecture,
                    metadata.framework, json.dumps(metadata.dataset_info),
                    json.dumps(metadata.performance_metrics), metadata.created_at,
                    metadata.updated_at, json.dumps(metadata.tags), metadata.license,
                    metadata.ipfs_cid, metadata.model_hash
                ))

                # Insertar linaje si existe
                if lineage:
                    await db.execute('''
                        INSERT INTO federated_lineage (
                            model_id, contributors, datasets, training_rounds,
                            privacy_measures, federated_metrics
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        lineage.model_id, json.dumps(lineage.contributors),
                        json.dumps(lineage.datasets), json.dumps(lineage.training_rounds),
                        json.dumps(lineage.privacy_measures), json.dumps(lineage.federated_metrics)
                    ))

                # Insertar firma
                signature_id = f"sig_{metadata.model_id}_{int(time.time())}"
                await db.execute('''
                    INSERT INTO signatures (
                        signature_id, model_id, signer_address, signature,
                        message_hash, signed_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    signature_id, metadata.model_id, metadata.publisher_address,
                    signature, hashlib.sha256(message.encode()).hexdigest(), time.time()
                ))

                # Crear versión inicial
                version_info = VersionInfo(
                    version_id=f"v_{metadata.model_id}_1.0.0",
                    model_id=metadata.model_id,
                    version_tag='1.0.0',
                    parent_version=None,
                    branch='main',
                    commit_message='Initial model registration',
                    author=metadata.publisher_address,
                    timestamp=time.time()
                )

                await db.execute('''
                    INSERT INTO versions (
                        version_id, model_id, version_tag, parent_version, branch,
                        commit_message, author, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version_info.version_id, version_info.model_id, version_info.version_tag,
                    version_info.parent_version, version_info.branch, version_info.commit_message,
                    version_info.author, version_info.timestamp
                ))

                await db.commit()

            logger.info(f"✅ Model {metadata.model_id} registered successfully")
            return {
                'success': True,
                'model_id': metadata.model_id,
                'version': metadata.version,
                'signature': signature
            }

        except Exception as e:
            logger.error(f"❌ Error registering model: {e}")
            return {'success': False, 'error': str(e)}

    async def update_version(self, model_id: str, new_weights: Dict[str, Any],
                           update_data: Dict[str, Any], author_private_key: str) -> Dict[str, Any]:
        """
        Actualiza versión del modelo con diff compression.

        Args:
            model_id: ID del modelo
            new_weights: Nuevos pesos del modelo
            update_data: Datos de actualización (mensaje, tipo de versión, etc.)
            author_private_key: Clave privada del autor

        Returns:
            Dict con resultado de la actualización
        """
        try:
            await self.initialize()

            # Obtener modelo actual
            current_model = await self._get_model(model_id)
            if not current_model:
                return {'success': False, 'error': 'Model not found'}

            # Obtener versión actual
            current_version = await self._get_latest_version(model_id, 'main')
            if not current_version:
                return {'success': False, 'error': 'No versions found'}

            # Calcular nueva versión
            new_version_tag = self._increment_version(current_version['version_tag'],
                                                    update_data.get('version_type', 'patch'))

            # Calcular diff comprimido
            old_weights = await self._get_weights_for_version(current_version['version_id'])
            diff_data = self._calculate_weight_diff(old_weights, new_weights)
            compressed_diff = self._compress_diff(diff_data)

            # Crear nueva versión
            version_info = VersionInfo(
                version_id=f"v_{model_id}_{new_version_tag}_{int(time.time())}",
                model_id=model_id,
                version_tag=new_version_tag,
                parent_version=current_version['version_id'],
                branch=update_data.get('branch', 'main'),
                commit_message=update_data.get('message', 'Model update'),
                author=update_data.get('author_address', current_model['publisher_address']),
                timestamp=time.time(),
                diff_hash=hashlib.sha256(compressed_diff).hexdigest(),
                compressed_diff=compressed_diff
            )

            # Firmar actualización
            message = f"{version_info.version_id}:{version_info.commit_message}:{version_info.timestamp}"
            signature = self._create_signature(message, author_private_key)

            # Persistir
            async with aiosqlite.connect(self.db_path) as db:
                # Insertar nueva versión
                await db.execute('''
                    INSERT INTO versions (
                        version_id, model_id, version_tag, parent_version, branch,
                        commit_message, author, timestamp, diff_hash, compressed_diff
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version_info.version_id, version_info.model_id, version_info.version_tag,
                    version_info.parent_version, version_info.branch, version_info.commit_message,
                    version_info.author, version_info.timestamp, version_info.diff_hash,
                    version_info.compressed_diff
                ))

                # Actualizar modelo
                await db.execute('''
                    UPDATE models SET
                        version = ?,
                        updated_at = ?,
                        model_hash = ?
                    WHERE model_id = ?
                ''', (
                    new_version_tag, time.time(),
                    self._calculate_model_hash(new_weights), model_id
                ))

                # Insertar firma
                signature_id = f"sig_{version_info.version_id}_{int(time.time())}"
                await db.execute('''
                    INSERT INTO signatures (
                        signature_id, model_id, version_id, signer_address, signature,
                        message_hash, signed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signature_id, model_id, version_info.version_id, version_info.author,
                    signature, hashlib.sha256(message.encode()).hexdigest(), time.time()
                ))

                await db.commit()

            logger.info(f"✅ Model {model_id} updated to version {new_version_tag}")
            return {
                'success': True,
                'model_id': model_id,
                'new_version': new_version_tag,
                'version_id': version_info.version_id,
                'signature': signature
            }

        except Exception as e:
            logger.error(f"❌ Error updating model version: {e}")
            return {'success': False, 'error': str(e)}

    async def create_branch(self, model_id: str, branch_name: str, from_version: Optional[str] = None) -> Dict[str, Any]:
        """Crea una nueva rama desde una versión específica."""
        try:
            await self.initialize()

            if not from_version:
                # Obtener última versión de main
                latest = await self._get_latest_version(model_id, 'main')
                if not latest:
                    return {'success': False, 'error': 'No main branch found'}
                from_version = latest['version_id']

            # Verificar que la rama no existe
            existing = await self._get_latest_version(model_id, branch_name)
            if existing:
                return {'success': False, 'error': f'Branch {branch_name} already exists'}

            # Crear commit inicial de la rama
            version_info = VersionInfo(
                version_id=f"v_{model_id}_{branch_name}_initial_{int(time.time())}",
                model_id=model_id,
                version_tag=f"{branch_name}-initial",
                parent_version=from_version,
                branch=branch_name,
                commit_message=f'Create branch {branch_name}',
                author='system',
                timestamp=time.time()
            )

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO versions (
                        version_id, model_id, version_tag, parent_version, branch,
                        commit_message, author, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version_info.version_id, version_info.model_id, version_info.version_tag,
                    version_info.parent_version, version_info.branch, version_info.commit_message,
                    version_info.author, version_info.timestamp
                ))
                await db.commit()

            return {'success': True, 'branch': branch_name, 'from_version': from_version}

        except Exception as e:
            logger.error(f"❌ Error creating branch: {e}")
            return {'success': False, 'error': str(e)}

    async def create_tag(self, model_id: str, version_id: str, tag_name: str, author: str) -> Dict[str, Any]:
        """Crea un tag en una versión específica."""
        try:
            await self.initialize()

            # Verificar que la versión existe
            version = await self._get_version(version_id)
            if not version or version['model_id'] != model_id:
                return {'success': False, 'error': 'Version not found'}

            # Crear versión con tag
            version_info = VersionInfo(
                version_id=f"tag_{model_id}_{tag_name}_{int(time.time())}",
                model_id=model_id,
                version_tag=tag_name,
                parent_version=version_id,
                branch='tags',
                commit_message=f'Tag {tag_name}',
                author=author,
                timestamp=time.time()
            )

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO versions (
                        version_id, model_id, version_tag, parent_version, branch,
                        commit_message, author, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version_info.version_id, version_info.model_id, version_info.version_tag,
                    version_info.parent_version, version_info.branch, version_info.commit_message,
                    version_info.author, version_info.timestamp
                ))
                await db.commit()

            return {'success': True, 'tag': tag_name, 'version_id': version_id}

        except Exception as e:
            logger.error(f"❌ Error creating tag: {e}")
            return {'success': False, 'error': str(e)}

    async def get_model_lineage(self, model_id: str) -> Optional[FederatedLineage]:
        """Obtiene el linaje federado completo de un modelo."""
        try:
            await self.initialize()

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT * FROM federated_lineage WHERE model_id = ?', (model_id,))
                row = await cursor.fetchone()

            if not row:
                return None

            return FederatedLineage(
                model_id=row[0],
                contributors=json.loads(row[1]),
                datasets=json.loads(row[2]),
                training_rounds=json.loads(row[3]),
                privacy_measures=json.loads(row[4]),
                federated_metrics=json.loads(row[5])
            )

        except Exception as e:
            logger.error(f"❌ Error getting model lineage: {e}")
            return None

    async def query_models(self, filters: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Consulta modelos con filtros avanzados."""
        try:
            await self.initialize()

            query = "SELECT * FROM models WHERE 1=1"
            params = []

            if 'publisher' in filters:
                query += " AND publisher_address = ?"
                params.append(filters['publisher'])

            if 'status' in filters:
                query += " AND status = ?"
                params.append(filters['status'])

            if 'tags' in filters:
                # Búsqueda en JSON array
                tags_json = json.dumps(filters['tags'])
                query += " AND tags LIKE ?"
                params.append(f'%{tags_json}%')

            if 'architecture' in filters:
                query += " AND architecture = ?"
                params.append(filters['architecture'])

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()

            models = []
            for row in rows:
                models.append({
                    'model_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'version': row[3],
                    'publisher_address': row[4],
                    'status': row[5],
                    'architecture': row[6],
                    'framework': row[7],
                    'dataset_info': json.loads(row[8]) if row[8] else {},
                    'performance_metrics': json.loads(row[9]) if row[9] else {},
                    'created_at': row[10],
                    'updated_at': row[11],
                    'tags': json.loads(row[12]) if row[12] else [],
                    'license': row[13],
                    'ipfs_cid': row[14],
                    'model_hash': row[15]
                })

            return models

        except Exception as e:
            logger.error(f"❌ Error querying models: {e}")
            return []

    async def get_version_history(self, model_id: str, branch: str = 'main') -> List[Dict[str, Any]]:
        """Obtiene historial de versiones de un modelo."""
        try:
            await self.initialize()

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT * FROM versions
                    WHERE model_id = ? AND branch = ?
                    ORDER BY timestamp DESC
                ''', (model_id, branch))
                rows = await cursor.fetchall()

            versions = []
            for row in rows:
                versions.append({
                    'version_id': row[0],
                    'model_id': row[1],
                    'version_tag': row[2],
                    'parent_version': row[3],
                    'branch': row[4],
                    'commit_message': row[5],
                    'author': row[6],
                    'timestamp': row[7],
                    'diff_hash': row[8]
                })

            return versions

        except Exception as e:
            logger.error(f"❌ Error getting version history: {e}")
            return []

    def _validate_metadata(self, metadata: ModelMetadata) -> Dict[str, Any]:
        """Valida metadatos del modelo."""
        errors = []

        if not metadata.model_id or len(metadata.model_id) < 3:
            errors.append("model_id must be at least 3 characters")

        if not metadata.name or len(metadata.name) < 1:
            errors.append("name is required")

        if not metadata.publisher_address or not metadata.publisher_address.startswith('0x'):
            errors.append("valid publisher_address is required")

        if metadata.architecture not in ['transformer', 'cnn', 'rnn', 'mlp', 'unknown']:
            errors.append("invalid architecture")

        return {'valid': len(errors) == 0, 'errors': errors}

    def _calculate_model_hash(self, weights: Dict[str, Any]) -> str:
        """Calcula hash del modelo basado en pesos."""
        try:
            # Serializar pesos para hashing
            weights_str = json.dumps(weights, sort_keys=True, default=str)
            return hashlib.sha256(weights_str.encode()).hexdigest()
        except Exception:
            return hashlib.sha256(str(weights).encode()).hexdigest()

    def _create_signature(self, message: str, private_key: str) -> str:
        """Crea firma criptográfica del mensaje."""
        from eth_account import Account
        message_hash = hashlib.sha256(message.encode()).digest()
        signed = Account.sign_message(message_hash, private_key)
        return signed.signature.hex()

    def _verify_signature(self, message: str, signature: str, address: str) -> bool:
        """Verifica firma criptográfica."""
        try:
            from eth_account import Account
            message_hash = hashlib.sha256(message.encode()).digest()
            recovered = Account.recover_message(message_hash, signature=signature)
            return recovered.lower() == address.lower()
        except Exception:
            return False

    def _increment_version(self, current_version: str, version_type: str) -> str:
        """Incrementa versión semántica."""
        parts = current_version.split('.')
        if len(parts) != 3:
            return '1.0.0'

        major, minor, patch = map(int, parts)

        if version_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif version_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"

    def _calculate_weight_diff(self, old_weights: Dict[str, Any], new_weights: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula diferencias entre pesos."""
        diff = {}
        all_keys = set(old_weights.keys()) | set(new_weights.keys())

        for key in all_keys:
            old_val = old_weights.get(key)
            new_val = new_weights.get(key)

            if old_val is None:
                diff[key] = {'type': 'added', 'value': new_val}
            elif new_val is None:
                diff[key] = {'type': 'removed'}
            elif str(old_val) != str(new_val):
                diff[key] = {'type': 'modified', 'old': old_val, 'new': new_val}

        return diff

    def _compress_diff(self, diff: Dict[str, Any]) -> bytes:
        """Comprime diferencias usando zlib."""
        diff_json = json.dumps(diff, default=str)
        return zlib.compress(diff_json.encode())

    async def _get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene modelo de la BD."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM models WHERE model_id = ?', (model_id,))
            row = await cursor.fetchone()

        if not row:
            return None

        return {
            'model_id': row[0], 'name': row[1], 'description': row[2], 'version': row[3],
            'publisher_address': row[4], 'status': row[5], 'architecture': row[6],
            'framework': row[7], 'dataset_info': json.loads(row[8]) if row[8] else {},
            'performance_metrics': json.loads(row[9]) if row[9] else {}, 'created_at': row[10],
            'updated_at': row[11], 'tags': json.loads(row[12]) if row[12] else [],
            'license': row[13], 'ipfs_cid': row[14], 'model_hash': row[15]
        }

    async def _get_latest_version(self, model_id: str, branch: str) -> Optional[Dict[str, Any]]:
        """Obtiene última versión de una rama."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM versions
                WHERE model_id = ? AND branch = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (model_id, branch))
            row = await cursor.fetchone()

        if not row:
            return None

        return {
            'version_id': row[0], 'model_id': row[1], 'version_tag': row[2],
            'parent_version': row[3], 'branch': row[4], 'commit_message': row[5],
            'author': row[6], 'timestamp': row[7], 'diff_hash': row[8]
        }

    async def _get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene versión específica."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM versions WHERE version_id = ?', (version_id,))
            row = await cursor.fetchone()

        if not row:
            return None

        return {
            'version_id': row[0], 'model_id': row[1], 'version_tag': row[2],
            'parent_version': row[3], 'branch': row[4], 'commit_message': row[5],
            'author': row[6], 'timestamp': row[7], 'diff_hash': row[8]
        }

    async def _get_weights_for_version(self, version_id: str) -> Dict[str, Any]:
        """Obtiene pesos para una versión (simulado - en producción vendría de IPFS/storage)."""
        # En implementación real, esto descargaría pesos desde IPFS o storage
        return {}


# Instancia global del registry
model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Obtiene instancia global del Model Registry."""
    return model_registry