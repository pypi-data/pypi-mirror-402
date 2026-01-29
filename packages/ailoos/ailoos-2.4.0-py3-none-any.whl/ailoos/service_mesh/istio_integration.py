import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class IstioVirtualService:
    name: str
    namespace: str = "default"
    hosts: List[str] = None
    http_routes: List[Dict[str, Any]] = None
    tcp_routes: List[Dict[str, Any]] = None
    tls_routes: List[Dict[str, Any]] = None

@dataclass
class IstioDestinationRule:
    name: str
    namespace: str = "default"
    host: str = None
    subsets: List[Dict[str, Any]] = None
    traffic_policy: Dict[str, Any] = None

@dataclass
class IstioGateway:
    name: str
    namespace: str = "default"
    selector: Dict[str, str] = None
    servers: List[Dict[str, Any]] = None

class IstioIntegration:
    """Complete Istio service mesh integration"""

    def __init__(self, istioctl_path: str = "istioctl", kubeconfig: Optional[str] = None):
        self.istioctl_path = istioctl_path
        self.kubeconfig = kubeconfig
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Istio control plane"""
        try:
            # Verify istioctl is available and cluster is accessible
            result = await self._run_istioctl_command(["version"])
            if result[0] == 0:
                self._connected = True
                logger.info("Connected to Istio control plane")
                return True
            else:
                logger.error("Failed to connect to Istio")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Istio: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Istio"""
        self._connected = False
        logger.info("Disconnected from Istio")

    async def install_istio(self, profile: str = "default", namespace: str = "istio-system") -> bool:
        """Install Istio using istioctl"""
        try:
            cmd = ["install", "--set", f"profile={profile}", "--set", f"values.global.istioNamespace={namespace}"]
            result = await self._run_istioctl_command(cmd)
            if result[0] == 0:
                logger.info(f"Istio installed with profile: {profile}")
                return True
            else:
                logger.error("Failed to install Istio")
                return False
        except Exception as e:
            logger.error(f"Error installing Istio: {e}")
            return False

    async def create_virtual_service(self, vs: IstioVirtualService) -> bool:
        """Create or update a VirtualService"""
        try:
            vs_spec = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "VirtualService",
                "metadata": {
                    "name": vs.name,
                    "namespace": vs.namespace
                },
                "spec": {}
            }

            if vs.hosts:
                vs_spec["spec"]["hosts"] = vs.hosts
            if vs.http_routes:
                vs_spec["spec"]["http"] = vs.http_routes
            if vs.tcp_routes:
                vs_spec["spec"]["tcp"] = vs.tcp_routes
            if vs.tls_routes:
                vs_spec["spec"]["tls"] = vs.tls_routes

            # Apply the VirtualService
            result = await self._apply_yaml(vs_spec)
            if result:
                logger.info(f"Created VirtualService: {vs.name}")
                return True
            else:
                logger.error(f"Failed to create VirtualService: {vs.name}")
                return False
        except Exception as e:
            logger.error(f"Error creating VirtualService: {e}")
            return False

    async def create_destination_rule(self, dr: IstioDestinationRule) -> bool:
        """Create or update a DestinationRule"""
        try:
            dr_spec = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "DestinationRule",
                "metadata": {
                    "name": dr.name,
                    "namespace": dr.namespace
                },
                "spec": {}
            }

            if dr.host:
                dr_spec["spec"]["host"] = dr.host
            if dr.subsets:
                dr_spec["spec"]["subsets"] = dr.subsets
            if dr.traffic_policy:
                dr_spec["spec"]["trafficPolicy"] = dr.traffic_policy

            result = await self._apply_yaml(dr_spec)
            if result:
                logger.info(f"Created DestinationRule: {dr.name}")
                return True
            else:
                logger.error(f"Failed to create DestinationRule: {dr.name}")
                return False
        except Exception as e:
            logger.error(f"Error creating DestinationRule: {e}")
            return False

    async def create_gateway(self, gateway: IstioGateway) -> bool:
        """Create or update a Gateway"""
        try:
            gw_spec = {
                "apiVersion": "networking.istio.io/v1beta1",
                "kind": "Gateway",
                "metadata": {
                    "name": gateway.name,
                    "namespace": gateway.namespace
                },
                "spec": {}
            }

            if gateway.selector:
                gw_spec["spec"]["selector"] = gateway.selector
            if gateway.servers:
                gw_spec["spec"]["servers"] = gateway.servers

            result = await self._apply_yaml(gw_spec)
            if result:
                logger.info(f"Created Gateway: {gateway.name}")
                return True
            else:
                logger.error(f"Failed to create Gateway: {gateway.name}")
                return False
        except Exception as e:
            logger.error(f"Error creating Gateway: {e}")
            return False

    async def get_proxy_config(self, pod_name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get proxy configuration for a pod"""
        try:
            cmd = ["proxy-config", "all", pod_name, "-n", namespace, "-o", "json"]
            result = await self._run_istioctl_command(cmd)
            if result[0] == 0:
                return json.loads(result[1])
            else:
                logger.error(f"Failed to get proxy config for pod: {pod_name}")
                return None
        except Exception as e:
            logger.error(f"Error getting proxy config: {e}")
            return None

    async def get_mesh_config(self) -> Optional[Dict[str, Any]]:
        """Get Istio mesh configuration"""
        try:
            cmd = ["proxy-status"]
            result = await self._run_istioctl_command(cmd)
            if result[0] == 0:
                # Parse the output to extract mesh config
                return {"status": "connected", "output": result[1]}
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting mesh config: {e}")
            return None

    async def enable_mutual_tls(self, namespace: str = "default") -> bool:
        """Enable mutual TLS for a namespace"""
        try:
            policy = {
                "apiVersion": "security.istio.io/v1beta1",
                "kind": "PeerAuthentication",
                "metadata": {
                    "name": "default",
                    "namespace": namespace
                },
                "spec": {
                    "mtls": {
                        "mode": "STRICT"
                    }
                }
            }
            result = await self._apply_yaml(policy)
            if result:
                logger.info(f"Enabled mTLS for namespace: {namespace}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error enabling mTLS: {e}")
            return False

    async def create_authorization_policy(self, name: str, namespace: str = "default",
                                        rules: List[Dict[str, Any]] = None) -> bool:
        """Create an authorization policy"""
        try:
            policy = {
                "apiVersion": "security.istio.io/v1beta1",
                "kind": "AuthorizationPolicy",
                "metadata": {
                    "name": name,
                    "namespace": namespace
                },
                "spec": {
                    "rules": rules or []
                }
            }
            result = await self._apply_yaml(policy)
            if result:
                logger.info(f"Created authorization policy: {name}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error creating authorization policy: {e}")
            return False

    async def get_traffic_metrics(self, service_name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get traffic metrics for a service"""
        try:
            # This would typically integrate with Prometheus/Kiali
            # For simulation, return mock data
            return {
                "service": service_name,
                "namespace": namespace,
                "request_count": 1500,
                "error_count": 15,
                "latency_p50": 45.2,
                "latency_p95": 120.5,
                "latency_p99": 250.0
            }
        except Exception as e:
            logger.error(f"Error getting traffic metrics: {e}")
            return None

    async def _run_istioctl_command(self, args: List[str]) -> Tuple[int, str]:
        """Run an istioctl command"""
        import subprocess

        cmd = [self.istioctl_path] + args
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode, stdout.decode()
        except Exception as e:
            logger.error(f"Error running istioctl command: {e}")
            return -1, ""

    async def _apply_yaml(self, spec: Dict[str, Any]) -> bool:
        """Apply a YAML specification to Kubernetes"""
        import subprocess
        import tempfile
        import yaml

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(spec, f)
                temp_file = f.name

            cmd = ["kubectl", "apply", "-f", temp_file]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Clean up temp file
            import os
            os.unlink(temp_file)

            if process.returncode == 0:
                return True
            else:
                logger.error(f"Failed to apply YAML: {stderr.decode()}")
                return False
        except Exception as e:
            logger.error(f"Error applying YAML: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected