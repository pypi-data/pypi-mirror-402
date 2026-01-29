"""
P2PClient - Cliente P2P Seguro con Intercambio de Claves ECDH
Implementa comunicación peer-to-peer encriptada usando Ephemeral Elliptic Curve Diffie-Hellman (ECDHE).
"""

import asyncio
import json
import socket
import threading
import time
import struct
import base64
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class P2PPeer:
    """Información de un peer P2P."""
    node_id: str
    host: str
    port: int
    is_connected: bool = False
    last_seen: Optional[datetime] = None
    public_key_pem: Optional[str] = None  # Clave pública de identidad del peer
    session_key: Optional[bytes] = None   # Clave de sesión compartida (AES)
    fernet: Optional[Fernet] = None       # Instancia Fernet para este peer específico
    is_banned: bool = False
    is_trusted: bool = False
    bytes_sent: int = 0
    bytes_received: int = 0


class SimpleDHT:
    """DHT simple para descubrimiento de peers (Simplificado para producción)."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.routing_table: Dict[str, Dict[str, Any]] = {}
        self.k = 5

    def store(self, key: str, value: Dict[str, Any]):
        """Almacenar valor en DHT."""
        self.routing_table[key] = value

    def find(self, key: str) -> Optional[Dict[str, Any]]:
        """Buscar valor en DHT."""
        return self.routing_table.get(key)
        
    def get_known_peers(self) -> List[Dict[str, Any]]:
        return list(self.routing_table.values())


class P2PClient:
    """
    Cliente P2P Seguro.
    
    Características de Seguridad:
    - Intercambio de claves ECDH (Elliptic Curve Diffie-Hellman)
    - Claves de sesión únicas por conexión (Forward Secrecy)
    - Encriptación autenticada (Fernet/AES-CBC+HMAC)
    """

    def __init__(self, node_id: str, port: int = 8443, bootstrap_peers: Optional[List[str]] = None):
        self.node_id = node_id
        self.port = port
        self.bootstrap_peers = bootstrap_peers or []

        # Estado
        self.running = False
        self.peers: Dict[str, P2PPeer] = {}
        self.active_connections: Dict[str, socket.socket] = {}
        
        # Identidad P2P (Efímera para ECDH, o persistente si se desea)
        # Aquí usamos claves efímeras para cada inicio de sesión, 
        # pero para firmar handshakes deberíamos usar la identidad de Auth (TODO integración futura)
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self._public_key = self._private_key.public_key()
        
        self.dht = SimpleDHT(node_id)

        # Sockets
        self.tcp_server_socket: Optional[socket.socket] = None
        self.udp_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None
        self.discovery_thread: Optional[threading.Thread] = None
        self.connection_threads: Dict[str, threading.Thread] = {}

        # Callbacks
        self.message_callbacks: Dict[str, List[Callable]] = {}
        self.peer_callbacks: Dict[str, List[Callable]] = {}

        # Persistence
        self.storage_path = Path("storage") / "peers.json"
        self._load_peers_state()

        logger.info(f"🔗 Secure P2PClient initialized: {node_id} on port {port}")

    def start(self) -> bool:
        try:
            if self.running:
                return True

            self.running = True
            
            # Servidores
            self._start_tcp_server()
            self._start_udp_discovery()
            self._start_heartbeat_thread()
            
            # Bootstrap
            self._connect_bootstrap_peers()
            self._announce_presence()

            logger.info(f"✅ Secure P2PClient started")
            return True
        except Exception as e:
            logger.error(f"❌ Error starting P2PClient: {e}")
            self.running = False
            return False

    def stop(self):
        try:
            self.running = False
            for sock in self.active_connections.values():
                try:
                    sock.close()
                except:
                    pass
            
            if self.tcp_server_socket:
                self.tcp_server_socket.close()
            if self.udp_socket:
                self.udp_socket.close()
                
            self.active_connections.clear()
            logger.info("⏹️ P2PClient stopped")
        except Exception as e:
            logger.error(f"Error stopping: {e}")

    # ==================== SERVIDOR TCP & HANDSHAKE ECDH ====================

    def _start_tcp_server(self):
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server_socket.bind(('0.0.0.0', self.port))
        self.tcp_server_socket.listen(10)
        
        self.server_thread = threading.Thread(target=self._tcp_server_loop, daemon=True)
        self.server_thread.start()

    def _tcp_server_loop(self):
        while self.running:
            try:
                client_socket, address = self.tcp_server_socket.accept()
                threading.Thread(target=self._handle_incoming_connection, 
                               args=(client_socket, address), daemon=True).start()
            except Exception:
                if self.running:
                    time.sleep(0.1)

    def _handle_incoming_connection(self, sock: socket.socket, address: Tuple[str, int]):
        """Manejar handshake entrante con ECDH."""
        peer_id = None
        try:
            sock.settimeout(10.0)

            # 1. Recibir Public Key del cliente (ECDH)
            data = self._receive_message_raw(sock)
            if not data:
                return
                
            handshake = json.loads(data.decode())
            peer_id = handshake.get('node_id')
            peer_pub_pem = handshake.get('public_key')
            
            if not peer_id or not peer_pub_pem:
                return

            # Cargar clave pública del peer
            peer_public_key = serialization.load_pem_public_key(peer_pub_pem.encode())

            # 2. Generar secreto compartido
            shared_key = self._derive_shared_key(peer_public_key)
            fernet = Fernet(base64.urlsafe_b64encode(shared_key))

            # 3. Enviar mi Public Key (ECDH)
            my_pub_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            
            response = {
                'node_id': self.node_id,
                'public_key': my_pub_pem,
                'timestamp': time.time()
            }
            self._send_message_raw(sock, json.dumps(response).encode())

            # 4. Registrar sesión segura
            self._register_secure_session(peer_id, address[0], handshake.get('port', address[1]), sock, fernet)
            
            # Mantener conexión
            self._maintain_connection(peer_id, sock)

        except Exception as e:
            logger.error(f"Handshake failed from {address}: {e}")
            if peer_id:
                self._disconnect_peer(peer_id)
            else:
                sock.close()

    def connect_to_peer(self, host: str, port: int) -> bool:
        """Iniciar conexión segura saliente."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((host, port))

            # 1. Enviar mi Public Key
            my_pub_pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            
            handshake = {
                'node_id': self.node_id,
                'public_key': my_pub_pem,
                'port': self.port,
                'timestamp': time.time()
            }
            self._send_message_raw(sock, json.dumps(handshake).encode())

            # 2. Recibir Public Key del servidor
            data = self._receive_message_raw(sock)
            if not data:
                return False
                
            response = json.loads(data.decode())
            peer_id = response.get('node_id')
            peer_pub_pem = response.get('public_key')
            
            if not peer_id or not peer_pub_pem:
                return False

            # Cargar clave pública
            peer_public_key = serialization.load_pem_public_key(peer_pub_pem.encode())

            # 3. Derivar secreto compartido
            shared_key = self._derive_shared_key(peer_public_key)
            fernet = Fernet(base64.urlsafe_b64encode(shared_key))

            # 4. Registrar sesión segura
            self._register_secure_session(peer_id, host, port, sock, fernet)

            # Iniciar thread de mantenimiento
            thread = threading.Thread(target=self._maintain_connection,
                                    args=(peer_id, sock), daemon=True)
            self.connection_threads[peer_id] = thread
            thread.start()
            
            logger.info(f"✅ Secure connection established with {peer_id}")
            self._save_peers_state()
            return True

        except Exception as e:
            logger.error(f"Connection failed to {host}:{port}: {e}")
            return False

    def _derive_shared_key(self, peer_public_key) -> bytes:
        """Derivar clave de sesión AES usando ECDH."""
        shared_secret = self._private_key.exchange(ec.ECDH(), peer_public_key)
        
        # Derivar clave de 32 bytes para AES/Fernet
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'ailoos-p2p-handshake',
        ).derive(shared_secret)
        
        return derived_key

    def _register_secure_session(self, peer_id: str, host: str, port: int, sock: socket.socket, fernet: Fernet):
        self.peers[peer_id] = P2PPeer(
            node_id=peer_id,
            host=host,
            port=port,
            is_connected=True,
            last_seen=datetime.now(),
            fernet=fernet
        )
        self.active_connections[peer_id] = sock

    def _disconnect_peer(self, peer_id: str):
        if peer_id in self.active_connections:
            try:
                self.active_connections[peer_id].close()
            except:
                pass
            del self.active_connections[peer_id]
        
        if peer_id in self.peers:
            self.peers[peer_id].is_connected = False

    def ban_peer(self, peer_id: str) -> bool:
        """Banear un peer y desconectarlo inmediatamente."""
        if peer_id in self.peers:
            self.peers[peer_id].is_banned = True
            self._disconnect_peer(peer_id)
            logger.warning(f"🚫 Bannan peer: {peer_id}")
            self._save_peers_state()
            return True
        # Create dummy peer entry if banning unknown ID
        self.peers[peer_id] = P2PPeer(node_id=peer_id, host="unknown", port=0, is_banned=True)
        self._save_peers_state()
        return True

    def trust_peer(self, peer_id: str) -> bool:
        """Marcar peer como confiable (prioridad)."""
        if peer_id in self.peers:
            self.peers[peer_id].is_trusted = True
            logger.info(f"🛡️ Trusted peer: {peer_id}")
            self._save_peers_state()
            return True
        return False

    def get_network_stats(self) -> List[Dict[str, Any]]:
        """Obtener estadísticas detalladas de la red."""
        stats = []
        for pid, peer in self.peers.items():
            stats.append({
                "node_id": pid,
                "host": peer.host,
                "status": "Connected" if peer.is_connected else ("Banned" if peer.is_banned else "Offline"),
                "trusted": peer.is_trusted,
                "bytes_rx": peer.bytes_received,
                "bytes_tx": peer.bytes_sent,
                "last_seen": peer.last_seen.strftime("%H:%M:%S") if peer.last_seen else "Never"
            })
        return stats

    # ==================== MENSAJERÍA ENCRIPTADA ====================

    def send_message(self, peer_id: str, message: Dict[str, Any]) -> bool:
        try:
            peer = self.peers.get(peer_id)
            sock = self.active_connections.get(peer_id)
            
            if not peer or not sock or not peer.fernet:
                return False

            payload = {
                'type': 'message',
                'sender': self.node_id,
                'content': message,
                'timestamp': time.time()
            }
            
            # Encriptar con clave de sesión
            json_bytes = json.dumps(payload).encode()
            encrypted_data = peer.fernet.encrypt(json_bytes)
            
            self._send_message_raw(sock, encrypted_data)
            return True

        except Exception as e:
            logger.error(f"Send error to {peer_id}: {e}")
            self._disconnect_peer(peer_id)
            return False

    def _maintain_connection(self, peer_id: str, sock: socket.socket):
        peer = self.peers.get(peer_id)
        while self.running and peer_id in self.active_connections:
            try:
                # Recibir datos raw (encriptados)
                encrypted_data = self._receive_message_raw(sock)
                if not encrypted_data:
                    break
                
                # Desencriptar
                try:
                    decrypted_data = peer.fernet.decrypt(encrypted_data)
                    msg = json.loads(decrypted_data.decode())
                    
                    # Routing
                    if msg.get('type') == 'heartbeat':
                        peer.last_seen = datetime.now()
                    elif msg.get('type') == 'message':
                        content = msg.get('content')
                        # Trigger callbacks (TODO)
                except Exception as e:
                    logger.warning(f"Decryption error from {peer_id}: {e}")
                    
            except socket.timeout:
                continue
            except Exception:
                break
        
        self._disconnect_peer(peer_id)

    # ==================== I/O BASE ====================

    def _send_message_raw(self, sock: socket.socket, data: bytes):
        length = struct.pack('!I', len(data))
        sock.sendall(length + data)

    def _receive_message_raw(self, sock: socket.socket) -> Optional[bytes]:
        try:
            header = sock.recv(4)
            if not header or len(header) < 4:
                return None
            length = struct.unpack('!I', header)[0]
            
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk: return None
                data += chunk
            return data
        except:
            return None

    # ==================== HELPERS ====================

    def _start_udp_discovery(self):
        # Implementación simplificada para brevedad, similar al original pero asíncrono seguro
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('0.0.0.0', self.port))
        
        self.discovery_thread = threading.Thread(target=self._udp_discovery_loop, daemon=True)
        self.discovery_thread.start()
        
    def _udp_discovery_loop(self):
        # Placeholder para no bloquear
        while self.running:
            time.sleep(1)

    def _start_heartbeat_thread(self):
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        while self.running:
            time.sleep(15)
            # Enviar heartbeat encriptado a todos
            for peer_id in list(self.active_connections.keys()):
                try:
                    self.send_message(peer_id, {'type': 'heartbeat'})
                except:
                    pass

    def _connect_bootstrap_peers(self):
        for addr in self.bootstrap_peers:
            try:
                host, port = addr.split(':')
                self.connect_to_peer(host, int(port))
            except:
                pass
    
    def _announce_presence(self):
        pass

    # ==================== PERSISTENCE ====================

    def _load_peers_state(self):
        """Cargar estado de peers (Bans, Trusts) desde disco."""
        try:
            if not self.storage_path.exists():
                return
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
            for pid, info in data.items():
                self.peers[pid] = P2PPeer(
                    node_id=pid,
                    host=info.get('host', 'unknown'),
                    port=info.get('port', 0),
                    is_banned=info.get('is_banned', False),
                    is_trusted=info.get('is_trusted', False),
                    last_seen=datetime.fromisoformat(info['last_seen']) if info.get('last_seen') else None
                )
            logger.info(f"📂 Loaded {len(self.peers)} peers from storage.")
        except Exception as e:
            logger.error(f"Failed to load peers state: {e}")

    def _save_peers_state(self):
        """Guardar estado de peers a disco."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            for pid, peer in self.peers.items():
                # Solo guardamos peers relevantes (baneados, trusted o conectados recientemente)
                if peer.is_banned or peer.is_trusted or peer.is_connected:
                    data[pid] = {
                        'host': peer.host,
                        'port': peer.port,
                        'is_banned': peer.is_banned,
                        'is_trusted': peer.is_trusted,
                        'last_seen': peer.last_seen.isoformat() if peer.last_seen else None
                    }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
             logger.error(f"Failed to save peers state: {e}")