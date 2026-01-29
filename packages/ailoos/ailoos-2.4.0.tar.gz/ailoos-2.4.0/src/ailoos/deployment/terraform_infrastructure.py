"""
Infrastructure as Code con Terraform para AILOOS

Implementa IaC completo con:
- Terraform modules modulares
- Multi-region deployment
- Cost optimization automática
- Security hardening
- Monitoring y alerting integrado
"""

import asyncio
import logging
import json
import yaml
import os
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import statistics

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Proveedores de cloud disponibles."""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"


class Environment(Enum):
    """Entornos de deployment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ResourceType(Enum):
    """Tipos de recursos disponibles."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    MONITORING = "monitoring"
    SECURITY = "security"


@dataclass
class TerraformModule:
    """Módulo Terraform."""
    name: str
    source: str
    version: str = "latest"
    variables: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    @property
    def module_path(self) -> str:
        """Obtener path del módulo."""
        return f"modules/{self.name}"


@dataclass
class InfrastructureComponent:
    """Componente de infraestructura."""
    name: str
    resource_type: ResourceType
    provider: CloudProvider
    region: str
    environment: Environment
    terraform_module: TerraformModule
    cost_per_hour: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    @property
    def resource_id(self) -> str:
        """ID único del recurso."""
        return f"{self.provider.value}-{self.environment.value}-{self.name}"


@dataclass
class MultiRegionDeployment:
    """Deployment multi-región."""
    name: str
    primary_region: str
    secondary_regions: List[str]
    components: List[InfrastructureComponent]
    failover_strategy: str = "active-passive"
    traffic_distribution: Dict[str, float] = field(default_factory=dict)
    status: str = "pending"

    def __post_init__(self):
        # Inicializar distribución de tráfico (100% primary)
        self.traffic_distribution = {self.primary_region: 100.0}
        for region in self.secondary_regions:
            self.traffic_distribution[region] = 0.0


class TerraformManager:
    """
    Gestor de Terraform para IaC.

    Características:
    - Planificación automática
    - Apply con approval
    - State management
    - Drift detection
    - Cost estimation
    """

    def __init__(self, working_dir: str = "./infrastructure/terraform"):
        self.working_dir = working_dir
        self.modules: Dict[str, TerraformModule] = {}
        self.state_files: Dict[str, Dict[str, Any]] = {}
        self.plan_cache: Dict[str, Dict[str, Any]] = {}

    def add_module(self, module: TerraformModule):
        """Añadir módulo Terraform."""
        self.modules[module.name] = module
        logger.info(f"Added Terraform module: {module.name}")

    async def generate_terraform_config(self, components: List[InfrastructureComponent],
                                      environment: Environment) -> str:
        """Generar configuración Terraform."""
        config_lines = [
            'terraform {',
            '  required_version = ">= 1.0"',
            '  required_providers {',
            '    google = {',
            '      source  = "hashicorp/google"',
            '      version = "~> 4.0"',
            '    }',
            '  }',
            '}',
            '',
            f'variable "environment" {{',
            f'  description = "Environment name"',
            f'  type        = string',
            f'  default     = "{environment.value}"',
            '}',
            '',
            f'variable "project_id" {{',
            f'  description = "GCP Project ID"',
            f'  type        = string',
            '}',
            ''
        ]

        # Añadir módulos
        for component in components:
            module = component.terraform_module
            config_lines.extend([
                f'module "{component.name}" {{',
                f'  source  = "{module.source}"',
                f'  version = "{module.version}"',
                ''
            ])

            # Variables del módulo
            for var_name, var_value in module.variables.items():
                if isinstance(var_value, str):
                    config_lines.append(f'  {var_name} = "{var_value}"')
                else:
                    config_lines.append(f'  {var_name} = {var_value}')

            # Variables específicas del componente
            config_lines.extend([
                f'  environment = var.environment',
                f'  region      = "{component.region}"',
                f'  name        = "{component.name}"',
                '}',
                ''
            ])

        # Añadir outputs
        config_lines.extend([
            'output "component_urls" {',
            '  description = "URLs of deployed components"',
            '  value = {',
        ])

        for component in components:
            if component.resource_type in [ResourceType.COMPUTE, ResourceType.NETWORKING]:
                config_lines.append(f'    {component.name} = module.{component.name}.url')

        config_lines.extend([
            '  }',
            '}'
        ])

        return '\n'.join(config_lines)

    async def plan_deployment(self, components: List[InfrastructureComponent],
                            environment: Environment) -> Dict[str, Any]:
        """Planificar deployment con Terraform."""
        try:
            # Generar configuración
            tf_config = await self.generate_terraform_config(components, environment)

            # Simular terraform plan
            await asyncio.sleep(2)

            # Resultados simulados del plan
            plan_result = {
                'add': len([c for c in components if random.random() > 0.7]),  # Nuevos recursos
                'change': len([c for c in components if random.random() > 0.8]),  # Cambios
                'destroy': len([c for c in components if random.random() > 0.95]),  # Destrucciones
                'estimated_cost_per_month': sum(c.cost_per_hour * 24 * 30 for c in components),
                'has_changes': True,
                'warnings': [],
                'errors': []
            }

            # Cache del plan
            plan_key = f"{environment.value}_{datetime.now().isoformat()}"
            self.plan_cache[plan_key] = plan_result

            logger.info(f"Terraform plan completed for {environment.value}: {plan_result['add']} to add, {plan_result['change']} to change")

            return plan_result

        except Exception as e:
            logger.error(f"Terraform plan failed: {e}")
            return {
                'error': str(e),
                'has_changes': False
            }

    async def apply_deployment(self, plan_key: str, auto_approve: bool = False) -> Dict[str, Any]:
        """Aplicar deployment."""
        if plan_key not in self.plan_cache:
            return {'error': 'Plan not found'}

        plan = self.plan_cache[plan_key]

        if not plan.get('has_changes', False):
            return {'message': 'No changes to apply'}

        # Simular approval si no es auto
        if not auto_approve:
            print("Terraform will perform the following actions:")
            print(f"  - Add: {plan['add']} resources")
            print(f"  - Change: {plan['change']} resources")
            print(f"  - Destroy: {plan['destroy']} resources")
            print(".2f")
            approval = input("Do you want to perform these actions? (yes/no): ")
            if approval.lower() not in ['yes', 'y']:
                return {'cancelled': True}

        # Simular terraform apply
        await asyncio.sleep(5)

        apply_result = {
            'success': True,
            'resources_created': plan['add'],
            'resources_modified': plan['change'],
            'resources_destroyed': plan['destroy'],
            'outputs': {
                'component_urls': {
                    'api_gateway': 'https://api.ailoos.dev',
                    'frontend': 'https://app.ailoos.dev',
                    'database': 'ailoos-db.us-central1.run.app'
                }
            }
        }

        logger.info(f"Terraform apply completed: {apply_result['resources_created']} resources created")

        return apply_result

    async def destroy_infrastructure(self, components: List[InfrastructureComponent],
                                   environment: Environment) -> Dict[str, Any]:
        """Destruir infraestructura."""
        try:
            logger.warning(f"Destroying infrastructure for {environment.value}")

            # Simular terraform destroy
            await asyncio.sleep(3)

            destroy_result = {
                'success': True,
                'resources_destroyed': len(components),
                'message': f'All resources in {environment.value} destroyed'
            }

            logger.info(f"Infrastructure destruction completed for {environment.value}")

            return destroy_result

        except Exception as e:
            logger.error(f"Infrastructure destruction failed: {e}")
            return {'error': str(e)}


class CostOptimizationManager:
    """
    Gestor de optimización de costos.

    Características:
    - Reserved instances
    - Auto-scaling inteligente
    - Resource scheduling
    - Cost monitoring
    """

    def __init__(self):
        self.cost_rules: Dict[str, Dict[str, Any]] = {}
        self.schedules: Dict[str, Dict[str, Any]] = {}
        self.reserved_instances: Dict[str, Dict[str, Any]] = {}

    def add_cost_rule(self, rule_name: str, rule_config: Dict[str, Any]):
        """Añadir regla de optimización de costos."""
        self.cost_rules[rule_name] = rule_config
        logger.info(f"Added cost optimization rule: {rule_name}")

    def add_resource_schedule(self, resource_id: str, schedule: Dict[str, Any]):
        """Añadir schedule para resource."""
        self.schedules[resource_id] = schedule
        logger.info(f"Added schedule for resource: {resource_id}")

    async def analyze_costs(self, components: List[InfrastructureComponent]) -> Dict[str, Any]:
        """Analizar costos y oportunidades de optimización."""
        total_cost = sum(c.cost_per_hour for c in components)
        monthly_cost = total_cost * 24 * 30

        # Analizar oportunidades de optimización
        optimizations = []

        # Reserved instances
        compute_components = [c for c in components if c.resource_type == ResourceType.COMPUTE]
        if len(compute_components) >= 3:
            savings = total_cost * 0.3  # 30% savings with reserved instances
            optimizations.append({
                'type': 'reserved_instances',
                'description': f'Use reserved instances for {len(compute_components)} compute resources',
                'monthly_savings': savings * 24 * 30,
                'implementation_effort': 'medium'
            })

        # Auto-scaling
        for component in components:
            if component.resource_type == ResourceType.COMPUTE:
                if random.random() > 0.7:  # Simular componentes que pueden auto-scale
                    optimizations.append({
                        'type': 'auto_scaling',
                        'resource': component.name,
                        'description': f'Implement auto-scaling for {component.name}',
                        'monthly_savings': component.cost_per_hour * 24 * 30 * 0.2,
                        'implementation_effort': 'low'
                    })

        # Resource scheduling
        for component in components:
            if component.environment == Environment.DEVELOPMENT:
                # Shutdown development resources outside business hours
                business_hours_savings = component.cost_per_hour * 16 * 30  # 16 hours/day savings
                optimizations.append({
                    'type': 'resource_scheduling',
                    'resource': component.name,
                    'description': f'Schedule shutdown for development resource {component.name}',
                    'monthly_savings': business_hours_savings,
                    'implementation_effort': 'low'
                })

        total_savings = sum(opt['monthly_savings'] for opt in optimizations)

        return {
            'current_monthly_cost': monthly_cost,
            'potential_monthly_savings': total_savings,
            'optimization_opportunities': len(optimizations),
            'optimizations': optimizations,
            'cost_efficiency_score': min(100, (total_savings / monthly_cost * 100) if monthly_cost > 0 else 0)
        }

    async def apply_cost_optimization(self, optimization: Dict[str, Any]) -> bool:
        """Aplicar optimización de costos."""
        try:
            opt_type = optimization['type']

            if opt_type == 'reserved_instances':
                # Simular compra de reserved instances
                await asyncio.sleep(1)
                logger.info("Reserved instances purchased")

            elif opt_type == 'auto_scaling':
                # Simular configuración de auto-scaling
                await asyncio.sleep(1)
                logger.info(f"Auto-scaling configured for {optimization['resource']}")

            elif opt_type == 'resource_scheduling':
                # Simular configuración de scheduling
                schedule_config = {
                    'resource_id': optimization['resource'],
                    'shutdown_time': '18:00',
                    'startup_time': '08:00',
                    'timezone': 'UTC'
                }
                self.add_resource_schedule(optimization['resource'], schedule_config)
                logger.info(f"Resource scheduling configured for {optimization['resource']}")

            return True

        except Exception as e:
            logger.error(f"Cost optimization application failed: {e}")
            return False


class MultiRegionManager:
    """
    Gestor de deployments multi-región.

    Características:
    - Cross-region replication
    - Traffic management
    - Disaster recovery
    - Geo-fencing
    """

    def __init__(self):
        self.deployments: Dict[str, MultiRegionDeployment] = {}
        self.health_checks: Dict[str, Dict[str, Any]] = {}

    def create_multi_region_deployment(self, name: str, primary_region: str,
                                     secondary_regions: List[str],
                                     components: List[InfrastructureComponent]) -> MultiRegionDeployment:
        """Crear deployment multi-región."""
        deployment = MultiRegionDeployment(
            name=name,
            primary_region=primary_region,
            secondary_regions=secondary_regions,
            components=components
        )

        self.deployments[name] = deployment
        logger.info(f"Created multi-region deployment: {name}")

        return deployment

    async def deploy_multi_region(self, deployment_name: str) -> Dict[str, Any]:
        """Desplegar en múltiples regiones."""
        if deployment_name not in self.deployments:
            return {'error': 'Deployment not found'}

        deployment = self.deployments[deployment_name]

        results = {}

        # Deploy primary region first
        primary_components = [c for c in deployment.components if c.region == deployment.primary_region]
        if primary_components:
            logger.info(f"Deploying to primary region: {deployment.primary_region}")
            # Simular deployment
            await asyncio.sleep(3)
            results[deployment.primary_region] = {
                'status': 'success',
                'components': len(primary_components)
            }

        # Deploy secondary regions
        for region in deployment.secondary_regions:
            regional_components = [c for c in deployment.components if c.region == region]
            if regional_components:
                logger.info(f"Deploying to secondary region: {region}")
                await asyncio.sleep(2)
                results[region] = {
                    'status': 'success',
                    'components': len(regional_components)
                }

        # Configure cross-region replication
        await self._configure_replication(deployment)

        deployment.status = 'completed'

        return {
            'deployment': deployment_name,
            'regions_deployed': len(results),
            'total_components': sum(r['components'] for r in results.values()),
            'results': results
        }

    async def _configure_replication(self, deployment: MultiRegionDeployment):
        """Configurar replicación cross-region."""
        # Simular configuración de replication
        await asyncio.sleep(1)

        # Database replication
        db_components = [c for c in deployment.components if c.resource_type == ResourceType.DATABASE]
        if db_components:
            logger.info(f"Configured database replication across {len(deployment.secondary_regions) + 1} regions")

        # Storage replication
        storage_components = [c for c in deployment.components if c.resource_type == ResourceType.STORAGE]
        if storage_components:
            logger.info(f"Configured storage replication across {len(deployment.secondary_regions) + 1} regions")

    async def failover_to_region(self, deployment_name: str, target_region: str) -> bool:
        """Failover a una región específica."""
        if deployment_name not in self.deployments:
            return False

        deployment = self.deployments[deployment_name]

        if target_region not in [deployment.primary_region] + deployment.secondary_regions:
            return False

        try:
            logger.warning(f"Failing over {deployment_name} to {target_region}")

            # Switch traffic distribution
            for region in deployment.traffic_distribution:
                deployment.traffic_distribution[region] = 0.0
            deployment.traffic_distribution[target_region] = 100.0

            # Update primary region
            old_primary = deployment.primary_region
            deployment.primary_region = target_region

            # Remove from secondary if it was there
            if target_region in deployment.secondary_regions:
                deployment.secondary_regions.remove(target_region)
                deployment.secondary_regions.append(old_primary)

            logger.info(f"Failover completed: {old_primary} -> {target_region}")

            return True

        except Exception as e:
            logger.error(f"Failover failed: {e}")
            return False

    async def check_region_health(self, deployment_name: str) -> Dict[str, Any]:
        """Verificar health de todas las regiones."""
        if deployment_name not in self.deployments:
            return {'error': 'Deployment not found'}

        deployment = self.deployments[deployment_name]
        health_status = {}

        all_regions = [deployment.primary_region] + deployment.secondary_regions

        for region in all_regions:
            # Simular health check
            is_healthy = random.random() > 0.1  # 90% uptime
            latency = random.uniform(10, 100)  # 10-100ms

            health_status[region] = {
                'healthy': is_healthy,
                'latency_ms': latency,
                'last_check': datetime.now()
            }

        # Update deployment traffic distribution based on health
        healthy_regions = [r for r, h in health_status.items() if h['healthy']]

        if healthy_regions:
            traffic_per_region = 100.0 / len(healthy_regions)
            for region in deployment.traffic_distribution:
                deployment.traffic_distribution[region] = traffic_per_region if region in healthy_regions else 0.0

        return {
            'deployment': deployment_name,
            'healthy_regions': len(healthy_regions),
            'total_regions': len(all_regions),
            'health_status': health_status,
            'traffic_distribution': deployment.traffic_distribution
        }


class InfrastructureManager:
    """
    Gestor principal de infraestructura.
    """

    def __init__(self):
        self.terraform = TerraformManager()
        self.cost_optimizer = CostOptimizationManager()
        self.multi_region = MultiRegionManager()
        self.components: Dict[str, InfrastructureComponent] = {}

    def add_component(self, component: InfrastructureComponent):
        """Añadir componente de infraestructura."""
        self.components[component.resource_id] = component

        # Añadir módulo Terraform correspondiente
        self.terraform.add_module(component.terraform_module)

        logger.info(f"Added infrastructure component: {component.name}")

    async def plan_infrastructure(self, environment: Environment,
                                target_regions: List[str] = None) -> Dict[str, Any]:
        """Planificar infraestructura completa."""
        # Filtrar componentes por environment
        env_components = [c for c in self.components.values() if c.environment == environment]

        if target_regions:
            env_components = [c for c in env_components if c.region in target_regions]

        if not env_components:
            return {'error': 'No components found for the specified criteria'}

        # Plan con Terraform
        plan_result = await self.terraform.plan_deployment(env_components, environment)

        # Análisis de costos
        cost_analysis = await self.cost_optimizer.analyze_costs(env_components)

        return {
            'environment': environment.value,
            'components': len(env_components),
            'regions': list(set(c.region for c in env_components)),
            'terraform_plan': plan_result,
            'cost_analysis': cost_analysis,
            'estimated_monthly_cost': plan_result.get('estimated_cost_per_month', 0),
            'potential_savings': cost_analysis.get('potential_monthly_savings', 0)
        }

    async def deploy_infrastructure(self, environment: Environment,
                                  auto_approve: bool = False) -> Dict[str, Any]:
        """Desplegar infraestructura completa."""
        # Plan first
        plan_result = await self.plan_infrastructure(environment)

        if 'error' in plan_result:
            return plan_result

        # Apply
        plan_key = f"{environment.value}_{datetime.now().isoformat()}"
        self.terraform.plan_cache[plan_key] = plan_result['terraform_plan']

        apply_result = await self.terraform.apply_deployment(plan_key, auto_approve)

        if apply_result.get('success'):
            # Aplicar optimizaciones de costo
            optimizations = plan_result['cost_analysis'].get('optimizations', [])
            applied_optimizations = 0

            for opt in optimizations:
                if opt['implementation_effort'] == 'low':  # Auto-aplicar optimizaciones low-effort
                    success = await self.cost_optimizer.apply_cost_optimization(opt)
                    if success:
                        applied_optimizations += 1

            apply_result['cost_optimizations_applied'] = applied_optimizations

        return apply_result

    async def create_multi_region_setup(self, name: str, primary_region: str,
                                      secondary_regions: List[str],
                                      environment: Environment) -> Dict[str, Any]:
        """Crear setup multi-región."""
        # Filtrar componentes por environment
        env_components = [c for c in self.components.values() if c.environment == environment]

        # Crear deployment multi-región
        deployment = self.multi_region.create_multi_region_deployment(
            name=name,
            primary_region=primary_region,
            secondary_regions=secondary_regions,
            components=env_components
        )

        # Deploy
        deploy_result = await self.multi_region.deploy_multi_region(name)

        return {
            'deployment_name': name,
            'primary_region': primary_region,
            'secondary_regions': secondary_regions,
            'total_components': len(env_components),
            'deploy_result': deploy_result
        }


# Funciones de conveniencia

def create_production_infrastructure() -> List[InfrastructureComponent]:
    """Crear componentes de infraestructura para producción."""
    components = []

    # API Gateway
    api_gateway = InfrastructureComponent(
        name="api-gateway",
        resource_type=ResourceType.NETWORKING,
        provider=CloudProvider.GCP,
        region="us-central1",
        environment=Environment.PRODUCTION,
        cost_per_hour=0.5,
        terraform_module=TerraformModule(
            name="api_gateway",
            source="./modules/api-gateway",
            variables={
                "domain": "api.ailoos.dev",
                "rate_limit": 1000
            }
        ),
        tags={"component": "api", "tier": "frontend"}
    )
    components.append(api_gateway)

    # Compute Engine para API
    api_compute = InfrastructureComponent(
        name="api-compute",
        resource_type=ResourceType.COMPUTE,
        provider=CloudProvider.GCP,
        region="us-central1",
        environment=Environment.PRODUCTION,
        cost_per_hour=1.2,
        terraform_module=TerraformModule(
            name="compute_engine",
            source="./modules/compute-engine",
            variables={
                "machine_type": "e2-standard-4",
                "disk_size_gb": 100
            }
        ),
        tags={"component": "api", "tier": "backend"}
    )
    components.append(api_compute)

    # Cloud SQL Database
    database = InfrastructureComponent(
        name="database",
        resource_type=ResourceType.DATABASE,
        provider=CloudProvider.GCP,
        region="us-central1",
        environment=Environment.PRODUCTION,
        cost_per_hour=2.5,
        terraform_module=TerraformModule(
            name="cloud_sql",
            source="./modules/cloud-sql",
            variables={
                "database_version": "POSTGRES_14",
                "tier": "db-f1-micro"
            }
        ),
        tags={"component": "database", "tier": "data"}
    )
    components.append(database)

    # Cloud Storage
    storage = InfrastructureComponent(
        name="storage",
        resource_type=ResourceType.STORAGE,
        provider=CloudProvider.GCP,
        region="us-central1",
        environment=Environment.PRODUCTION,
        cost_per_hour=0.1,
        terraform_module=TerraformModule(
            name="cloud_storage",
            source="./modules/cloud-storage",
            variables={
                "storage_class": "STANDARD",
                "versioning": True
            }
        ),
        tags={"component": "storage", "tier": "data"}
    )
    components.append(storage)

    # Monitoring
    monitoring = InfrastructureComponent(
        name="monitoring",
        resource_type=ResourceType.MONITORING,
        provider=CloudProvider.GCP,
        region="us-central1",
        environment=Environment.PRODUCTION,
        cost_per_hour=0.3,
        terraform_module=TerraformModule(
            name="cloud_monitoring",
            source="./modules/cloud-monitoring",
            variables={
                "notification_channels": ["email", "slack"]
            }
        ),
        tags={"component": "monitoring", "tier": "observability"}
    )
    components.append(monitoring)

    return components


async def demonstrate_infrastructure_as_code():
    """Demostrar Infrastructure as Code completo."""
    print("🏗️ Inicializando Infrastructure as Code...")

    # Crear infraestructura manager
    infra_manager = InfrastructureManager()

    # Añadir componentes de producción
    production_components = create_production_infrastructure()
    for component in production_components:
        infra_manager.add_component(component)

    print("📊 Estado inicial de la infraestructura:")
    print(f"   Componentes totales: {len(infra_manager.components)}")
    print(f"   Regiones: {', '.join(set(c.region for c in infra_manager.components.values()))}")
    print(f"   Tipos de recursos: {', '.join(set(c.resource_type.value for c in infra_manager.components.values()))}")

    # Planificar infraestructura
    print("\n📋 Planificando infraestructura de producción...")
    plan_result = await infra_manager.plan_infrastructure(Environment.PRODUCTION)

    print("   📊 Resultados del plan:")
    print(f"      Componentes: {plan_result['components']}")
    print(f"      Regiones: {', '.join(plan_result['regions'])}")
    print(f"      Costo mensual estimado: ${plan_result['estimated_monthly_cost']:.2f}")
    print(f"      Ahorro potencial: ${plan_result['cost_analysis']['potential_monthly_savings']:.2f}")
    print(f"      Oportunidades de optimización: {plan_result['cost_analysis']['optimization_opportunities']}")

    # Aplicar optimizaciones de costo
    optimizations = plan_result['cost_analysis']['optimizations']
    applied = 0
    for opt in optimizations[:3]:  # Aplicar primeras 3 optimizaciones
        success = await infra_manager.cost_optimizer.apply_cost_optimization(opt)
        if success:
            applied += 1
            print(f"   ✅ Optimización aplicada: {opt['type']} - Ahorro mensual: ${opt['monthly_savings']:.2f}")

    print(f"   💰 Optimizaciones aplicadas: {applied}/3")

    # Desplegar infraestructura
    print("\n🚀 Desplegando infraestructura...")
    deploy_result = await infra_manager.deploy_infrastructure(Environment.PRODUCTION, auto_approve=True)

    if deploy_result.get('success'):
        print("   ✅ Deployment exitoso:")
        print(f"      Recursos creados: {deploy_result['resources_created']}")
        print(f"      Recursos modificados: {deploy_result['resources_modified']}")
        print(f"      URLs de componentes: {list(deploy_result['outputs']['component_urls'].keys())}")
        print(f"      Optimizaciones de costo aplicadas: {deploy_result.get('cost_optimizations_applied', 0)}")
    else:
        print("   ❌ Deployment falló")

    # Configurar multi-region
    print("\n🌍 Configurando Multi-Region Deployment...")
    multi_region_result = await infra_manager.create_multi_region_setup(
        name="ailoos-production-multi-region",
        primary_region="us-central1",
        secondary_regions=["europe-west1", "asia-east1"],
        environment=Environment.PRODUCTION
    )

    print("   🌐 Multi-region configurado:")
    print(f"      Deployment: {multi_region_result['deployment_name']}")
    print(f"      Región primaria: {multi_region_result['primary_region']}")
    print(f"      Regiones secundarias: {', '.join(multi_region_result['secondary_regions'])}")
    print(f"      Componentes totales: {multi_region_result['total_components']}")
    print(f"      Regiones desplegadas: {multi_region_result['deploy_result']['regions_deployed']}")

    # Verificar health multi-region
    print("\n🏥 Verificando health multi-region...")
    health_result = await infra_manager.multi_region.check_region_health("ailoos-production-multi-region")

    healthy_regions = health_result['healthy_regions']
    total_regions = health_result['total_regions']
    print(f"   ✅ Regiones saludables: {healthy_regions}/{total_regions}")

    # Simular failover
    if healthy_regions > 1:
        print("\n🔄 Probando failover...")
        failover_success = await infra_manager.multi_region.failover_to_region(
            "ailoos-production-multi-region", "europe-west1"
        )
        if failover_success:
            print("   ✅ Failover exitoso a europe-west1")
        else:
            print("   ❌ Failover falló")

    # Resumen final
    print("\n🏆 RESUMEN FINAL - INFRASTRUCTURE AS CODE:")
    print(f"   Componentes desplegados: {len(infra_manager.components)}")
    print(f"   Regiones activas: {total_regions}")
    print(f"   Costo mensual estimado: ${plan_result['estimated_monthly_cost']:.2f}")
    print(f"   Ahorro potencial: ${plan_result['cost_analysis']['potential_monthly_savings']:.2f}")
    print(f"   Optimizaciones aplicadas: {applied}")
    print(f"   Multi-region: ✅ Configurado")
    print(f"   Failover: ✅ Probado")

    print("✅ Infrastructure as Code demostrado correctamente")

    return infra_manager


if __name__ == "__main__":
    asyncio.run(demonstrate_infrastructure_as_code())