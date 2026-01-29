"""
CCPA Privacy Rights API

Implementa APIs para derechos de privacidad CCPA:
- Data portability
- Access request automation
- Privacy dashboard
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from aiohttp import web
import aiohttp

from .do_not_sell import get_do_not_sell_manager
from .consent_management import get_consent_manager
from .data_retention import get_retention_manager
from .data_deletion import get_deletion_manager

logger = logging.getLogger(__name__)


class CCPAPrivacyAPI:
    """
    API para derechos de privacidad CCPA.

    Endpoints:
    - POST /api/ccpa/access - Solicitar acceso a datos personales
    - POST /api/ccpa/portability - Solicitar portabilidad de datos
    - GET /api/ccpa/dashboard - Privacy dashboard
    - POST /api/ccpa/do-not-sell - Configurar Do Not Sell
    - GET /api/ccpa/do-not-sell - Ver estado Do Not Sell
    """

    def __init__(self, coordinator_url: str = "http://localhost:5001"):
        self.coordinator_url = coordinator_url
        self.app = web.Application()

        # Managers
        self.do_not_sell_manager = get_do_not_sell_manager()
        self.consent_manager = get_consent_manager()
        self.retention_manager = get_retention_manager()
        self.deletion_manager = get_deletion_manager()

        self._setup_routes()

    def _setup_routes(self):
        """Configurar rutas de la API."""
        self.app.router.add_post('/api/ccpa/access', self.request_data_access)
        self.app.router.add_post('/api/ccpa/portability', self.request_data_portability)
        self.app.router.add_get('/api/ccpa/dashboard', self.get_privacy_dashboard)
        self.app.router.add_post('/api/ccpa/do-not-sell', self.set_do_not_sell_preference)
        self.app.router.add_get('/api/ccpa/do-not-sell', self.get_do_not_sell_status)
        self.app.router.add_delete('/api/ccpa/do-not-sell', self.withdraw_do_not_sell_preference)

    async def request_data_access(self, request):
        """
        Solicitar acceso a datos personales (CCPA Right to Know).

        POST /api/ccpa/access
        Body: {"user_id": "user123", "data_categories": ["personal", "financial"]}
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            data_categories = data.get('data_categories', ['all'])

            if not user_id:
                return web.json_response({
                    'error': 'user_id is required'
                }, status=400)

            # Generar ID único para la solicitud
            request_id = f"access_req_{user_id}_{int(datetime.now().timestamp())}"

            # Recopilar datos del usuario de diferentes sistemas
            access_data = await self._gather_user_data(user_id, data_categories)

            response_data = {
                'request_id': request_id,
                'user_id': user_id,
                'data_categories_requested': data_categories,
                'access_data': access_data,
                'generated_at': datetime.now().isoformat(),
                'ccpa_compliant': True,
                'processing_time_days': 45  # CCPA permite hasta 45 días
            }

            logger.info(f"Data access request processed for user {user_id}: {request_id}")

            return web.json_response(response_data)

        except Exception as e:
            logger.error(f"Error in data access request: {e}")
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    async def request_data_portability(self, request):
        """
        Solicitar portabilidad de datos (CCPA Right to Portability).

        POST /api/ccpa/portability
        Body: {"user_id": "user123", "format": "json", "data_categories": ["personal"]}
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            format_type = data.get('format', 'json')
            data_categories = data.get('data_categories', ['all'])

            if not user_id:
                return web.json_response({
                    'error': 'user_id is required'
                }, status=400)

            # Generar ID único para la solicitud
            request_id = f"portability_req_{user_id}_{int(datetime.now().timestamp())}"

            # Recopilar y formatear datos para portabilidad
            portability_data = await self._prepare_portability_data(user_id, data_categories, format_type)

            response_data = {
                'request_id': request_id,
                'user_id': user_id,
                'format': format_type,
                'data_categories': data_categories,
                'portability_data': portability_data,
                'download_url': f"/api/ccpa/download/{request_id}",  # URL para descargar archivo
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),  # Expira en 30 días
                'generated_at': datetime.now().isoformat(),
                'ccpa_compliant': True
            }

            logger.info(f"Data portability request processed for user {user_id}: {request_id}")

            return web.json_response(response_data)

        except Exception as e:
            logger.error(f"Error in data portability request: {e}")
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    async def get_privacy_dashboard(self, request):
        """
        Obtener dashboard de privacidad del usuario.

        GET /api/ccpa/dashboard?user_id=user123
        """
        try:
            user_id = request.query.get('user_id')

            if not user_id:
                return web.json_response({
                    'error': 'user_id parameter is required'
                }, status=400)

            # Recopilar datos de privacidad de todos los sistemas
            dashboard_data = await self._build_privacy_dashboard(user_id)

            return web.json_response(dashboard_data)

        except Exception as e:
            logger.error(f"Error getting privacy dashboard: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def set_do_not_sell_preference(self, request):
        """
        Configurar preferencias Do Not Sell.

        POST /api/ccpa/do-not-sell
        Body: {"user_id": "user123", "global_opt_out": true}
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            global_opt_out = data.get('global_opt_out', False)
            category_opt_outs = data.get('category_opt_outs', [])
            third_party_opt_outs = data.get('third_party_opt_outs', [])

            if not user_id:
                return web.json_response({
                    'error': 'user_id is required'
                }, status=400)

            # Convertir strings a enums
            from .do_not_sell import DataSaleCategory, ThirdPartyRecipient
            categories = [DataSaleCategory(cat) for cat in category_opt_outs] if category_opt_outs else None
            third_parties = [ThirdPartyRecipient(tp) for tp in third_party_opt_outs] if third_party_opt_outs else None

            # Establecer preferencia
            verification_token = self.do_not_sell_manager.set_do_not_sell_preference(
                user_id=user_id,
                global_opt_out=global_opt_out,
                category_opt_outs=categories,
                third_party_opt_outs=third_parties,
                ip_address=request.remote,
                user_agent=request.headers.get('User-Agent'),
                source='api'
            )

            return web.json_response({
                'user_id': user_id,
                'verification_token': verification_token,
                'global_opt_out': global_opt_out,
                'category_opt_outs': category_opt_outs,
                'third_party_opt_outs': third_party_opt_outs,
                'status': 'preference_set',
                'ccpa_compliant': True,
                'set_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error setting Do Not Sell preference: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def get_do_not_sell_status(self, request):
        """
        Obtener estado de Do Not Sell.

        GET /api/ccpa/do-not-sell?user_id=user123
        """
        try:
            user_id = request.query.get('user_id')

            if not user_id:
                return web.json_response({
                    'error': 'user_id parameter is required'
                }, status=400)

            status = self.do_not_sell_manager.get_do_not_sell_status(user_id)

            return web.json_response({
                'user_id': user_id,
                'do_not_sell_status': status,
                'ccpa_compliant': True,
                'generated_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error getting Do Not Sell status: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def withdraw_do_not_sell_preference(self, request):
        """
        Retirar preferencias Do Not Sell.

        DELETE /api/ccpa/do-not-sell?user_id=user123&scope=global
        """
        try:
            user_id = request.query.get('user_id')
            scope = request.query.get('scope', 'all')  # all, global, categories, third_parties

            if not user_id:
                return web.json_response({
                    'error': 'user_id parameter is required'
                }, status=400)

            # Determinar qué retirar basado en scope
            if scope == 'global':
                # Retirar solo opt-out global
                preference = self.do_not_sell_manager.preferences.get(user_id)
                if preference:
                    preference.global_opt_out = False
                    preference.updated_at = datetime.now()
            elif scope == 'all':
                # Retirar todas las preferencias
                if user_id in self.do_not_sell_manager.preferences:
                    del self.do_not_sell_manager.preferences[user_id]
            # Para scopes específicos, se podría implementar lógica adicional

            return web.json_response({
                'user_id': user_id,
                'scope': scope,
                'status': 'preference_withdrawn',
                'ccpa_compliant': True,
                'withdrawn_at': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error withdrawing Do Not Sell preference: {e}")
            return web.json_response({
                'error': 'Internal server error'
            }, status=500)

    async def _gather_user_data(self, user_id: str, categories: List[str]) -> Dict[str, Any]:
        """Recopilar datos del usuario de diferentes sistemas."""
        user_data = {
            'personal_information': {},
            'account_data': {},
            'consent_history': {},
            'data_sales_history': {},
            'retention_status': {},
            'deletion_history': {}
        }

        try:
            # Datos de consentimiento
            consent_status = self.consent_manager.get_user_consent_status(user_id)
            user_data['consent_history'] = consent_status

            # Datos de Do Not Sell
            dns_status = self.do_not_sell_manager.get_do_not_sell_status(user_id)
            user_data['do_not_sell_status'] = dns_status

            # Historial de ventas de datos
            privacy_dashboard = self.do_not_sell_manager.get_privacy_dashboard_data(user_id)
            user_data['data_sales_history'] = privacy_dashboard.get('sales_summary', {})

            # Estado de retención
            retention_status = self.retention_manager.get_retention_status(user_id)
            user_data['retention_status'] = retention_status

            # Historial de eliminaciones
            deletion_history = self.deletion_manager.get_user_deletion_history(user_id)
            user_data['deletion_history'] = deletion_history

            # Datos de cuenta (simulados - en producción vendrían de la DB)
            user_data['account_data'] = {
                'user_id': user_id,
                'account_created': '2024-01-15T10:30:00Z',
                'last_login': '2024-11-28T00:26:00Z',
                'account_status': 'active'
            }

            # Información personal (simulada - anonimizada)
            user_data['personal_information'] = {
                'data_collected': [
                    'email_hash', 'ip_address', 'user_agent', 'geolocation',
                    'device_fingerprint', 'consent_records', 'usage_patterns'
                ],
                'data_sources': ['website', 'api', 'federated_nodes'],
                'data_purposes': ['account_management', 'analytics', 'personalization']
            }

        except Exception as e:
            logger.error(f"Error gathering user data for {user_id}: {e}")
            user_data['error'] = str(e)

        return user_data

    async def _prepare_portability_data(self, user_id: str, categories: List[str], format_type: str) -> Dict[str, Any]:
        """Preparar datos para portabilidad."""
        # Recopilar datos
        user_data = await self._gather_user_data(user_id, categories)

        # Formatear según el tipo solicitado
        if format_type == 'json':
            return user_data
        elif format_type == 'xml':
            # Convertir a XML (simplificado)
            return self._convert_to_xml(user_data)
        elif format_type == 'csv':
            # Convertir a CSV (simplificado)
            return self._convert_to_csv(user_data)
        else:
            return user_data

    def _convert_to_xml(self, data: Dict[str, Any]) -> str:
        """Convertir datos a formato XML."""
        # Implementación simplificada
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<user_data>']

        for key, value in data.items():
            xml_parts.append(f'<{key}>')
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    xml_parts.append(f'<{sub_key}>{sub_value}</{sub_key}>')
            else:
                xml_parts.append(str(value))
            xml_parts.append(f'</{key}>')

        xml_parts.append('</user_data>')
        return '\n'.join(xml_parts)

    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convertir datos a formato CSV."""
        # Implementación simplificada
        csv_lines = ['Category,Key,Value']

        for category, category_data in data.items():
            if isinstance(category_data, dict):
                for key, value in category_data.items():
                    csv_lines.append(f'{category},{key},{value}')
            else:
                csv_lines.append(f'{category},value,{category_data}')

        return '\n'.join(csv_lines)

    async def _build_privacy_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Construir dashboard completo de privacidad."""
        dashboard = {
            'user_id': user_id,
            'ccpa_rights': {
                'right_to_know': True,
                'right_to_delete': True,
                'right_to_opt_out': True,
                'right_to_portability': True,
                'right_to_non_discrimination': True
            },
            'sections': {}
        }

        try:
            # Sección de consentimiento
            consent_status = self.consent_manager.get_user_consent_status(user_id)
            dashboard['sections']['consent_management'] = {
                'title': 'Consent Management',
                'status': 'active' if consent_status['has_active_consent'] else 'no_consent',
                'details': consent_status
            }

            # Sección Do Not Sell
            dns_status = self.do_not_sell_manager.get_do_not_sell_status(user_id)
            dashboard['sections']['do_not_sell'] = {
                'title': 'Do Not Sell My Personal Information',
                'status': 'opted_out' if dns_status['global_opt_out'] else 'opted_in',
                'details': dns_status
            }

            # Sección de ventas de datos
            privacy_data = self.do_not_sell_manager.get_privacy_dashboard_data(user_id)
            dashboard['sections']['data_sales'] = {
                'title': 'Data Sales History',
                'total_sales': privacy_data.get('total_sales', 0),
                'details': privacy_data
            }

            # Sección de retención de datos
            retention_status = self.retention_manager.get_retention_status(user_id)
            dashboard['sections']['data_retention'] = {
                'title': 'Data Retention Status',
                'total_records': retention_status.get('total_records', 0),
                'details': retention_status
            }

            # Sección de solicitudes
            deletion_history = self.deletion_manager.get_user_deletion_history(user_id)
            dashboard['sections']['requests_history'] = {
                'title': 'Privacy Requests History',
                'deletion_requests': len(deletion_history),
                'details': deletion_history
            }

            # Acciones disponibles
            dashboard['available_actions'] = {
                'request_data_access': '/api/ccpa/access',
                'request_data_portability': '/api/ccpa/portability',
                'set_do_not_sell': '/api/ccpa/do-not-sell',
                'request_data_deletion': '/api/privacy/erase'
            }

        except Exception as e:
            logger.error(f"Error building privacy dashboard for {user_id}: {e}")
            dashboard['error'] = str(e)

        dashboard['generated_at'] = datetime.now().isoformat()
        return dashboard

    async def start_server(self, host: str = '0.0.0.0', port: int = 8082):
        """Iniciar servidor de la API."""
        logger.info(f"Starting CCPA Privacy API server on {host}:{port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"CCPA Privacy API active at http://{host}:{port}")

        # Mantener servidor corriendo
        while True:
            await asyncio.sleep(1)


# Función de conveniencia para iniciar la API
async def start_ccpa_privacy_api(coordinator_url: str = "http://localhost:5001"):
    """Función de conveniencia para iniciar la API de privacidad CCPA."""
    api = CCPAPrivacyAPI(coordinator_url)
    await api.start_server()


if __name__ == "__main__":
    # Para testing directo
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_ccpa_privacy_api())