#!/usr/bin/env python3
"""
Módulo de autenticación de dos factores (2FA) con TOTP
======================================================

Implementa autenticación de dos factores usando Time-based One-Time Password (TOTP)
según RFC 6238, incluyendo generación de códigos QR, verificación de códigos TOTP,
gestión de secrets, e integración con el sistema de autenticación existente.
"""

import base64
import hashlib
import hmac
import logging
import secrets
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import pyotp  # Necesita ser instalado: pip install pyotp
import qrcode  # Necesita ser instalado: pip install qrcode[pil]
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwoFactorAlgorithm(Enum):
    """Algoritmos soportados para TOTP"""
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA512 = "SHA512"

class TwoFactorStatus(Enum):
    """Estados posibles del 2FA para un usuario"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    PENDING_SETUP = "pending_setup"
    SUSPENDED = "suspended"

@dataclass
class TwoFactorSecret:
    """Secreto TOTP para un usuario"""
    user_id: str
    secret: str  # Base32 encoded secret
    algorithm: TwoFactorAlgorithm = TwoFactorAlgorithm.SHA256
    digits: int = 6
    interval: int = 30  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    backup_codes: List[str] = field(default_factory=list)
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el secreto a diccionario para almacenamiento"""
        return {
            'user_id': self.user_id,
            'secret': self.secret,
            'algorithm': self.algorithm.value,
            'digits': self.digits,
            'interval': self.interval,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'backup_codes': self.backup_codes,
            'failed_attempts': self.failed_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TwoFactorSecret':
        """Crea instancia desde diccionario"""
        return cls(
            user_id=data['user_id'],
            secret=data['secret'],
            algorithm=TwoFactorAlgorithm(data['algorithm']),
            digits=data.get('digits', 6),
            interval=data.get('interval', 30),
            created_at=datetime.fromisoformat(data['created_at']),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
            backup_codes=data.get('backup_codes', []),
            failed_attempts=data.get('failed_attempts', 0),
            locked_until=datetime.fromisoformat(data['locked_until']) if data.get('locked_until') else None,
        )

@dataclass
class TwoFactorSetup:
    """Información de configuración temporal para 2FA"""
    user_id: str
    secret: str
    qr_code_uri: str
    qr_code_data: bytes  # PNG image data
    expires_at: datetime
    verification_code: Optional[str] = None  # Para verificación inicial

class TwoFactorManager:
    """
    Gestor principal de autenticación de dos factores con TOTP
    """

    def __init__(self):
        # Almacenamiento en memoria - en producción usar base de datos
        self.secrets: Dict[str, TwoFactorSecret] = {}
        self.pending_setups: Dict[str, TwoFactorSetup] = {}

        # Configuración
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.setup_expiration = timedelta(minutes=15)
        self.backup_codes_count = 10

        logger.info("🔐 TwoFactorManager initialized")

    def generate_secret(self, user_id: str, algorithm: TwoFactorAlgorithm = TwoFactorAlgorithm.SHA256) -> str:
        """
        Genera un nuevo secreto TOTP para un usuario

        Args:
            user_id: ID del usuario
            algorithm: Algoritmo hash a usar

        Returns:
            Secreto en formato base32
        """
        # Generar 32 bytes aleatorios (256 bits)
        random_bytes = secrets.token_bytes(32)

        # Usar HKDF para derivar clave final
        hkdf = HKDF(
            algorithm={
                TwoFactorAlgorithm.SHA1: hashes.SHA1(),
                TwoFactorAlgorithm.SHA256: hashes.SHA256(),
                TwoFactorAlgorithm.SHA512: hashes.SHA512(),
            }[algorithm],
            length=32,
            salt=f"{user_id}:{int(time.time())}".encode(),
            info=b"TOTP-Secret-Derivation",
            backend=default_backend()
        )

        derived_key = hkdf.derive(random_bytes)

        # Convertir a base32 (formato estándar para TOTP)
        secret = base64.b32encode(derived_key).decode('ascii').rstrip('=')

        return secret

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Genera códigos de respaldo para recuperación

        Args:
            count: Número de códigos a generar

        Returns:
            Lista de códigos de respaldo
        """
        codes = []
        for _ in range(count):
            # Generar código de 8 caracteres alfanuméricos
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(code)
        return codes

    def create_qr_code_uri(self, user_id: str, secret: str, issuer: str = "AILOOS",
                          account_name: str = "", algorithm: TwoFactorAlgorithm = TwoFactorAlgorithm.SHA256,
                          digits: int = 6, interval: int = 30) -> str:
        """
        Crea URI para código QR según estándar otpauth

        Args:
            user_id: ID del usuario
            secret: Secreto TOTP
            issuer: Nombre del emisor (aplicación)
            account_name: Nombre de cuenta (opcional)
            algorithm: Algoritmo hash
            digits: Número de dígitos
            interval: Intervalo en segundos

        Returns:
            URI otpauth para generar QR
        """
        account = account_name or user_id

        # Construir URI según RFC 6238
        uri = f"otpauth://totp/{issuer}:{account}?secret={secret}&issuer={issuer}"

        if algorithm != TwoFactorAlgorithm.SHA1:
            uri += f"&algorithm={algorithm.value}"

        if digits != 6:
            uri += f"&digits={digits}"

        if interval != 30:
            uri += f"&period={interval}"

        return uri

    def generate_qr_code_image(self, uri: str) -> bytes:
        """
        Genera imagen PNG del código QR

        Args:
            uri: URI otpauth

        Returns:
            Datos binarios de la imagen PNG
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir a bytes
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def setup_two_factor(self, user_id: str, issuer: str = "AILOOS",
                         account_name: str = "", algorithm: TwoFactorAlgorithm = TwoFactorAlgorithm.SHA256,
                         digits: int = 6, interval: int = 30) -> TwoFactorSetup:
        """
        Inicia configuración de 2FA para un usuario

        Args:
            user_id: ID del usuario
            issuer: Nombre del emisor
            account_name: Nombre de cuenta
            algorithm: Algoritmo TOTP
            digits: Dígitos del código
            interval: Intervalo en segundos

        Returns:
            Objeto TwoFactorSetup con información de configuración
        """
        # Verificar que no tenga 2FA ya configurado
        if user_id in self.secrets:
            raise ValueError(f"User {user_id} already has 2FA configured")

        # Generar secreto
        secret = self.generate_secret(user_id, algorithm)

        # Crear URI para QR
        qr_uri = self.create_qr_code_uri(user_id, secret, issuer, account_name, algorithm, digits, interval)

        # Generar imagen QR
        qr_image = self.generate_qr_code_image(qr_uri)

        # Generar códigos de respaldo
        backup_codes = self.generate_backup_codes(self.backup_codes_count)

        # Crear objeto de configuración
        setup = TwoFactorSetup(
            user_id=user_id,
            secret=secret,
            qr_code_uri=qr_uri,
            qr_code_data=qr_image,
            expires_at=datetime.now() + self.setup_expiration,
            verification_code=None
        )

        # Almacenar configuración pendiente
        self.pending_setups[user_id] = setup

        logger.info(f"🔧 2FA setup initiated for user {user_id}")
        return setup

    def verify_setup_code(self, user_id: str, code: str) -> bool:
        """
        Verifica el código TOTP durante la configuración inicial

        Args:
            user_id: ID del usuario
            code: Código TOTP proporcionado

        Returns:
            True si el código es válido
        """
        setup = self.pending_setups.get(user_id)
        if not setup:
            return False

        # Verificar expiración
        if datetime.now() > setup.expires_at:
            del self.pending_setups[user_id]
            return False

        # Verificar código TOTP
        totp = pyotp.TOTP(setup.secret)
        if totp.verify(code):
            # Marcar como verificado
            setup.verification_code = code
            return True

        return False

    def complete_setup(self, user_id: str) -> TwoFactorSecret:
        """
        Completa la configuración de 2FA y crea el secreto permanente

        Args:
            user_id: ID del usuario

        Returns:
            TwoFactorSecret creado

        Raises:
            ValueError: Si la configuración no está verificada
        """
        setup = self.pending_setups.get(user_id)
        if not setup or not setup.verification_code:
            raise ValueError(f"Setup not verified for user {user_id}")

        # Crear secreto permanente
        secret_obj = TwoFactorSecret(
            user_id=user_id,
            secret=setup.secret,
            backup_codes=setup.backup_codes if hasattr(setup, 'backup_codes') else self.generate_backup_codes()
        )

        # Almacenar secreto
        self.secrets[user_id] = secret_obj

        # Limpiar configuración pendiente
        del self.pending_setups[user_id]

        logger.info(f"✅ 2FA setup completed for user {user_id}")
        return secret_obj

    def verify_totp_code(self, user_id: str, code: str) -> bool:
        """
        Verifica un código TOTP para un usuario

        Args:
            user_id: ID del usuario
            code: Código TOTP a verificar

        Returns:
            True si el código es válido
        """
        secret_obj = self.secrets.get(user_id)
        if not secret_obj:
            return False

        # Verificar si está bloqueado
        if secret_obj.locked_until and datetime.now() < secret_obj.locked_until:
            return False

        # Crear objeto TOTP
        totp = pyotp.TOTP(
            secret_obj.secret,
            digits=secret_obj.digits,
            interval=secret_obj.interval,
            digest={
                TwoFactorAlgorithm.SHA1: hashlib.sha1,
                TwoFactorAlgorithm.SHA256: hashlib.sha256,
                TwoFactorAlgorithm.SHA512: hashlib.sha512,
            }[secret_obj.algorithm]
        )

        # Verificar código
        if totp.verify(code):
            # Reset failed attempts y actualizar last_used
            secret_obj.failed_attempts = 0
            secret_obj.last_used = datetime.now()
            secret_obj.locked_until = None
            return True
        else:
            # Incrementar contador de fallos
            secret_obj.failed_attempts += 1

            # Bloquear si excede máximo
            if secret_obj.failed_attempts >= self.max_failed_attempts:
                secret_obj.locked_until = datetime.now() + self.lockout_duration
                logger.warning(f"🔒 User {user_id} locked out due to failed 2FA attempts")

            return False

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verifica un código de respaldo

        Args:
            user_id: ID del usuario
            code: Código de respaldo

        Returns:
            True si el código es válido y se consume
        """
        secret_obj = self.secrets.get(user_id)
        if not secret_obj:
            return False

        # Buscar código en lista
        if code in secret_obj.backup_codes:
            # Remover código usado
            secret_obj.backup_codes.remove(code)
            secret_obj.last_used = datetime.now()
            logger.info(f"🔑 Backup code used for user {user_id}")
            return True

        return False

    def get_two_factor_status(self, user_id: str) -> TwoFactorStatus:
        """
        Obtiene el estado actual del 2FA para un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Estado del 2FA
        """
        if user_id in self.pending_setups:
            return TwoFactorStatus.PENDING_SETUP
        elif user_id in self.secrets:
            secret_obj = self.secrets[user_id]
            if secret_obj.locked_until and datetime.now() < secret_obj.locked_until:
                return TwoFactorStatus.SUSPENDED
            else:
                return TwoFactorStatus.ENABLED
        else:
            return TwoFactorStatus.DISABLED

    def disable_two_factor(self, user_id: str) -> bool:
        """
        Deshabilita 2FA para un usuario

        Args:
            user_id: ID del usuario

        Returns:
            True si se deshabilitó correctamente
        """
        if user_id in self.secrets:
            del self.secrets[user_id]
            logger.info(f"🚫 2FA disabled for user {user_id}")
            return True

        # También limpiar configuraciones pendientes
        if user_id in self.pending_setups:
            del self.pending_setups[user_id]

        return False

    def regenerate_backup_codes(self, user_id: str) -> Optional[List[str]]:
        """
        Regenera códigos de respaldo para un usuario

        Args:
            user_id: ID del usuario

        Returns:
            Nuevos códigos de respaldo o None si no tiene 2FA
        """
        secret_obj = self.secrets.get(user_id)
        if not secret_obj:
            return None

        new_codes = self.generate_backup_codes(self.backup_codes_count)
        secret_obj.backup_codes = new_codes

        logger.info(f"🔄 Backup codes regenerated for user {user_id}")
        return new_codes

    def get_user_secret_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del secreto 2FA de un usuario (sin el secreto mismo)

        Args:
            user_id: ID del usuario

        Returns:
            Información del secreto o None
        """
        secret_obj = self.secrets.get(user_id)
        if not secret_obj:
            return None

        return {
            'user_id': secret_obj.user_id,
            'algorithm': secret_obj.algorithm.value,
            'digits': secret_obj.digits,
            'interval': secret_obj.interval,
            'created_at': secret_obj.created_at.isoformat(),
            'last_used': secret_obj.last_used.isoformat() if secret_obj.last_used else None,
            'backup_codes_count': len(secret_obj.backup_codes),
            'failed_attempts': secret_obj.failed_attempts,
            'locked_until': secret_obj.locked_until.isoformat() if secret_obj.locked_until else None,
        }

    def cleanup_expired_setups(self):
        """Limpia configuraciones pendientes expiradas"""
        current_time = datetime.now()
        expired = []

        for user_id, setup in self.pending_setups.items():
            if current_time > setup.expires_at:
                expired.append(user_id)

        for user_id in expired:
            del self.pending_setups[user_id]

        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired 2FA setups")

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema 2FA"""
        return {
            'total_users_with_2fa': len(self.secrets),
            'pending_setups': len(self.pending_setups),
            'locked_accounts': sum(1 for s in self.secrets.values()
                                 if s.locked_until and datetime.now() < s.locked_until),
            'total_backup_codes': sum(len(s.backup_codes) for s in self.secrets.values()),
        }


# Instancia global del gestor 2FA
two_factor_manager = TwoFactorManager()


def get_two_factor_manager() -> TwoFactorManager:
    """Obtiene la instancia global del gestor 2FA"""
    return two_factor_manager


# Integración con sistema de autenticación JWT
def create_two_factor_enhanced_token(user_id: str, permissions: list = None, two_factor_verified: bool = False) -> str:
    """
    Crea un token JWT con información de verificación 2FA

    Args:
        user_id: ID del usuario
        permissions: Lista de permisos
        two_factor_verified: Si el usuario ha completado verificación 2FA

    Returns:
        Token JWT con claims de 2FA
    """
    from ..coordinator.auth.jwt import create_access_token

    # Agregar claim de 2FA al token
    enhanced_permissions = permissions or ["user:read"]
    if two_factor_verified:
        enhanced_permissions.append("2fa:verified")

    return create_access_token(
        subject=user_id,
        token_type="user",
        permissions=enhanced_permissions
    )


def require_two_factor_for_login(user_id: str, password: str, db_session=None) -> dict:
    """
    Función de integración para login con 2FA

    Args:
        user_id: ID del usuario
        password: Contraseña (ya verificada)
        db_session: Sesión de base de datos

    Returns:
        Dict con resultado del login y estado 2FA
    """
    manager = get_two_factor_manager()

    # Verificar si usuario tiene 2FA habilitado
    status = manager.get_two_factor_status(user_id)

    if status == TwoFactorStatus.ENABLED:
        # Requiere código 2FA
        return {
            "requires_2fa": True,
            "user_id": user_id,
            "message": "Two-factor authentication required"
        }
    elif status == TwoFactorStatus.SUSPENDED:
        # Cuenta bloqueada por intentos fallidos
        return {
            "requires_2fa": False,
            "blocked": True,
            "message": "Account temporarily locked due to failed 2FA attempts"
        }
    else:
        # No tiene 2FA o está pendiente
        return {
            "requires_2fa": False,
            "user_id": user_id,
            "message": "Login successful"
        }


def complete_login_with_two_factor(user_id: str, two_factor_code: str, db_session=None) -> dict:
    """
    Completa el login verificando el código 2FA

    Args:
        user_id: ID del usuario
        two_factor_code: Código TOTP o de respaldo
        db_session: Sesión de base de datos

    Returns:
        Dict con resultado de la verificación
    """
    manager = get_two_factor_manager()

    # Verificar código 2FA
    if require_two_factor_verification(user_id, two_factor_code):
        # Crear token con 2FA verificado
        token = create_two_factor_enhanced_token(user_id, two_factor_verified=True)

        return {
            "success": True,
            "access_token": token,
            "message": "Login successful with 2FA verification"
        }
    else:
        return {
            "success": False,
            "message": "Invalid 2FA code"
        }

# Funciones de conveniencia para integración con autenticación
def require_two_factor_verification(user_id: str, code: str) -> bool:
    """
    Función de conveniencia para verificar 2FA durante login

    Args:
        user_id: ID del usuario
        code: Código TOTP o de respaldo

    Returns:
        True si la verificación es exitosa
    """
    manager = get_two_factor_manager()

    # Intentar verificar como TOTP primero
    if manager.verify_totp_code(user_id, code):
        return True

    # Si falla, intentar como código de respaldo
    if manager.verify_backup_code(user_id, code):
        return True

    return False


def is_two_factor_enabled(user_id: str) -> bool:
    """
    Verifica si un usuario tiene 2FA habilitado

    Args:
        user_id: ID del usuario

    Returns:
        True si tiene 2FA habilitado
    """
    manager = get_two_factor_manager()
    return manager.get_two_factor_status(user_id) == TwoFactorStatus.ENABLED


if __name__ == '__main__':
    # Demo del sistema 2FA
    print("🔐 Two-Factor Authentication (TOTP) Demo")
    print("=" * 50)

    manager = get_two_factor_manager()
    user_id = "demo_user"

    try:
        # 1. Iniciar configuración
        print("1. Iniciando configuración de 2FA...")
        setup = manager.setup_two_factor(user_id, issuer="AILOOS Demo", account_name="demo@example.com")

        print(f"   Secreto generado: {setup.secret}")
        print(f"   URI QR: {setup.qr_code_uri}")
        print("   (En aplicación real, mostrar QR code al usuario)")

        # 2. Simular verificación del código
        print("\n2. Generando código TOTP para verificación...")

        # Crear TOTP object para generar código de prueba
        totp = pyotp.TOTP(setup.secret)
        test_code = totp.now()

        print(f"   Código generado: {test_code}")

        # 3. Verificar código
        print("\n3. Verificando código...")
        if manager.verify_setup_code(user_id, test_code):
            print("   ✅ Código verificado correctamente")

            # 4. Completar configuración
            print("\n4. Completando configuración...")
            secret_obj = manager.complete_setup(user_id)
            print("   ✅ 2FA configurado exitosamente")
            print(f"   Códigos de respaldo generados: {len(secret_obj.backup_codes)}")

            # 5. Probar verificación normal
            print("\n5. Probando verificación normal...")
            new_code = totp.now()
            if manager.verify_totp_code(user_id, new_code):
                print("   ✅ Verificación TOTP exitosa")
            else:
                print("   ❌ Verificación TOTP fallida")

            # 6. Probar código de respaldo
            print("\n6. Probando código de respaldo...")
            if secret_obj.backup_codes:
                backup_code = secret_obj.backup_codes[0]
                if manager.verify_backup_code(user_id, backup_code):
                    print("   ✅ Código de respaldo verificado")
                else:
                    print("   ❌ Código de respaldo fallido")

        else:
            print("   ❌ Verificación del código fallida")

    except Exception as e:
        print(f"❌ Error en demo: {e}")

    # Mostrar estadísticas
    stats = manager.get_system_stats()
    print(f"\n📊 Estadísticas del sistema: {stats}")

    print("\n🎉 Demo completada!")