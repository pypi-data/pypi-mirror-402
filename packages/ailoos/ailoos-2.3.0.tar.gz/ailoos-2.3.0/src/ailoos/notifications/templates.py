"""
Plantillas de notificación reutilizables para AILOOS
==================================================

Este módulo proporciona plantillas predefinidas para diferentes tipos
de notificaciones del sistema.
"""

from typing import Dict, Any, List
from .models import NotificationTemplate, NotificationType


class NotificationTemplates:
    """Gestor de plantillas de notificación."""

    def __init__(self):
        self._templates: Dict[str, NotificationTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Carga las plantillas por defecto del sistema."""

        # Plantilla: Bienvenida
        self._templates['welcome'] = NotificationTemplate(
            name='welcome',
            type=NotificationType.BOTH,
            subject='¡Bienvenido a AILOOS!',
            title='¡Bienvenido a AILOOS!',
            body='Hola {user_name}, ¡bienvenido a AILOOS! Tu cuenta ha sido creada exitosamente.',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #2563eb;">¡Bienvenido a AILOOS!</h1>
                <p>Hola <strong>{user_name}</strong>,</p>
                <p>¡Bienvenido a AILOOS! Tu cuenta ha sido creada exitosamente.</p>
                <p>Estamos emocionados de tenerte con nosotros. Puedes comenzar explorando todas las funcionalidades que tenemos para ofrecerte.</p>
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>¿Qué puedes hacer ahora?</h3>
                    <ul>
                        <li>Configurar tus preferencias de notificación</li>
                        <li>Explorar el marketplace de datos</li>
                        <li>Unirte a sesiones de entrenamiento federado</li>
                        <li>Personalizar tu experiencia</li>
                    </ul>
                </div>
                <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
                <p>¡Que disfrutes tu experiencia en AILOOS!</p>
                <p style="color: #6b7280; font-size: 14px;">Equipo de AILOOS</p>
            </div>
            ''',
            variables=['user_name']
        )

        # Plantilla: Nueva respuesta del asistente
        self._templates['response_ready'] = NotificationTemplate(
            name='response_ready',
            type=NotificationType.BOTH,
            subject='Nueva respuesta disponible',
            title='Nueva respuesta disponible',
            body='Tu consulta "{query_preview}" ha sido procesada. Tienes una nueva respuesta esperando.',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Nueva respuesta disponible</h2>
                <p>Tu consulta <strong>"{query_preview}"</strong> ha sido procesada.</p>
                <p>Tienes una nueva respuesta esperando en tu conversación.</p>
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Consulta:</strong> {query_preview}</p>
                    <p><strong>Procesada en:</strong> {processing_time}</p>
                </div>
                <a href="{conversation_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Ver respuesta</a>
            </div>
            ''',
            variables=['query_preview', 'processing_time', 'conversation_url']
        )

        # Plantilla: Tarea completada
        self._templates['task_completed'] = NotificationTemplate(
            name='task_completed',
            type=NotificationType.BOTH,
            subject='Tarea completada: {task_name}',
            title='Tarea completada',
            body='La tarea "{task_name}" ha sido completada exitosamente.',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #059669;">✅ Tarea completada</h2>
                <p>La tarea <strong>"{task_name}"</strong> ha sido completada exitosamente.</p>
                <div style="background-color: #f0fdf4; border-left: 4px solid #059669; padding: 15px; margin: 20px 0;">
                    <p><strong>Detalles:</strong></p>
                    <ul>
                        <li><strong>Tarea:</strong> {task_name}</li>
                        <li><strong>Completada en:</strong> {completion_time}</li>
                        <li><strong>Estado:</strong> Exitosa</li>
                    </ul>
                </div>
                {next_steps}
            </div>
            ''',
            variables=['task_name', 'completion_time', 'next_steps']
        )

        # Plantilla: Sesión federada disponible
        self._templates['federated_session_available'] = NotificationTemplate(
            name='federated_session_available',
            type=NotificationType.BOTH,
            subject='Nueva sesión federada disponible',
            title='Nueva sesión federada disponible',
            body='Una nueva sesión de entrenamiento federado "{session_name}" está disponible para unirse.',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #7c3aed;">🔗 Nueva sesión federada disponible</h2>
                <p>Una nueva sesión de entrenamiento federado está disponible para unirse.</p>
                <div style="background-color: #faf5ff; border-left: 4px solid #7c3aed; padding: 15px; margin: 20px 0;">
                    <h3>{session_name}</h3>
                    <p><strong>Descripción:</strong> {session_description}</p>
                    <p><strong>Inicia:</strong> {start_time}</p>
                    <p><strong>Participantes:</strong> {participant_count}/{max_participants}</p>
                    <p><strong>Recompensa:</strong> {reward_amount} tokens</p>
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{join_url}" style="background-color: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-right: 10px;">Unirse ahora</a>
                    <a href="{details_url}" style="background-color: #e5e7eb; color: #374151; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Ver detalles</a>
                </div>
            </div>
            ''',
            variables=['session_name', 'session_description', 'start_time', 'participant_count', 'max_participants', 'reward_amount', 'join_url', 'details_url']
        )

        # Plantilla: Alerta de seguridad
        self._templates['security_alert'] = NotificationTemplate(
            name='security_alert',
            type=NotificationType.BOTH,
            subject='Alerta de seguridad - {alert_type}',
            title='Alerta de seguridad',
            body='Se ha detectado una actividad inusual en tu cuenta: {alert_description}',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #dc2626;">🚨 Alerta de seguridad</h2>
                <p>Se ha detectado una actividad inusual en tu cuenta.</p>
                <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                    <h3>{alert_type}</h3>
                    <p>{alert_description}</p>
                    <p><strong>Hora:</strong> {alert_time}</p>
                    <p><strong>IP:</strong> {alert_ip}</p>
                </div>
                <div style="background-color: #fffbeb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4>¿Fue tú?</h4>
                    <p>Si reconoces esta actividad, puedes ignorar esta alerta.</p>
                    <p>Si no reconoces esta actividad, te recomendamos:</p>
                    <ul>
                        <li>Cambiar tu contraseña inmediatamente</li>
                        <li>Revisar los dispositivos conectados</li>
                        <li>Contactar al soporte si tienes dudas</li>
                    </ul>
                </div>
                <a href="{security_settings_url}" style="background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Revisar seguridad</a>
            </div>
            ''',
            variables=['alert_type', 'alert_description', 'alert_time', 'alert_ip', 'security_settings_url']
        )

        # Plantilla: Recomendación personalizada
        self._templates['personalized_recommendation'] = NotificationTemplate(
            name='personalized_recommendation',
            type=NotificationType.BOTH,
            subject='Recomendación personalizada para ti',
            title='Recomendación personalizada',
            body='Basado en tu actividad reciente, te recomendamos: {recommendation_title}',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #0891b2;">💡 Recomendación personalizada</h2>
                <p>Basado en tu actividad reciente, tenemos una recomendación para ti.</p>
                <div style="background-color: #ecfeff; border-left: 4px solid #0891b2; padding: 15px; margin: 20px 0;">
                    <h3>{recommendation_title}</h3>
                    <p>{recommendation_description}</p>
                    <p><strong>¿Por qué te recomendamos esto?</strong></p>
                    <p>{recommendation_reason}</p>
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{action_url}" style="background-color: #0891b2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-right: 10px;">{action_text}</a>
                    <a href="{dismiss_url}" style="background-color: #e5e7eb; color: #374151; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Descartar</a>
                </div>
            </div>
            ''',
            variables=['recommendation_title', 'recommendation_description', 'recommendation_reason', 'action_url', 'action_text', 'dismiss_url']
        )

        # Plantilla: Recordatorio de sesión
        self._templates['session_reminder'] = NotificationTemplate(
            name='session_reminder',
            type=NotificationType.BOTH,
            subject='Recordatorio: {session_name} comienza pronto',
            title='Recordatorio de sesión',
            body='Tu sesión "{session_name}" está programada para comenzar en {time_until_start}.',
            html_body='''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #f59e0b;">⏰ Recordatorio de sesión</h2>
                <p>Tu sesión está programada para comenzar pronto.</p>
                <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                    <h3>{session_name}</h3>
                    <p><strong>Comienza en:</strong> {time_until_start}</p>
                    <p><strong>Hora de inicio:</strong> {start_time}</p>
                    <p><strong>Duración estimada:</strong> {duration}</p>
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{join_url}" style="background-color: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-right: 10px;">Unirse ahora</a>
                    <a href="{reschedule_url}" style="background-color: #e5e7eb; color: #374151; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Reprogramar</a>
                </div>
            </div>
            ''',
            variables=['session_name', 'time_until_start', 'start_time', 'duration', 'join_url', 'reschedule_url']
        )

        # Plantillas específicas para Discord

        # Plantilla: Alerta de sistema para Discord
        self._templates['discord_system_alert'] = NotificationTemplate(
            name='discord_system_alert',
            type=NotificationType.DISCORD,
            title='🚨 Alerta del Sistema',
            body='**Alerta del Sistema**\n\n{alert_message}\n\n**Severidad:** {severity}\n**Hora:** {timestamp}',
            variables=['alert_message', 'severity', 'timestamp']
        )

        # Plantilla: Nueva sesión federada para Discord
        self._templates['discord_federated_session'] = NotificationTemplate(
            name='discord_federated_session',
            type=NotificationType.DISCORD,
            title='🔗 Nueva Sesión Federada Disponible',
            body='**Nueva Sesión Federada**\n\n📋 **{session_name}**\n📝 {session_description}\n⏰ **Inicio:** {start_time}\n👥 **Participantes:** {participant_count}/{max_participants}\n💰 **Recompensa:** {reward_amount} DRS\n\n¡Únete ahora!',
            variables=['session_name', 'session_description', 'start_time', 'participant_count', 'max_participants', 'reward_amount']
        )

        # Plantilla: Recompensa ganada para Discord
        self._templates['discord_reward_earned'] = NotificationTemplate(
            name='discord_reward_earned',
            type=NotificationType.DISCORD,
            title='🎉 ¡Recompensa Ganada!',
            body='**¡Felicitaciones!**\n\nHas ganado **{reward_amount} DRS** por tu participación en:\n📊 {activity_type}\n⏱️ **Completado:** {completion_time}\n\nTu balance actual: **{current_balance} DRS**',
            variables=['reward_amount', 'activity_type', 'completion_time', 'current_balance']
        )

        # Plantilla: Actualización del marketplace para Discord
        self._templates['discord_marketplace_update'] = NotificationTemplate(
            name='discord_marketplace_update',
            type=NotificationType.DISCORD,
            title='🛒 Actualización del Marketplace',
            body='**Nuevo dataset disponible**\n\n📦 **{dataset_name}**\n📝 {dataset_description}\n💰 **Precio:** {price} DRS\n📊 **Calidad:** {quality_score}/10\n👤 **Vendedor:** {seller_name}\n\n¡Disponible para descarga!',
            variables=['dataset_name', 'dataset_description', 'price', 'quality_score', 'seller_name']
        )

        # Plantillas específicas para Webhooks

        # Plantilla: Evento de notificación para webhook
        self._templates['webhook_notification'] = NotificationTemplate(
            name='webhook_notification',
            type=NotificationType.WEBHOOK,
            title='Nueva Notificación',
            body='notification',
            variables=['event_type', 'user_id', 'title', 'body', 'data', 'timestamp']
        )

        # Plantilla: Evento de sesión federada para webhook
        self._templates['webhook_federated_event'] = NotificationTemplate(
            name='webhook_federated_event',
            type=NotificationType.WEBHOOK,
            title='Evento Federado',
            body='federated_event',
            variables=['event_type', 'session_id', 'round_number', 'participants', 'status', 'timestamp']
        )

        # Plantilla: Evento de marketplace para webhook
        self._templates['webhook_marketplace_event'] = NotificationTemplate(
            name='webhook_marketplace_event',
            type=NotificationType.WEBHOOK,
            title='Evento de Marketplace',
            body='marketplace_event',
            variables=['event_type', 'transaction_id', 'buyer_id', 'seller_id', 'dataset_id', 'price', 'timestamp']
        )

        # Plantilla: Evento de sistema para webhook
        self._templates['webhook_system_event'] = NotificationTemplate(
            name='webhook_system_event',
            type=NotificationType.WEBHOOK,
            title='Evento del Sistema',
            body='system_event',
            variables=['event_type', 'severity', 'message', 'component', 'timestamp']
        )

    def get_template(self, template_name: str) -> NotificationTemplate:
        """Obtiene una plantilla por nombre."""
        if template_name not in self._templates:
            raise ValueError(f"Plantilla '{template_name}' no encontrada")
        return self._templates[template_name]

    def list_templates(self) -> List[NotificationTemplate]:
        """Lista todas las plantillas disponibles."""
        return list(self._templates.values())

    def add_template(self, template: NotificationTemplate):
        """Agrega una nueva plantilla."""
        self._templates[template.name] = template

    def remove_template(self, template_name: str):
        """Elimina una plantilla."""
        if template_name in self._templates:
            del self._templates[template_name]

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> NotificationTemplate:
        """Renderiza una plantilla con variables."""
        template = self.get_template(template_name)

        # Crear copia para no modificar la original
        rendered = NotificationTemplate(
            id=template.id,
            name=template.name,
            type=template.type,
            subject=template.subject,
            title=template.title,
            body=template.body,
            html_body=template.html_body,
            variables=template.variables.copy(),
            created_at=template.created_at,
            updated_at=template.updated_at
        )

        # Reemplazar variables en textos
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered.subject = rendered.subject.replace(placeholder, str(value))
            rendered.title = rendered.title.replace(placeholder, str(value))
            rendered.body = rendered.body.replace(placeholder, str(value))
            if rendered.html_body:
                rendered.html_body = rendered.html_body.replace(placeholder, str(value))

        return rendered


# Instancia global de plantillas
notification_templates = NotificationTemplates()