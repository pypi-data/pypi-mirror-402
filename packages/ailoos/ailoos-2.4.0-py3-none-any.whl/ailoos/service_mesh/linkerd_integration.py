import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class LinkerdServiceProfile:
    name: str
    namespace: str = "default"
    routes: List[Dict[str, Any]] = None

@dataclass
class LinkerdTrafficSplit:
    name: str
    namespace: str = "default"
    service: str = None
    backends: List[Dict[str, str]] = None

@dataclass
class LinkerdAuthorizationPolicy:
    name: str
    namespace: str = "default"
    target_ref: Dict[str, str] = None
    required_during_request: Dict[str, Any] = None

class LinkerdIntegration:
    """Complete Linkerd service mesh integration"""

    def __init__(self, linkerd_path: str = "linkerd", kubeconfig: Optional[str] = None):
        self.linkerd_path = linkerd_path
        self.kubeconfig = kubeconfig
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Linkerd control plane"""
        try:
            # Verify linkerd CLI is available and cluster is accessible
            result = await self._run_linkerd_command(["version"])
            if result[0] == 0:
                self._connected = True
                logger.info("Connected to Linkerd control plane")
                return True
            else:
                logger.error("Failed to connect to Linkerd")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Linkerd: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Linkerd"""
        self._connected = False
        logger.info("Disconnected from Linkerd")

    async def install_linkerd(self, namespace: str = "linkerd") -> bool:
        """Install Linkerd using linkerd CLI"""
        try:
            cmd = ["install", "--linkerd-namespace", namespace]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                # Apply the installation
                apply_result = await self._run_command(["kubectl", "apply", "-f", "-"], input_data=result[1])
                if apply_result[0] == 0:
                    logger.info(f"Linkerd installed in namespace: {namespace}")
                    return True
                else:
                    logger.error("Failed to apply Linkerd installation")
                    return False
            else:
                logger.error("Failed to generate Linkerd installation")
                return False
        except Exception as e:
            logger.error(f"Error installing Linkerd: {e}")
            return False

    async def inject_deployment(self, deployment_name: str, namespace: str = "default") -> bool:
        """Inject Linkerd proxy into a deployment"""
        try:
            cmd = ["inject", f"{deployment_name}.yaml", "-n", namespace]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                # Apply the injected deployment
                apply_result = await self._run_command(["kubectl", "apply", "-f", "-"], input_data=result[1])
                if apply_result[0] == 0:
                    logger.info(f"Injected Linkerd proxy into deployment: {deployment_name}")
                    return True
                else:
                    return False
            else:
                logger.error(f"Failed to inject deployment: {deployment_name}")
                return False
        except Exception as e:
            logger.error(f"Error injecting deployment: {e}")
            return False

    async def create_service_profile(self, profile: LinkerdServiceProfile) -> bool:
        """Create or update a ServiceProfile"""
        try:
            sp_spec = {
                "apiVersion": "linkerd.io/v1alpha2",
                "kind": "ServiceProfile",
                "metadata": {
                    "name": profile.name,
                    "namespace": profile.namespace
                },
                "spec": {}
            }

            if profile.routes:
                sp_spec["spec"]["routes"] = profile.routes

            result = await self._apply_yaml(sp_spec)
            if result:
                logger.info(f"Created ServiceProfile: {profile.name}")
                return True
            else:
                logger.error(f"Failed to create ServiceProfile: {profile.name}")
                return False
        except Exception as e:
            logger.error(f"Error creating ServiceProfile: {e}")
            return False

    async def create_traffic_split(self, split: LinkerdTrafficSplit) -> bool:
        """Create or update a TrafficSplit"""
        try:
            ts_spec = {
                "apiVersion": "split.smi-spec.io/v1alpha1",
                "kind": "TrafficSplit",
                "metadata": {
                    "name": split.name,
                    "namespace": split.namespace
                },
                "spec": {}
            }

            if split.service:
                ts_spec["spec"]["service"] = split.service
            if split.backends:
                ts_spec["spec"]["backends"] = split.backends

            result = await self._apply_yaml(ts_spec)
            if result:
                logger.info(f"Created TrafficSplit: {split.name}")
                return True
            else:
                logger.error(f"Failed to create TrafficSplit: {split.name}")
                return False
        except Exception as e:
            logger.error(f"Error creating TrafficSplit: {e}")
            return False

    async def create_authorization_policy(self, policy: LinkerdAuthorizationPolicy) -> bool:
        """Create or update an AuthorizationPolicy"""
        try:
            ap_spec = {
                "apiVersion": "policy.linkerd.io/v1beta1",
                "kind": "AuthorizationPolicy",
                "metadata": {
                    "name": policy.name,
                    "namespace": policy.namespace
                },
                "spec": {}
            }

            if policy.target_ref:
                ap_spec["spec"]["targetRef"] = policy.target_ref
            if policy.required_during_request:
                ap_spec["spec"]["requiredDuringRequest"] = policy.required_during_request

            result = await self._apply_yaml(ap_spec)
            if result:
                logger.info(f"Created AuthorizationPolicy: {policy.name}")
                return True
            else:
                logger.error(f"Failed to create AuthorizationPolicy: {policy.name}")
                return False
        except Exception as e:
            logger.error(f"Error creating AuthorizationPolicy: {e}")
            return False

    async def get_proxy_status(self) -> Optional[Dict[str, Any]]:
        """Get Linkerd proxy status"""
        try:
            cmd = ["check", "--proxy"]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                return {"status": "healthy", "output": result[1]}
            else:
                return {"status": "unhealthy", "output": result[1]}
        except Exception as e:
            logger.error(f"Error getting proxy status: {e}")
            return None

    async def get_data_plane_status(self) -> Optional[Dict[str, Any]]:
        """Get Linkerd data plane status"""
        try:
            cmd = ["check", "--linkerd-cni-enabled"]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                return {"status": "healthy", "output": result[1]}
            else:
                return {"status": "unhealthy", "output": result[1]}
        except Exception as e:
            logger.error(f"Error getting data plane status: {e}")
            return None

    async def get_traffic_metrics(self, service_name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get traffic metrics for a service"""
        try:
            cmd = ["stat", "deploy", "-n", namespace]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                # Parse the output to extract metrics for the specific service
                return {
                    "service": service_name,
                    "namespace": namespace,
                    "metrics": result[1]
                }
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting traffic metrics: {e}")
            return None

    async def enable_viz(self, namespace: str = "linkerd-viz") -> bool:
        """Install Linkerd Viz for observability"""
        try:
            cmd = ["viz", "install"]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                apply_result = await self._run_command(["kubectl", "apply", "-f", "-"], input_data=result[1])
                if apply_result[0] == 0:
                    logger.info("Linkerd Viz installed")
                    return True
                else:
                    return False
            else:
                logger.error("Failed to install Linkerd Viz")
                return False
        except Exception as e:
            logger.error(f"Error installing Linkerd Viz: {e}")
            return False

    async def get_viz_dashboard_url(self) -> Optional[str]:
        """Get Linkerd Viz dashboard URL"""
        try:
            cmd = ["viz", "dashboard", "--show-url"]
            result = await self._run_linkerd_command(cmd)
            if result[0] == 0:
                # Extract URL from output
                return "http://localhost:50750"  # Default viz dashboard URL
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting viz dashboard URL: {e}")
            return None

    async def _run_linkerd_command(self, args: List[str]) -> Tuple[int, str]:
        """Run a linkerd command"""
        import subprocess

        cmd = [self.linkerd_path] + args
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
            logger.error(f"Error running linkerd command: {e}")
            return -1, ""

    async def _run_command(self, cmd: List[str], input_data: str = None) -> Tuple[int, str]:
        """Run a generic command"""
        import subprocess

        try:
            if input_data:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate(input=input_data.encode())
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
            return process.returncode, stdout.decode()
        except Exception as e:
            logger.error(f"Error running command: {e}")
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