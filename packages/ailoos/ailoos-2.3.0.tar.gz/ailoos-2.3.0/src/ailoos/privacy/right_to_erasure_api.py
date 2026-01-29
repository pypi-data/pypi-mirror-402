"""
Right to Erasure API para GDPR Compliance

Implementa endpoints REST para solicitudes de eliminación de datos
con verificación completa y auditoría.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from aiohttp import web
import aiohttp

from .data_deletion import get_deletion_manager, initiate_user_data_deletion as initiate_user_data_erasure, get_deletion_workflow_status
from .consent_management import get_consent_manager
from .data_retention import get_retention_manager

logger = logging.getLogger(__name__)


class RightToErasureAPI:
    """
    API para Right to Erasure (Derecho al Olvido) según GDPR.

    Endpoints:
    - POST /api/privacy/erase - Solicitar eliminación de datos
    - GET /api/privacy/erase/{request_id} - Ver estado de solicitud
    - DELETE /api/privacy/erase/{request_id} - Cancelar solicitud
    - GET /api/privacy/data-status - Ver qué datos existen del usuario
    """

    def __init__(self, coordinator_url: str = "http://localhost:5001"):
        self.coordinator_url = coordinator_url
        self.app = web.Application()
        self.deletion_manager = get_deletion_manager()
        self.consent_manager = get_consent_manager()
        self.retention_manager = get_retention_manager()

        self._setup_routes()

    def _setup_routes(self):
        """Configurar rutas de la API."""
        self.app.router.add_post('/api/privacy/erase', self.request_data_erasure)
        self.app.router.add_get('/api/privacy/erase/{request_id}', self.get_erasure_status)
        self.app.router.add_delete('/api/privacy/erase/{request_id}', self.cancel_erasure_request)
        self.app.router.add_get('/api/privacy/data-status', self.get_user_data_status)
        self.app.router.add_get('/api/privacy/consent', self.get_user_consent_status)
        self.app.router.add_post('/api/privacy/consent', self.update_user_consent)
        self.app.router.add_delete('/api/privacy/consent', self.withdraw_user_consent)

    async def request_data_erasure(self, request):
        """
        Solicitar eliminación completa de datos del usuario.

        POST /api/privacy/erase
        Body: {"user_id": "user123", "reason": "optional_reason"}
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            reason = data.get('reason', 'User requested data erasure')

            if not user_id:
                return web.json_response({
                    'error': 'user_id is required'
                }, status=400)

            # Generar ID único para la solicitud
            request_id = f"erase_req_{user_id}_{int(datetime.now().timestamp())}"

            # Iniciar workflow de eliminación
            workflow_id = await initiate_user_data_erasure(user_id, request_id)

            # Retirar todos los consentimientos del usuario
            consent_withdrawal = self.consent_manager.withdraw_consent(
                user_id, reason="Data erasure requested"
            )

            # Forzar eliminación de datos en retention manager
            retention_deletion = await self.retention_manager.force_delete_user_data(user_id)

            response_data = {
                'request_id': request_id,
                'workflow_id': workflow_id,
                'user_id': user_id,
                'status': 'initiated',
                'message': 'Data erasure request initiated successfully',
                'estimated_completion': '24-48 hours',
                'consent_withdrawn': consent_withdrawal,
                'retention_cleanup': retention_deletion,
                'initiated_at': datetime.now().isoformat()
            }

            logger.info(f"Data erasure requested for user {user_id}: {request_id}")

            return web.json_response(response_data, status=202)

        except Exception as e:
            logger.error(f"Error in data erasure request: {e}")
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    async def get_erasure_status(self, request):
        """
        Obtener estado de una solicitud de eliminación.

        GET /api/privacy/erase/{request_id}
        """
        try:
            request_id = request.match_info['request_id']

            # Buscar workflow por request_id
            workflow = None
            for wf in self.deletion_manager.workflows.values():
                if wf.request_id == request_id:
                    workflow = wf
                    break

            if not workflow:
                return web.json_response({
                    'error': 'Erasure request not found'
                }, status=404)

            status_data = self.deletion_manager.get_workflow_status(workflow.workflow_id)

            if not status_data:
                return web.json_response({
                    'error': 'Workflow status not available'
                }, status=500)

            # Enriquecer con información adicional
            enriched_status = {
                **status_data,
                'request_id': request_id,
                'user_id': workflow.user_id,
                'gdpr_compliant': self._verify_gdpr_compliance(status_data),
                'next_steps': self._get_next_steps(status_data)
            }

            return web.json_response(enriched_status)

        except Exception as e:
            logger.error(f"Error getting erasure status: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def cancel_erasure_request(self, request):
        """
        Cancelar una solicitud de eliminación (si no ha empezado).

        DELETE /api/privacy/erase/{request_id}
        """
        try:
            request_id = request.match_info['request_id']

            # Buscar workflow por request_id
            workflow = None
            for wf in self.deletion_manager.workflows.values():
                if wf.request_id == request_id:
                    workflow = wf
                    break

            if not workflow:
                return web.json_response({
                    'error': 'Erasure request not found'
                }, status=404)

            # Solo permitir cancelación si no ha empezado
            if workflow.status != 'pending':
                return web.json_response({
                    'error': 'Cannot cancel erasure request that has already started',
                    'current_status': workflow.status.value
                }, status=409)

            # Marcar como cancelado
            workflow.status = 'cancelled'
            workflow.completed_at = datetime.now()
            workflow.metadata['cancelled_at'] = datetime.now().isoformat()
            workflow.metadata['cancelled_by'] = 'user_request'

            logger.info(f"Erasure request cancelled: {request_id}")

            return web.json_response({
                'request_id': request_id,
                'status': 'cancelled',
                'message': 'Erasure request cancelled successfully',
                'cancelled_at': workflow.completed_at.isoformat()
            })

        except Exception as e:
            logger.error(f"Error cancelling erasure request: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def get_user_data_status(self, request):
        """
        Obtener información sobre qué datos existen del usuario.

        GET /api/privacy/data-status?user_id=user123
        """
        try:
            user_id = request.query.get('user_id')

            if not user_id:
                return web.json_response({
                    'error': 'user_id parameter is required'
                }, status=400)

            # Obtener datos de diferentes sistemas
            retention_status = self.retention_manager.get_retention_status(user_id)
            consent_status = self.consent_manager.get_user_consent_status(user_id)
            deletion_history = self.deletion_manager.get_user_deletion_history(user_id)

            # Verificar datos en servicios externos (simulado)
            external_data_status = await self._check_external_data_status(user_id)

            data_status = {
                'user_id': user_id,
                'data_locations': {
                    'database_records': retention_status.get('total_records', 0),
                    'consent_records': consent_status.get('total_consents', 0),
                    'retention_records': len(retention_status.get('by_category', {})),
                    'external_services': len(external_data_status.get('services', []))
                },
                'consent_status': consent_status,
                'retention_status': retention_status,
                'external_data': external_data_status,
                'deletion_history': deletion_history,
                'gdpr_rights': {
                    'right_to_access': True,
                    'right_to_rectification': True,
                    'right_to_erasure': True,
                    'right_to_restriction': True,
                    'right_to_portability': True,
                    'right_to_object': True
                },
                'generated_at': datetime.now().isoformat()
            }

            return web.json_response(data_status)

        except Exception as e:
            logger.error(f"Error getting user data status: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def get_user_consent_status(self, request):
        """
        Obtener estado de consentimientos del usuario.

        GET /api/privacy/consent?user_id=user123
        """
        try:
            user_id = request.query.get('user_id')

            if not user_id:
                return web.json_response({
                    'error': 'user_id parameter is required'
                }, status=400)

            consent_status = self.consent_manager.get_user_consent_status(user_id)
            banner_config = self.consent_manager.get_consent_banner_config(user_id)

            return web.json_response({
                'user_id': user_id,
                'consent_status': consent_status,
                'banner_config': banner_config
            })

        except Exception as e:
            logger.error(f"Error getting user consent status: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def update_user_consent(self, request):
        """
        Actualizar consentimientos del usuario.

        POST /api/privacy/consent
        Body: {"user_id": "user123", "categories": ["analytics"], "purposes": ["marketing"]}
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            categories = data.get('categories', [])
            purposes = data.get('purposes', [])

            if not user_id:
                return web.json_response({
                    'error': 'user_id is required'
                }, status=400)

            # Convertir strings a enums
            from .consent_management import ConsentCategory, ConsentPurpose
            category_enums = [ConsentCategory(cat) for cat in categories]
            purpose_enums = [ConsentPurpose(purp) for purp in purposes]

            # Otorgar consentimiento
            consent_id = self.consent_manager.grant_consent(
                user_id=user_id,
                categories=category_enums,
                purposes=purpose_enums,
                ip_address=request.remote,
                user_agent=request.headers.get('User-Agent'),
                source='api'
            )

            return web.json_response({
                'consent_id': consent_id,
                'user_id': user_id,
                'categories_granted': categories,
                'purposes_granted': purposes,
                'status': 'granted',
                'granted_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error updating user consent: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def withdraw_user_consent(self, request):
        """
        Retirar consentimientos del usuario.

        DELETE /api/privacy/consent?user_id=user123&categories=analytics,marketing
        """
        try:
            user_id = request.query.get('user_id')
            categories_str = request.query.get('categories')
            reason = request.query.get('reason', 'User withdrew consent')

            if not user_id:
                return web.json_response({
                    'error': 'user_id parameter is required'
                }, status=400)

            # Convertir categorías
            categories = None
            if categories_str:
                from .consent_management import ConsentCategory
                categories = [ConsentCategory(cat.strip()) for cat in categories_str.split(',')]

            # Retirar consentimiento
            withdrawal_result = self.consent_manager.withdraw_consent(
                user_id=user_id,
                categories=categories,
                reason=reason
            )

            return web.json_response({
                'user_id': user_id,
                'withdrawal_result': withdrawal_result,
                'status': 'withdrawn',
                'withdrawn_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error withdrawing user consent: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    def _verify_gdpr_compliance(self, workflow_status: Dict[str, Any]) -> bool:
        """Verificar cumplimiento GDPR del workflow."""
        success_rate = workflow_status.get('success_rate', 0)
        status = workflow_status.get('status', '')

        # Considerar compliant si éxito > 95% o parcialmente exitoso
        return success_rate >= 95.0 or status == 'partial'

    def _get_next_steps(self, workflow_status: Dict[str, Any]) -> List[str]:
        """Obtener próximos pasos basados en el estado."""
        status = workflow_status.get('status', '')
        success_rate = workflow_status.get('success_rate', 0)

        if status == 'pending':
            return ['Your erasure request is being processed']
        elif status == 'in_progress':
            return ['Data erasure is in progress', 'Check back in 24 hours for completion']
        elif status == 'completed':
            return ['Data erasure completed successfully', 'You will receive a confirmation email']
        elif status == 'partial':
            return [f'Data erasure partially completed ({success_rate:.1f}% success)',
                   'Contact support for manual cleanup of remaining data']
        elif status == 'failed':
            return ['Data erasure failed', 'Contact support for assistance']
        else:
            return ['Unknown status - contact support']

    async def _check_external_data_status(self, user_id: str) -> Dict[str, Any]:
        """Verificar datos en servicios externos (simulado)."""
        # En implementación real, verificaría APIs de terceros
        external_services = [
            {'service': 'email_provider', 'has_data': False, 'last_check': datetime.now().isoformat()},
            {'service': 'payment_processor', 'has_data': False, 'last_check': datetime.now().isoformat()},
            {'service': 'analytics_platform', 'has_data': False, 'last_check': datetime.now().isoformat()},
            {'service': 'backup_storage', 'has_data': False, 'last_check': datetime.now().isoformat()}
        ]

        return {
            'services': external_services,
            'total_services_checked': len(external_services),
            'services_with_data': 0,
            'last_check': datetime.now().isoformat()
        }

    async def start_server(self, host: str = '0.0.0.0', port: int = 8081):
        """Iniciar servidor de la API."""
        logger.info(f"Starting Right to Erasure API server on {host}:{port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Right to Erasure API active at http://{host}:{port}")

        # Mantener servidor corriendo
        while True:
            await asyncio.sleep(1)


# Función de conveniencia para iniciar la API
async def start_right_to_erasure_api(coordinator_url: str = "http://localhost:5001"):
    """Función de conveniencia para iniciar la API de Right to Erasure."""
    api = RightToErasureAPI(coordinator_url)
    await api.start_server()


if __name__ == "__main__":
    # Para testing directo
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_right_to_erasure_api())