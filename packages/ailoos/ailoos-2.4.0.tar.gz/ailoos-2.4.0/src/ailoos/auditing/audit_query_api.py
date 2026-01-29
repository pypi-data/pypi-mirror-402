"""
API para consultas de auditoría y reportes en AILOOS.
Proporciona endpoints REST para acceder a datos de auditoría blockchain.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from .blockchain_auditor import get_blockchain_auditor
from .hash_chain_manager import get_hash_chain_manager
from .audit_smart_contracts import get_smart_contract_manager
from ..core.logging import get_logger

logger = get_logger(__name__)

# Crear router para la API de auditoría
audit_router = APIRouter(prefix="/audit", tags=["audit"])


@audit_router.get("/blockchain/info")
async def get_blockchain_info():
    """
    Obtiene información general de la blockchain de auditoría.
    """
    try:
        auditor = get_blockchain_auditor()
        info = auditor.get_chain_info()

        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        logger.error("Error getting blockchain info: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/blockchain/blocks/{block_index}")
async def get_block(block_index: int):
    """
    Obtiene un bloque específico por índice.
    """
    try:
        auditor = get_blockchain_auditor()
        block = auditor.get_block_by_index(block_index)

        if not block:
            raise HTTPException(status_code=404, detail="Block not found")

        return {
            "status": "success",
            "data": {
                "index": block.index,
                "timestamp": block.timestamp,
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "operations_count": len(block.operations),
                "merkle_root": block.merkle_root,
                "operations": block.operations
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting block %d: %s", block_index, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/blockchain/blocks")
async def get_blocks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Obtiene lista de bloques con paginación.
    """
    try:
        auditor = get_blockchain_auditor()
        total_blocks = len(auditor.chain)

        start_index = max(0, total_blocks - offset - limit)
        end_index = max(0, total_blocks - offset)

        blocks = []
        for i in range(start_index, end_index):
            block = auditor.chain[i]
            blocks.append({
                "index": block.index,
                "timestamp": block.timestamp,
                "hash": block.hash,
                "operations_count": len(block.operations),
                "merkle_root": block.merkle_root
            })

        return {
            "status": "success",
            "data": {
                "blocks": blocks,
                "total": total_blocks,
                "limit": limit,
                "offset": offset
            }
        }
    except Exception as e:
        logger.error("Error getting blocks: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/blockchain/search")
async def search_operations(
    operation_type: Optional[str] = None,
    user_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Busca operaciones en la blockchain por filtros.
    """
    try:
        filters = {}

        if operation_type:
            filters["operation_type"] = operation_type
        if user_id:
            filters["user_id"] = user_id
        if date_from:
            filters["date_from"] = date_from.timestamp()
        if date_to:
            filters["date_to"] = date_to.timestamp()

        auditor = get_blockchain_auditor()
        results = auditor.search_operations(filters)

        # Limitar resultados
        results = results[:limit]

        return {
            "status": "success",
            "data": {
                "operations": results,
                "count": len(results),
                "filters": filters
            }
        }
    except Exception as e:
        logger.error("Error searching operations: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/blockchain/proof/{operation_id}")
async def get_operation_proof(operation_id: str):
    """
    Obtiene prueba de existencia de una operación en la blockchain.
    """
    try:
        auditor = get_blockchain_auditor()
        proof = auditor.get_operation_proof(operation_id)

        if not proof:
            raise HTTPException(status_code=404, detail="Operation not found")

        return {
            "status": "success",
            "data": proof
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting operation proof for %s: %s", operation_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/hash-chains/info")
async def get_hash_chains_info():
    """
    Obtiene información de todas las cadenas de hash.
    """
    try:
        manager = get_hash_chain_manager()
        info = manager.get_all_chains_info()

        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        logger.error("Error getting hash chains info: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/hash-chains/{chain_id}/info")
async def get_hash_chain_info(chain_id: str):
    """
    Obtiene información de una cadena de hash específica.
    """
    try:
        manager = get_hash_chain_manager()
        info = manager.get_chain_info(chain_id)

        if not info:
            raise HTTPException(status_code=404, detail="Hash chain not found")

        return {
            "status": "success",
            "data": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting hash chain info for %s: %s", chain_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/hash-chains/{chain_id}/entries")
async def get_hash_chain_entries(
    chain_id: str,
    limit: int = Query(100, ge=1, le=1000),
    timestamp_from: Optional[float] = None,
    timestamp_to: Optional[float] = None
):
    """
    Obtiene entradas de una cadena de hash con filtros.
    """
    try:
        manager = get_hash_chain_manager()

        # Verificar que la cadena existe
        if chain_id not in manager.chains:
            raise HTTPException(status_code=404, detail="Hash chain not found")

        chain = manager.chains[chain_id]

        # Aplicar filtros
        entries = chain.entries
        if timestamp_from:
            entries = [e for e in entries if e.timestamp >= timestamp_from]
        if timestamp_to:
            entries = [e for e in entries if e.timestamp <= timestamp_to]

        # Ordenar por timestamp descendente y limitar
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        entries = entries[:limit]

        return {
            "status": "success",
            "data": {
                "chain_id": chain_id,
                "entries": [e.to_dict() for e in entries],
                "count": len(entries)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting hash chain entries for %s: %s", chain_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/hash-chains/{chain_id}/proof/{entry_id}")
async def get_hash_chain_proof(chain_id: str, entry_id: str):
    """
    Obtiene prueba de integridad para una entrada de hash chain.
    """
    try:
        manager = get_hash_chain_manager()
        proof = manager.create_integrity_proof(chain_id, entry_id)

        if not proof:
            raise HTTPException(status_code=404, detail="Entry or chain not found")

        return {
            "status": "success",
            "data": proof
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting hash chain proof for %s:%s: %s", chain_id, entry_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/smart-contracts/info")
async def get_smart_contracts_info():
    """
    Obtiene información de todos los contratos inteligentes.
    """
    try:
        manager = get_smart_contract_manager()
        info = manager.get_all_contracts_info()

        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        logger.error("Error getting smart contracts info: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/smart-contracts/{contract_id}/info")
async def get_smart_contract_info(contract_id: str):
    """
    Obtiene información de un contrato inteligente específico.
    """
    try:
        manager = get_smart_contract_manager()
        info = manager.get_contract_info(contract_id)

        if not info:
            raise HTTPException(status_code=404, detail="Smart contract not found")

        return {
            "status": "success",
            "data": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting smart contract info for %s: %s", contract_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/smart-contracts/executions")
async def get_contract_executions(
    contract_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Obtiene historial de ejecuciones de contratos.
    """
    try:
        manager = get_smart_contract_manager()
        executions = manager.get_execution_history(contract_id, limit)

        return {
            "status": "success",
            "data": {
                "executions": executions,
                "count": len(executions),
                "contract_filter": contract_id
            }
        }
    except Exception as e:
        logger.error("Error getting contract executions: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.post("/smart-contracts/{contract_id}/execute")
async def execute_smart_contract(contract_id: str, operation: Dict[str, Any]):
    """
    Ejecuta un contrato inteligente sobre una operación.
    """
    try:
        manager = get_smart_contract_manager()
        execution = await manager.execute_contract(contract_id, operation)

        if not execution:
            raise HTTPException(status_code=404, detail="Contract not found or inactive")

        return {
            "status": "success",
            "data": {
                "execution": {
                    "contract_id": execution.contract_id,
                    "operation_id": execution.operation_id,
                    "success": execution.success,
                    "result": execution.result,
                    "gas_used": execution.gas_used,
                    "timestamp": execution.timestamp,
                    "events": execution.events
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error executing smart contract %s: %s", contract_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.post("/validate-operation")
async def validate_operation(operation: Dict[str, Any]):
    """
    Valida una operación ejecutando todos los contratos inteligentes activos.
    """
    try:
        # Ejecutar todos los contratos
        contract_manager = get_smart_contract_manager()
        executions = await contract_manager.execute_all_contracts(operation)

        # Agregar a blockchain si la validación pasa
        blockchain_auditor = get_blockchain_auditor()
        hash_chain_manager = get_hash_chain_manager()

        # Verificar si todas las validaciones pasaron
        all_passed = all(exec.success for exec in executions)

        if all_passed:
            # Registrar en blockchain
            from .blockchain_auditor import AuditOperation
            audit_op = AuditOperation(
                operation_id=operation.get("operation_id", f"op_{int(datetime.now().timestamp())}"),
                operation_type=operation.get("operation_type", "unknown"),
                user_id=operation.get("user_id", "system"),
                timestamp=operation.get("timestamp", datetime.now().timestamp()),
                data=operation.get("data", {}),
                compliance_flags=[event.get("event", "") for exec in executions for event in exec.events]
            )

            await blockchain_auditor.add_operation(audit_op)

            # Registrar en hash chain apropiada
            chain_type = operation.get("operation_type", "general")
            hash_chain_manager.add_log_entry(f"operation_{chain_type}", operation)

        # Preparar respuesta
        validation_results = []
        for exec in executions:
            validation_results.append({
                "contract_id": exec.contract_id,
                "success": exec.success,
                "result": exec.result,
                "events": exec.events
            })

        return {
            "status": "success",
            "data": {
                "operation_id": operation.get("operation_id"),
                "validation_passed": all_passed,
                "contracts_executed": len(executions),
                "validation_results": validation_results,
                "blockchain_registered": all_passed
            }
        }
    except Exception as e:
        logger.error("Error validating operation: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/reports/compliance-summary")
async def get_compliance_summary(
    days: int = Query(30, ge=1, le=365)
):
    """
    Obtiene resumen de compliance para el período especificado.
    """
    try:
        # Calcular fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Buscar operaciones en blockchain
        auditor = get_blockchain_auditor()
        operations = auditor.search_operations({
            "date_from": start_date.timestamp(),
            "date_to": end_date.timestamp()
        })

        # Analizar compliance
        total_operations = len(operations)
        compliant_operations = 0
        violations = []

        for op in operations:
            compliance_flags = op.get("compliance_flags", [])
            if not any("violation" in flag.lower() for flag in compliance_flags):
                compliant_operations += 1
            else:
                violations.extend([flag for flag in compliance_flags if "violation" in flag.lower()])

        compliance_rate = (compliant_operations / total_operations * 100) if total_operations > 0 else 100

        # Obtener estadísticas de contratos
        contract_manager = get_smart_contract_manager()
        executions = contract_manager.get_execution_history(limit=1000)

        # Filtrar por período
        recent_executions = [e for e in executions if e["timestamp"] >= start_date.timestamp()]

        return {
            "status": "success",
            "data": {
                "period_days": days,
                "total_operations": total_operations,
                "compliant_operations": compliant_operations,
                "compliance_rate": round(compliance_rate, 2),
                "total_violations": len(violations),
                "contract_executions": len(recent_executions),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        }
    except Exception as e:
        logger.error("Error getting compliance summary: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@audit_router.get("/reports/risk-assessment")
async def get_risk_assessment_report(
    days: int = Query(7, ge=1, le=90)
):
    """
    Obtiene reporte de evaluación de riesgos.
    """
    try:
        # Obtener ejecuciones del contrato de riesgo
        contract_manager = get_smart_contract_manager()
        executions = contract_manager.get_execution_history("risk_assessor", limit=1000)

        # Filtrar por período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        recent_executions = [e for e in executions if e["timestamp"] >= start_date.timestamp()]

        # Analizar niveles de riesgo
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0, "minimal": 0}
        total_risk_score = 0

        for exec in recent_executions:
            result = exec.get("result", {})
            level = result.get("risk_level", "unknown")
            score = result.get("risk_score", 0)

            if level in risk_levels:
                risk_levels[level] += 1
            total_risk_score += score

        avg_risk_score = total_risk_score / len(recent_executions) if recent_executions else 0

        return {
            "status": "success",
            "data": {
                "period_days": days,
                "total_assessments": len(recent_executions),
                "average_risk_score": round(avg_risk_score, 2),
                "risk_distribution": risk_levels,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        }
    except Exception as e:
        logger.error("Error getting risk assessment report: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# Exportar el router para incluirlo en la aplicación principal
__all__ = ["audit_router"]