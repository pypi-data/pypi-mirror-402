#!/usr/bin/env python3
"""
AILOOS IPFS Connector - Conector Híbrido Inteligente
====================================================

Este módulo gestiona la conexión física con IPFS. Es "Híbrido" porque:
- Intenta usar un nodo local para máxima soberanía de datos
- Hace fallback automático a gateways públicos para operaciones de lectura
- Gestiona errores y reconexiones automáticamente
- Proporciona estadísticas detalladas de uso

Arquitectura:
- Nodo Local (lectura/escritura) → Máxima privacidad
- Gateway Público (solo lectura) → Fallback cuando no hay nodo local
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class IPFSConnector:
    """
    Conector híbrido inteligente para IPFS.
    Gestiona conexiones locales y gateways públicos.
    """

    def __init__(self,
                 local_api_url: str = "http://127.0.0.1:5001/api/v0",
                 public_gateways: List[str] = None,
                 enforce_tls: bool = True):
        """
        Inicializa el conector IPFS.

        Args:
            local_api_url: URL del API del nodo IPFS local
            public_gateways: Lista de gateways públicos para fallback
            enforce_tls: Forzar uso de HTTPS en todas las comunicaciones
        """
        self.local_api_url = local_api_url
        self.public_gateways = public_gateways or [
            "https://ipfs.io/ipfs/",
            "https://gateway.pinata.cloud/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/"
        ]
        self.enforce_tls = enforce_tls

        # Estado de conexión
        self.connected = False
        self.mode = "gateway_only"  # "full_node" o "gateway_only"

        # Estadísticas
        self.stats = {
            "uploads": 0,
            "downloads": 0,
            "errors": 0,
            "last_check": 0,
            "connected_peers": 0,
            "repo_size": 0
        }

        # Verificar que todos los gateways usen HTTPS si TLS está forzado
        if self.enforce_tls:
            self._validate_https_gateways()

        # Verificar conexión inicial
        self._check_connection()

    def _validate_https_gateways(self):
        """Valida que todos los gateways públicos usen HTTPS."""
        from urllib.parse import urlparse

        invalid_gateways = []
        for gateway in self.public_gateways:
            parsed = urlparse(gateway)
            if parsed.scheme != "https":
                invalid_gateways.append(gateway)

        if invalid_gateways:
            logger.warning(f"⚠️ Gateways no-HTTPS encontrados (serán forzados a HTTPS): {invalid_gateways}")
            # Forzar HTTPS en todos los gateways
            self.public_gateways = [gw.replace("http://", "https://") for gw in self.public_gateways]

    def _check_connection(self) -> bool:
        """Verifica el estado de conexión con IPFS."""
        try:
            # Intentar conexión local
            response = requests.post(
                f"{self.local_api_url}/id",
                timeout=5
            )

            if response.status_code == 200:
                self.connected = True
                self.mode = "full_node"
                logger.info("✅ Conectado a nodo IPFS local")

                # Obtener estadísticas del nodo
                self._update_node_stats()
                return True

        except (requests.RequestException, ConnectionError):
            if os.getenv('AILOOS_ENV') == 'production':
                logger.warning("⚠️ Nodo IPFS local no disponible, usando modo gateway")
            else:
                logger.info("ℹ️ Modo IPFS Gateway (nodo local no detectado)")

        # Fallback a modo gateway
        self.connected = True  # Gateways siempre están disponibles para lectura
        self.mode = "gateway_only"
        return True

    def _update_node_stats(self):
        """Actualiza estadísticas del nodo local."""
        try:
            # Obtener peers conectados
            response = requests.post(
                f"{self.local_api_url}/swarm/peers",
                timeout=5
            )
            if response.status_code == 200:
                peers_data = response.json()
                self.stats["connected_peers"] = len(peers_data.get("Peers", []))

            # Obtener tamaño del repositorio
            response = requests.post(
                f"{self.local_api_url}/repo/stat",
                timeout=5
            )
            if response.status_code == 200:
                repo_data = response.json()
                self.stats["repo_size"] = repo_data.get("RepoSize", 0)

        except Exception as e:
            logger.debug(f"Error obteniendo estadísticas del nodo: {e}")

    def add_json(self, data: Dict) -> Optional[str]:
        """
        Sube datos JSON a IPFS.

        Args:
            data: Datos a subir

        Returns:
            CID del contenido subido, o None si falla
        """
        if not self.connected:
            logger.error("❌ No hay conexión IPFS disponible")
            return None

        # Convertir a JSON string
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

        try:
            if self.mode == "full_node":
                # Usar nodo local para subida
                response = requests.post(
                    f"{self.local_api_url}/add",
                    files={"file": ("data.json", json_str, "application/json")},
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    cid = result.get("Hash")
                    self.stats["uploads"] += 1
                    logger.info(f"✅ Datos subidos a IPFS local: {cid}")
                    return cid

            # Si no hay nodo local o falló, no podemos subir
            logger.error("❌ No se puede subir datos sin nodo IPFS local")
            return None

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Error subiendo datos a IPFS: {e}")
            return None

    def get_json(self, cid: str) -> Optional[Dict]:
        """
        Descarga datos JSON desde IPFS.

        Args:
            cid: CID del contenido a descargar

        Returns:
            Datos descargados como dict, o None si falla
        """
        if not self.connected:
            logger.error("❌ No hay conexión IPFS disponible")
            return None

        # Intentar descarga desde diferentes fuentes
        sources = []

        if self.mode == "full_node":
            sources.append(("local", f"{self.local_api_url}/cat/{cid}"))

        # Añadir gateways públicos
        for gateway in self.public_gateways:
            sources.append(("gateway", urljoin(gateway, cid)))

        for source_name, url in sources:
            try:
                logger.debug(f"Intentando descarga desde {source_name}: {url}")

                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    self.stats["downloads"] += 1
                    logger.info(f"✅ Datos descargados desde {source_name}: {cid}")
                    return data

            except json.JSONDecodeError:
                logger.warning(f"Contenido de {source_name} no es JSON válido")
            except requests.RequestException as e:
                logger.debug(f"Error descargando desde {source_name}: {e}")
                continue

        self.stats["errors"] += 1
        logger.error(f"❌ No se pudo descargar {cid} desde ninguna fuente")
        return None

    def get_bytes(self, cid: str) -> Optional[bytes]:
        """
        Descarga datos binarios desde IPFS.

        Args:
            cid: CID del contenido a descargar

        Returns:
            Datos como bytes, o None si falla
        """
        if not self.connected:
            logger.error("❌ No hay conexión IPFS disponible")
            return None

        # Intentar descarga desde diferentes fuentes
        sources = []

        if self.mode == "full_node":
            sources.append(("local", f"{self.local_api_url}/cat/{cid}"))

        # Añadir gateways públicos
        for gateway in self.public_gateways:
            sources.append(("gateway", urljoin(gateway, cid)))

        for source_name, url in sources:
            try:
                logger.debug(f"Intentando descarga desde {source_name}: {url}")

                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    self.stats["downloads"] += 1
                    logger.info(f"✅ Datos binarios descargados desde {source_name}: {cid}")
                    return response.content

            except requests.RequestException as e:
                logger.debug(f"Error descargando desde {source_name}: {e}")
                continue

        self.stats["errors"] += 1
        logger.error(f"❌ No se pudo descargar {cid} desde ninguna fuente")
        return None

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del conector.

        Returns:
            Dict con estadísticas de uso
        """
        # Actualizar timestamp
        self.stats["last_check"] = time.time()

        # Verificar conexión actual
        self._check_connection()

        return {
            "connected": self.connected,
            "mode": self.mode,
            "uploads": self.stats["uploads"],
            "downloads": self.stats["downloads"],
            "errors": self.stats["errors"],
            "connected_peers": self.stats.get("connected_peers", 0),
            "repo_size": self.stats.get("repo_size", 0),
            "last_check": self.stats["last_check"]
        }

    def pin_cid(self, cid: str) -> bool:
        """
        Pin un CID para mantenerlo disponible localmente.

        Args:
            cid: CID a pinear

        Returns:
            True si se pudo pinear, False en caso contrario
        """
        if self.mode != "full_node":
            logger.warning("⚠️ Pinning solo disponible en modo nodo local")
            return False

        try:
            response = requests.post(
                f"{self.local_api_url}/pin/add/{cid}",
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"✅ CID pineado: {cid}")
                return True
            else:
                logger.error(f"❌ Error pineando CID: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error en pinning: {e}")
            return False

# Instancia global del conector
ipfs_connector = IPFSConnector()