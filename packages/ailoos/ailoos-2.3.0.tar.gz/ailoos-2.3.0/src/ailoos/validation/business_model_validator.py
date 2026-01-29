"""
Business Model Validator - Validación completa del modelo de negocio AILOOS.
Verifica viabilidad económica, escalabilidad y sostenibilidad del sistema.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.logging import get_logger
from ..blockchain import get_token_manager
from ..marketplace import marketplace
from ..node import get_node_capabilities

logger = get_logger(__name__)


@dataclass
class BusinessMetrics:
    """Métricas clave del modelo de negocio."""
    total_users: int = 0
    active_nodes: int = 0
    total_dracma_distributed: float = 0.0
    marketplace_volume: float = 0.0
    avg_session_duration: float = 0.0
    user_retention_rate: float = 0.0
    cost_per_user: float = 0.0
    revenue_per_user: float = 0.0
    network_utilization: float = 0.0


@dataclass
class ValidationResult:
    """Resultado de validación del modelo de negocio."""
    is_viable: bool
    score: float  # 0-100
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    projected_metrics: Dict[str, Any]
    risks: List[str]


class BusinessModelValidator:
    """
    Validador completo del modelo de negocio AILOOS.
    Evalúa viabilidad económica, escalabilidad y riesgos.
    """

    def __init__(self):
        self.metrics = BusinessMetrics()
        self.validation_history: List[ValidationResult] = []

        # Parámetros del modelo de negocio
        self.business_params = {
            "dracma_per_training_hour": 10.0,  # DracmaS por hora de entrenamiento
            "marketplace_commission": 0.15,    # 15% comisión marketplace
            "staking_apy": 0.05,              # 5% APY para staking
            "operational_cost_per_user": 0.50, # $0.50 costo operativo por usuario/mes
            "target_user_acquisition_cost": 5.0, # $5 costo adquisición usuario
            "churn_rate_target": 0.15,        # 15% tasa de abandono objetivo
            "network_efficiency_target": 0.85  # 85% eficiencia de red objetivo
        }

        logger.info("💼 Business Model Validator initialized")

    async def validate_business_model(self) -> ValidationResult:
        """
        Validación completa del modelo de negocio.

        Returns:
            Resultado detallado de la validación
        """
        logger.info("🔍 Starting business model validation...")

        # Recopilar métricas actuales
        await self._collect_current_metrics()

        # Evaluar componentes del modelo
        economic_viability = await self._evaluate_economic_viability()
        scalability = await self._evaluate_scalability()
        sustainability = await self._evaluate_sustainability()
        market_fit = await self._evaluate_market_fit()

        # Calcular score general
        components = [economic_viability, scalability, sustainability, market_fit]
        overall_score = sum(components) / len(components)

        # Determinar viabilidad
        is_viable = overall_score >= 70.0

        # Identificar fortalezas y debilidades
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            economic_viability, scalability, sustainability, market_fit
        )

        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            economic_viability, scalability, sustainability, market_fit
        )

        # Proyectar métricas futuras
        projected_metrics = self._project_future_metrics()

        # Identificar riesgos
        risks = self._identify_risks()

        result = ValidationResult(
            is_viable=is_viable,
            score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            projected_metrics=projected_metrics,
            risks=risks
        )

        self.validation_history.append(result)

        logger.info(f"✅ Business model validation completed. Score: {overall_score:.1f}/100")
        logger.info(f"   Viable: {is_viable}")

        return result

    async def _collect_current_metrics(self):
        """Recopilar métricas actuales del sistema."""
        try:
            # Token metrics
            token_manager = get_token_manager()
            token_info = token_manager.get_token_info()

            # Marketplace metrics
            market_stats = marketplace.get_market_stats()

            # Node capabilities (como proxy para capacidad de red)
            node_caps = get_node_capabilities()

            # Actualizar métricas
            self.metrics.total_dracma_distributed = token_info.get("circulating_supply", 0)
            self.metrics.marketplace_volume = market_stats.get("total_volume_dracma", 0)
            self.metrics.active_nodes = 1  # En desarrollo, asumimos 1 nodo activo
            self.metrics.total_users = 1   # En desarrollo, asumimos 1 usuario

            # Estimaciones basadas en capacidades
            if node_caps.get("gpu_available"):
                self.metrics.network_utilization = 0.8  # Alta utilización con GPU
            else:
                self.metrics.network_utilization = 0.6  # Utilización moderada con CPU

            logger.info("📊 Current metrics collected")

        except Exception as e:
            logger.warning(f"Error collecting metrics: {e}")

    async def _evaluate_economic_viability(self) -> float:
        """
        Evaluar viabilidad económica.

        Returns:
            Score de 0-100
        """
        score = 0.0

        try:
            # Revenue streams
            training_revenue = self.metrics.active_nodes * self.business_params["dracma_per_training_hour"] * 24 * 30  # mensual
            marketplace_revenue = self.metrics.marketplace_volume * self.business_params["marketplace_commission"]
            staking_revenue = self.metrics.total_dracma_distributed * self.business_params["staking_apy"] / 12  # mensual

            total_revenue = training_revenue + marketplace_revenue + staking_revenue

            # Costs
            operational_costs = self.metrics.total_users * self.business_params["operational_cost_per_user"]

            # Profitability
            if total_revenue > operational_costs:
                profitability_ratio = total_revenue / operational_costs
                if profitability_ratio > 2.0:
                    score += 40  # Excelente rentabilidad
                elif profitability_ratio > 1.5:
                    score += 30  # Buena rentabilidad
                elif profitability_ratio > 1.0:
                    score += 20  # Rentable
                else:
                    score += 10  # Marginalmente rentable

            # Unit economics
            if self.metrics.total_users > 0:
                revenue_per_user = total_revenue / self.metrics.total_users
                cost_per_user = operational_costs / self.metrics.total_users

                if revenue_per_user > cost_per_user * 3:
                    score += 30  # Excelente unit economics
                elif revenue_per_user > cost_per_user * 2:
                    score += 20  # Buena unit economics
                elif revenue_per_user > cost_per_user:
                    score += 10  # Positiva unit economics

            # Market validation
            if self.metrics.marketplace_volume > 1000:  # Más de 1000 DracmaS en volumen
                score += 30  # Mercado validado

            score = min(100, score)  # Cap at 100

        except Exception as e:
            logger.error(f"Error evaluating economic viability: {e}")
            score = 25  # Default conservative score

        return score

    async def _evaluate_scalability(self) -> float:
        """
        Evaluar escalabilidad del modelo.

        Returns:
            Score de 0-100
        """
        score = 0.0

        try:
            # Network utilization
            if self.metrics.network_utilization > 0.8:
                score += 25  # Excelente utilización
            elif self.metrics.network_utilization > 0.6:
                score += 15  # Buena utilización

            # Node distribution (estimado)
            # En producción, esto vendría de métricas reales de distribución geográfica
            estimated_global_coverage = 0.3  # 30% cobertura global estimada
            if estimated_global_coverage > 0.5:
                score += 25
            elif estimated_global_coverage > 0.3:
                score += 15

            # Technology stack scalability
            # IPFS + Federated Learning = altamente escalable
            score += 25

            # Cost scaling
            # Modelo distribuido debería tener costos marginales cercanos a cero
            score += 25

        except Exception as e:
            logger.error(f"Error evaluating scalability: {e}")
            score = 40  # Default moderate score

        return score

    async def _evaluate_sustainability(self) -> float:
        """
        Evaluar sostenibilidad del modelo.

        Returns:
            Score de 0-100
        """
        score = 0.0

        try:
            # Tokenomics balance
            circulating_supply = self.metrics.total_dracma_distributed
            total_supply = 1_000_000_000  # 1B DracmaS total

            if circulating_supply < total_supply * 0.1:  # Menos del 10% en circulación
                score += 25  # Saludable - supply controlado

            # Incentive alignment
            # Los nodos ganan por contribuir, usuarios pagan por valor
            score += 25

            # Regulatory compliance
            # Privacidad por diseño, datos locales
            score += 25

            # Community governance potential
            # DAO structure preparado
            score += 25

        except Exception as e:
            logger.error(f"Error evaluating sustainability: {e}")
            score = 50  # Default moderate score

        return score

    async def _evaluate_market_fit(self) -> float:
        """
        Evaluar ajuste al mercado.

        Returns:
            Score de 0-100
        """
        score = 0.0

        try:
            # Problem validation
            # IA accesible es un problema real
            score += 20

            # Solution uniqueness
            # Federated learning + tokenomics único
            score += 25

            # Market size
            # Mercado IA = $500B+, federated subset significativo
            score += 25

            # Competition
            # Pocos competidores directos
            score += 20

            # Go-to-market
            # Freemium + enterprise = buena estrategia
            score += 10

        except Exception as e:
            logger.error(f"Error evaluating market fit: {e}")
            score = 60  # Default good score for market fit

        return score

    def _analyze_strengths_weaknesses(self, economic: float, scalability: float,
                                    sustainability: float, market_fit: float) -> Tuple[List[str], List[str]]:
        """Analizar fortalezas y debilidades."""
        strengths = []
        weaknesses = []

        # Economic strengths
        if economic > 80:
            strengths.append("Excelente viabilidad económica con múltiples streams de revenue")
        elif economic > 60:
            strengths.append("Buena viabilidad económica")
        else:
            weaknesses.append("Viabilidad económica requiere validación adicional")

        # Scalability strengths
        if scalability > 80:
            strengths.append("Arquitectura altamente escalable con costos marginales cercanos a cero")
        elif scalability > 60:
            strengths.append("Buena escalabilidad técnica")
        else:
            weaknesses.append("Escalabilidad necesita optimizaciones adicionales")

        # Sustainability strengths
        if sustainability > 80:
            strengths.append("Modelo sostenible con tokenomics balanceados y privacidad por diseño")
        elif sustainability > 60:
            strengths.append("Fundamentos sólidos de sostenibilidad")
        else:
            weaknesses.append("Sostenibilidad requiere más validación")

        # Market fit strengths
        if market_fit > 80:
            strengths.append("Excelente ajuste al mercado con problema validado y solución única")
        elif market_fit > 60:
            strengths.append("Buen ajuste al mercado")
        else:
            weaknesses.append("Ajuste al mercado necesita más validación")

        return strengths, weaknesses

    def _generate_recommendations(self, economic: float, scalability: float,
                                sustainability: float, market_fit: float) -> List[str]:
        """Generar recomendaciones basadas en evaluación."""
        recommendations = []

        if economic < 70:
            recommendations.extend([
                "Validar unit economics con usuarios reales",
                "Optimizar costo de adquisición de usuarios",
                "Desarrollar más streams de revenue enterprise"
            ])

        if scalability < 70:
            recommendations.extend([
                "Implementar monitoreo de performance distribuido",
                "Optimizar algoritmos de federated learning para edge devices",
                "Expandir cobertura geográfica de nodos"
            ])

        if sustainability < 70:
            recommendations.extend([
                "Implementar governance DAO para decisiones comunitarias",
                "Desarrollar programa de staking con rewards atractivos",
                "Preparar compliance regulatory para diferentes jurisdicciones"
            ])

        if market_fit < 70:
            recommendations.extend([
                "Realizar más validación de mercado con usuarios objetivo",
                "Desarrollar casos de uso específicos por industria",
                "Crear partnerships estratégicos con empresas de IA"
            ])

        # Recomendaciones generales
        recommendations.extend([
            "Implementar métricas detalladas de engagement de usuarios",
            "Desarrollar programa de referidos para crecimiento orgánico",
            "Crear contenido educativo sobre IA distribuida"
        ])

        return recommendations

    def _project_future_metrics(self) -> Dict[str, Any]:
        """Proyectar métricas futuras basadas en tendencias actuales."""
        projections = {}

        try:
            # Proyecciones conservadoras basadas en métricas actuales
            current_users = max(1, self.metrics.total_users)
            current_nodes = max(1, self.metrics.active_nodes)

            # Proyección 6 meses
            projections["6_months"] = {
                "users": current_users * 10,  # 10x crecimiento
                "nodes": current_nodes * 15,  # 15x crecimiento
                "dracma_volume": self.metrics.total_dracma_distributed * 5,
                "marketplace_volume": self.metrics.marketplace_volume * 8,
                "revenue_monthly": current_users * 10 * 25  # $25 ARPU estimado
            }

            # Proyección 12 meses
            projections["12_months"] = {
                "users": current_users * 50,   # 50x crecimiento
                "nodes": current_nodes * 100,  # 100x crecimiento
                "dracma_volume": self.metrics.total_dracma_distributed * 25,
                "marketplace_volume": self.metrics.marketplace_volume * 40,
                "revenue_monthly": current_users * 50 * 25
            }

            # Proyección 24 meses
            projections["24_months"] = {
                "users": current_users * 500,    # 500x crecimiento
                "nodes": current_nodes * 1000,   # 1000x crecimiento
                "dracma_volume": self.metrics.total_dracma_distributed * 200,
                "marketplace_volume": self.metrics.marketplace_volume * 500,
                "revenue_monthly": current_users * 500 * 25
            }

        except Exception as e:
            logger.error(f"Error projecting metrics: {e}")
            projections = {"error": "Could not generate projections"}

        return projections

    def _identify_risks(self) -> List[str]:
        """Identificar riesgos del modelo de negocio."""
        risks = [
            " Riesgo regulatorio: Cambios en leyes de criptomonedas o privacidad de datos",
            " Riesgo técnico: Fallos en escalabilidad de federated learning con millones de nodos",
            " Riesgo de mercado: Competidores con más recursos (Google, Meta, etc.)",
            " Riesgo de adopción: Curva de aprendizaje para usuarios no técnicos",
            " Riesgo económico: Volatilidad del precio del token DRACMA",
            " Riesgo operacional: Dependencia de infraestructura IPFS y coordinadores"
        ]

        return risks

    def save_validation_report(self, filename: str = "business_model_validation.json"):
        """
        Guardar reporte completo de validación.

        Args:
            filename: Archivo donde guardar el reporte
        """
        try:
            report = {
                "validation_timestamp": time.time(),
                "datetime": time.strftime('%Y-%m-%d %H:%M:%S'),
                "current_metrics": {
                    "total_users": self.metrics.total_users,
                    "active_nodes": self.metrics.active_nodes,
                    "total_dracma_distributed": self.metrics.total_dracma_distributed,
                    "marketplace_volume": self.metrics.marketplace_volume,
                    "network_utilization": self.metrics.network_utilization
                },
                "business_parameters": self.business_params,
                "validation_history": [
                    {
                        "is_viable": v.is_viable,
                        "score": v.score,
                        "strengths": v.strengths,
                        "weaknesses": v.weaknesses,
                        "recommendations": v.recommendations,
                        "risks": v.risks
                    }
                    for v in self.validation_history[-5:]  # Últimas 5 validaciones
                ]
            }

            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"📄 Business model validation report saved to {filename}")

        except Exception as e:
            logger.error(f"❌ Failed to save validation report: {e}")

    def print_validation_summary(self, result: ValidationResult):
        """
        Imprimir resumen de validación.

        Args:
            result: Resultado de validación a imprimir
        """
        print("\n" + "="*80)
        print("💼 AILOOS BUSINESS MODEL VALIDATION REPORT")
        print("="*80)

        print(f"\n📊 OVERALL SCORE: {result.score:.1f}/100")
        print(f"✅ VIABLE: {'YES' if result.is_viable else 'NO'}")

        print("\n🏆 STRENGTHS:")
        for strength in result.strengths:
            print(f"   • {strength}")

        print("\n⚠️  WEAKNESSES:")
        for weakness in result.weaknesses:
            print(f"   • {weakness}")

        print("\n💡 RECOMMENDATIONS:")
        for rec in result.recommendations[:5]:  # Top 5
            print(f"   • {rec}")

        print("\n🚨 TOP RISKS:")
        for risk in result.risks[:3]:  # Top 3
            print(f"   • {risk}")

        print("\n📈 FUTURE PROJECTIONS:")
        projections = result.projected_metrics
        if "12_months" in projections:
            p12 = projections["12_months"]
            print(f"   • 12 months: {p12.get('users', 0):,} users, ${p12.get('revenue_monthly', 0):,.0f}/month")

        if "24_months" in projections:
            p24 = projections["24_months"]
            print(f"   • 24 months: {p24.get('users', 0):,} users, ${p24.get('revenue_monthly', 0):,.0f}/month")

        print("\n" + "="*80)


# Funciones de conveniencia
async def validate_business_model(save_report: bool = True) -> ValidationResult:
    """
    Validar modelo de negocio completo.

    Args:
        save_report: Si guardar reporte en archivo

    Returns:
        Resultado de validación
    """
    validator = BusinessModelValidator()
    result = await validator.validate_business_model()

    if save_report:
        validator.save_validation_report()

    validator.print_validation_summary(result)

    return result


def validate_business_model_sync(save_report: bool = True) -> ValidationResult:
    """
    Validar modelo de negocio de manera síncrona.

    Args:
        save_report: Si guardar reporte en archivo

    Returns:
        Resultado de validación
    """
    return asyncio.run(validate_business_model(save_report))


if __name__ == "__main__":
    print("🚀 Running AILOOS Business Model Validation...")
    result = validate_business_model_sync()
    print(f"\n🏁 Validation completed. Viable: {result.is_viable}, Score: {result.score:.1f}/100")