"""
API endpoints para consultar logs, auditoría y métricas.
Proporciona endpoints REST para acceder al sistema de auditoría.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..core.config import get_config
from .audit_manager import get_audit_manager, AuditEventType, SecurityAlertLevel
from .security_monitor import get_security_monitor
from .metrics_collector import get_metrics_collector
from .structured_logger import get_structured_logger
from ..coordinator.auth.dependencies import get_current_admin

router = APIRouter()
logger = get_structured_logger("audit_api")


@router.get("/events", response_model=Dict[str, Any],
           summary="Obtener eventos de auditoría",
           description="Obtiene eventos de auditoría filtrados por criterios específicos.")
async def get_audit_events(
    event_type: Optional[str] = Query(None, description="Tipo de evento"),
    user_id: Optional[str] = Query(None, description="ID de usuario"),
    resource: Optional[str] = Query(None, description="Recurso"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Obtener eventos de auditoría con filtros.

    - **event_type**: Filtrar por tipo de evento
    - **user_id**: Filtrar por usuario
    - **resource**: Filtrar por recurso
    - **start_date**: Fecha de inicio (ISO format)
    - **end_date**: Fecha de fin (ISO format)
    - **limit**: Número máximo de resultados
    """
    try:
        audit_manager = get_audit_manager()

        # Convertir string a enum si es necesario
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")

        events = audit_manager.get_audit_events(
            event_type=event_type_enum,
            user_id=user_id,
            resource=resource,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        logger.log_api_request("GET", "/api/v1/auditing/events", 200, 0.0, user_id=current_admin.get('sub'))

        return {
            "events": [event.to_dict() for event in events],
            "total": len(events),
            "filters": {
                "event_type": event_type,
                "user_id": user_id,
                "resource": resource,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/events", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving audit events: {str(e)}")


@router.get("/alerts", response_model=Dict[str, Any],
           summary="Obtener alertas de seguridad",
           description="Obtiene alertas de seguridad activas y recientes.")
async def get_security_alerts(
    level: Optional[str] = Query(None, description="Nivel de alerta"),
    acknowledged: Optional[bool] = Query(None, description="Si está reconocida"),
    limit: int = Query(50, ge=1, le=500, description="Límite de resultados"),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Obtener alertas de seguridad.

    - **level**: Filtrar por nivel (low, medium, high, critical)
    - **acknowledged**: Filtrar por estado de reconocimiento
    - **limit**: Número máximo de resultados
    """
    try:
        audit_manager = get_audit_manager()

        # Convertir string a enum si es necesario
        level_enum = None
        if level:
            try:
                level_enum = SecurityAlertLevel(level.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid alert level: {level}")

        alerts = audit_manager.get_security_alerts(
            level=level_enum,
            acknowledged=acknowledged,
            limit=limit
        )

        logger.log_api_request("GET", "/api/v1/auditing/alerts", 200, 0.0, user_id=current_admin.get('sub'))

        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts),
            "unacknowledged_count": len([a for a in alerts if not a.acknowledged])
        }

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/alerts", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving security alerts: {str(e)}")


@router.put("/alerts/{alert_id}/acknowledge", response_model=Dict[str, Any],
           summary="Reconocer alerta de seguridad",
           description="Marca una alerta de seguridad como reconocida.")
async def acknowledge_alert(
    alert_id: str,
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Reconocer una alerta de seguridad.

    - **alert_id**: ID de la alerta a reconocer
    """
    try:
        audit_manager = get_audit_manager()

        success = audit_manager.acknowledge_alert(alert_id, current_admin.get('sub', 'unknown'))

        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")

        logger.log_api_request("PUT", f"/api/v1/auditing/alerts/{alert_id}/acknowledge", 200, 0.0,
                             user_id=current_admin.get('sub'))

        return {
            "success": True,
            "message": "Alert acknowledged successfully",
            "alert_id": alert_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.log_api_request("PUT", f"/api/v1/auditing/alerts/{alert_id}/acknowledge", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error acknowledging alert: {str(e)}")


@router.get("/metrics", response_model=Dict[str, Any],
           summary="Obtener métricas del sistema",
           description="Obtiene métricas actuales y tendencias del sistema.")
async def get_system_metrics(
    hours: int = Query(1, ge=1, le=24, description="Horas de historial"),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Obtener métricas del sistema.

    - **hours**: Horas de historial a incluir
    """
    try:
        metrics_collector = get_metrics_collector()

        latest = metrics_collector.get_latest_metrics()
        history = metrics_collector.get_metrics_history(hours=hours)
        performance_stats = metrics_collector.get_performance_stats()

        logger.log_api_request("GET", "/api/v1/auditing/metrics", 200, 0.0, user_id=current_admin.get('sub'))

        return {
            "latest": latest,
            "history": history,
            "performance_stats": performance_stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/metrics", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving system metrics: {str(e)}")


@router.get("/health", response_model=Dict[str, Any],
           summary="Obtener estado de salud del sistema",
           description="Obtiene el estado de salud de todos los servicios del sistema.")
async def get_system_health(
    current_admin: Dict = Depends(get_current_admin)
):
    """Obtener estado de salud del sistema."""
    try:
        metrics_collector = get_metrics_collector()
        health_status = metrics_collector.get_health_status()

        logger.log_api_request("GET", "/api/v1/auditing/health", 200, 0.0, user_id=current_admin.get('sub'))

        return health_status

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/health", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving system health: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any],
           summary="Obtener estadísticas de auditoría",
           description="Obtiene estadísticas generales del sistema de auditoría.")
async def get_audit_statistics(
    current_admin: Dict = Depends(get_current_admin)
):
    """Obtener estadísticas de auditoría."""
    try:
        audit_manager = get_audit_manager()
        security_monitor = get_security_monitor()

        audit_stats = audit_manager.get_audit_statistics()
        security_status = security_monitor.get_security_status()

        logger.log_api_request("GET", "/api/v1/auditing/statistics", 200, 0.0, user_id=current_admin.get('sub'))

        return {
            "audit_statistics": audit_stats,
            "security_status": security_status,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/statistics", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving audit statistics: {str(e)}")


@router.get("/report", response_model=Dict[str, Any],
           summary="Generar reporte completo de auditoría",
           description="Genera un reporte completo de auditoría para un período específico.")
async def generate_audit_report(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    include_metrics: bool = Query(True, description="Incluir métricas"),
    include_zk_audit: bool = Query(True, description="Incluir auditoría ZK"),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Generar reporte completo de auditoría.

    - **start_date**: Fecha de inicio del reporte
    - **end_date**: Fecha de fin del reporte
    - **include_metrics**: Incluir métricas del sistema
    - **include_zk_audit**: Incluir auditoría zero-knowledge
    """
    try:
        audit_manager = get_audit_manager()

        report = await audit_manager.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            include_metrics=include_metrics,
            include_zk_audit=include_zk_audit
        )

        logger.log_api_request("GET", "/api/v1/auditing/report", 200, 0.0, user_id=current_admin.get('sub'))

        return report

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/report", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error generating audit report: {str(e)}")


@router.get("/export", response_class=StreamingResponse,
           summary="Exportar datos de auditoría",
           description="Exporta datos de auditoría en formato JSON para análisis externo.")
async def export_audit_data(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    data_type: str = Query("events", description="Tipo de datos: events, alerts, metrics"),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Exportar datos de auditoría.

    - **start_date**: Fecha de inicio
    - **end_date**: Fecha de fin
    - **data_type**: Tipo de datos a exportar (events, alerts, metrics)
    """
    try:
        async def generate_export():
            audit_manager = get_audit_manager()
            metrics_collector = get_metrics_collector()

            if data_type == "events":
                events = audit_manager.get_audit_events(
                    start_date=start_date,
                    end_date=end_date,
                    limit=10000
                )
                data = {"events": [event.to_dict() for event in events]}

            elif data_type == "alerts":
                alerts = audit_manager.get_security_alerts(limit=1000)
                data = {"alerts": [alert.to_dict() for alert in alerts]}

            elif data_type == "metrics":
                history = metrics_collector.get_metrics_history(hours=24)
                data = {"metrics": history}

            else:
                raise HTTPException(status_code=400, detail=f"Invalid data_type: {data_type}")

            # Metadata del export
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": current_admin.get('sub'),
                    "data_type": data_type,
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    }
                },
                **data
            }

            yield json.dumps(export_data, indent=2, ensure_ascii=False)

        logger.log_api_request("GET", "/api/v1/auditing/export", 200, 0.0, user_id=current_admin.get('sub'))

        return StreamingResponse(
            generate_export(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=audit_export_{data_type}_{int(datetime.now().timestamp())}.json"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/export", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error exporting audit data: {str(e)}")


@router.get("/config-audit", response_model=Dict[str, Any],
           summary="Obtener historial de cambios de configuración",
           description="Obtiene el historial de cambios en la configuración del sistema.")
async def get_config_audit_history(
    key: Optional[str] = Query(None, description="Clave de configuración específica"),
    user: Optional[str] = Query(None, description="Usuario que realizó cambios"),
    category: Optional[str] = Query(None, description="Categoría de configuración"),
    limit: int = Query(50, ge=1, le=500, description="Límite de resultados"),
    current_admin: Dict = Depends(get_current_admin)
):
    """
    Obtener historial de cambios de configuración.

    - **key**: Filtrar por clave específica
    - **user**: Filtrar por usuario
    - **category**: Filtrar por categoría
    - **limit**: Número máximo de resultados
    """
    try:
        from ..validation.config_auditor import get_config_auditor

        config_auditor = get_config_auditor()
        changes = config_auditor.get_config_history(
            key=key,
            user=user,
            category=category,
            limit=limit
        )

        logger.log_api_request("GET", "/api/v1/auditing/config-audit", 200, 0.0, user_id=current_admin.get('sub'))

        return {
            "changes": [change.to_dict() for change in changes],
            "total": len(changes),
            "filters": {
                "key": key,
                "user": user,
                "category": category
            }
        }

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/config-audit", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving config audit history: {str(e)}")


@router.get("/realtime", response_model=Dict[str, Any],
           summary="Obtener datos en tiempo real",
           description="Obtiene datos de auditoría y métricas en tiempo real.")
async def get_realtime_data(
    current_admin: Dict = Depends(get_current_admin)
):
    """Obtener datos en tiempo real para dashboard."""
    try:
        audit_manager = get_audit_manager()
        metrics_collector = get_metrics_collector()
        security_monitor = get_security_monitor()

        # Eventos recientes (última hora)
        recent_events = audit_manager.get_audit_events(
            start_date=datetime.now() - timedelta(hours=1),
            limit=20
        )

        # Alertas activas no reconocidas
        active_alerts = audit_manager.get_security_alerts(
            acknowledged=False,
            limit=10
        )

        # Métricas actuales
        latest_metrics = metrics_collector.get_latest_metrics()

        # Estado de seguridad
        security_status = security_monitor.get_security_status()

        logger.log_api_request("GET", "/api/v1/auditing/realtime", 200, 0.0, user_id=current_admin.get('sub'))

        return {
            "recent_events": [event.to_dict() for event in recent_events],
            "active_alerts": [alert.to_dict() for alert in active_alerts],
            "current_metrics": latest_metrics,
            "security_status": security_status,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.log_api_request("GET", "/api/v1/auditing/realtime", 500, 0.0,
                             user_id=current_admin.get('sub'), error=str(e))
        raise HTTPException(status_code=500, detail=f"Error retrieving realtime data: {str(e)}")