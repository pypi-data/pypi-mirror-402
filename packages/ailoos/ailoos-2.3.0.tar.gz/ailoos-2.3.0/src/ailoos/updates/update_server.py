"""
Update server for distributing Ailoos updates.
Handles update metadata, file serving, and compatibility checking.
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..utils.logging import AiloosLogger


@dataclass
class UpdateMetadata:
    """Metadata for an update package."""
    component: str
    version: str
    filename: str
    checksum: str
    size: int
    release_date: datetime
    release_notes: str
    priority: str
    requires_restart: bool
    compatible_versions: List[str]
    dependencies: List[str]
    platform_requirements: Dict[str, Any]


class UpdateServer:
    """HTTP server for serving Ailoos updates."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Server configuration
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 8080)
        self.updates_dir = Path(config.get('updates_dir', '/var/lib/ailoos/updates'))
        self.metadata_file = self.updates_dir / 'metadata.json'

        # Update data
        self.updates: Dict[str, UpdateMetadata] = {}
        self.app = web.Application()
        self.runner = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_post('/api/v1/updates/check', self.handle_update_check)
        self.app.router.add_get('/api/v1/updates/{component}/{version}', self.handle_update_download)
        self.app.router.add_get('/api/v1/updates/metadata', self.handle_metadata)
        self.app.router.add_post('/api/v1/updates/publish', self.handle_publish_update)
        self.app.router.add_get('/health', self.handle_health)

    async def start(self):
        """Start the update server."""
        self.logger.info(f"Starting update server on {self.host}:{self.port}")

        # Load existing metadata
        await self._load_metadata()

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        self.logger.info("Update server started successfully")

    async def stop(self):
        """Stop the update server."""
        if self.runner:
            await self.runner.cleanup()
        self.logger.info("Update server stopped")

    async def _load_metadata(self):
        """Load update metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)

                for update_data in data.get('updates', []):
                    # Convert release_date string back to datetime
                    if 'release_date' in update_data:
                        update_data['release_date'] = datetime.fromisoformat(update_data['release_date'])

                    update = UpdateMetadata(**update_data)
                    self.updates[f"{update.component}_{update.version}"] = update

                self.logger.info(f"Loaded {len(self.updates)} update metadata entries")

            except Exception as e:
                self.logger.error(f"Error loading metadata: {e}")

    async def _save_metadata(self):
        """Save update metadata to disk."""
        try:
            # Convert datetime objects to strings for JSON serialization
            data = {
                'updates': [
                    {
                        **vars(update),
                        'release_date': update.release_date.isoformat()
                    }
                    for update in self.updates.values()
                ],
                'last_updated': datetime.now().isoformat()
            }

            self.updates_dir.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")

    async def handle_update_check(self, request: web.Request) -> web.Response:
        """Handle update check requests."""
        try:
            data = await request.json()
            component_type = data.get('component_type')
            current_versions = data.get('current_versions', {})
            platform_info = data.get('platform', {})

            available_updates = []

            for update in self.updates.values():
                # Check if this update is applicable
                if self._is_update_applicable(update, component_type, current_versions, platform_info):
                    available_updates.append({
                        'component': update.component,
                        'version': update.version,
                        'url': f"/api/v1/updates/{update.component}/{update.version}",
                        'checksum': update.checksum,
                        'size': update.size,
                        'release_notes': update.release_notes,
                        'priority': update.priority,
                        'requires_restart': update.requires_restart,
                        'compatible_versions': update.compatible_versions
                    })

            return web.json_response({
                'status': 'success',
                'updates': available_updates,
                'server_time': datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error handling update check: {e}")
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    def _is_update_applicable(
        self,
        update: UpdateMetadata,
        component_type: str,
        current_versions: Dict[str, str],
        platform_info: Dict[str, Any]
    ) -> bool:
        """Check if an update is applicable for the requesting client."""
        # Check component type
        if component_type not in ['coordinator', 'node', 'dashboard', 'all']:
            return False

        # Check current version
        current_version = current_versions.get(update.component)
        if current_version and current_version >= update.version:
            return False

        # Check platform compatibility
        if not self._check_platform_compatibility(update, platform_info):
            return False

        # Check version compatibility
        if update.compatible_versions and current_version:
            if not any(self._version_matches(current_version, compat) for compat in update.compatible_versions):
                return False

        return True

    def _check_platform_compatibility(self, update: UpdateMetadata, platform_info: Dict[str, Any]) -> bool:
        """Check if update is compatible with client platform."""
        requirements = update.platform_requirements

        # Check OS
        if 'os' in requirements:
            if platform_info.get('os') not in requirements['os']:
                return False

        # Check architecture
        if 'arch' in requirements:
            if platform_info.get('arch') not in requirements['arch']:
                return False

        # Check Python version
        if 'python_version' in requirements:
            client_python = tuple(platform_info.get('python_version', []))
            required_python = requirements['python_version']
            if isinstance(required_python, list):
                if client_python not in [tuple(v) for v in required_python]:
                    return False
            elif client_python < tuple(required_python.get('min', [])):
                return False

        return True

    def _version_matches(self, version: str, pattern: str) -> bool:
        """Check if version matches a pattern (supports wildcards)."""
        if pattern.endswith('.*'):
            return version.startswith(pattern[:-2])
        return version == pattern

    async def handle_update_download(self, request: web.Request) -> web.Response:
        """Handle update file downloads."""
        try:
            component = request.match_info['component']
            version = request.match_info['version']

            update_key = f"{component}_{version}"
            if update_key not in self.updates:
                return web.json_response(
                    {'status': 'error', 'message': 'Update not found'},
                    status=404
                )

            update = self.updates[update_key]
            update_file = self.updates_dir / update.filename

            if not update_file.exists():
                return web.json_response(
                    {'status': 'error', 'message': 'Update file not found'},
                    status=404
                )

            # Stream file with proper headers
            response = web.StreamResponse()
            response.headers['Content-Type'] = 'application/octet-stream'
            response.headers['Content-Length'] = str(update.size)
            response.headers['Content-Disposition'] = f'attachment; filename="{update.filename}"'
            response.headers['X-Checksum-SHA256'] = update.checksum

            await response.prepare(request)

            # Stream file in chunks
            with open(update_file, 'rb') as f:
                chunk = f.read(8192)
                while chunk:
                    await response.write(chunk)
                    chunk = f.read(8192)

            return response

        except Exception as e:
            self.logger.error(f"Error handling update download: {e}")
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    async def handle_metadata(self, request: web.Request) -> web.Response:
        """Handle metadata requests."""
        try:
            metadata = {
                'server_version': '1.0.0',
                'total_updates': len(self.updates),
                'last_updated': datetime.now().isoformat(),
                'updates': [
                    {
                        'component': update.component,
                        'version': update.version,
                        'release_date': update.release_date.isoformat(),
                        'size': update.size,
                        'priority': update.priority
                    }
                    for update in self.updates.values()
                ]
            }

            return web.json_response(metadata)

        except Exception as e:
            self.logger.error(f"Error handling metadata request: {e}")
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    async def handle_publish_update(self, request: web.Request) -> web.Response:
        """Handle update publishing (admin endpoint)."""
        try:
            # In a real implementation, this would require authentication
            data = await request.json()

            # Validate required fields
            required_fields = [
                'component', 'version', 'filename', 'checksum', 'size',
                'release_notes', 'priority', 'requires_restart'
            ]

            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {'status': 'error', 'message': f'Missing required field: {field}'},
                        status=400
                    )

            # Create update metadata
            update = UpdateMetadata(
                component=data['component'],
                version=data['version'],
                filename=data['filename'],
                checksum=data['checksum'],
                size=data['size'],
                release_date=datetime.now(),
                release_notes=data['release_notes'],
                priority=data['priority'],
                requires_restart=data.get('requires_restart', False),
                compatible_versions=data.get('compatible_versions', []),
                dependencies=data.get('dependencies', []),
                platform_requirements=data.get('platform_requirements', {})
            )

            # Store update
            update_key = f"{update.component}_{update.version}"
            self.updates[update_key] = update

            # Save metadata
            await self._save_metadata()

            self.logger.info(f"Published update: {update.component} v{update.version}")

            return web.json_response({
                'status': 'success',
                'message': f'Update {update.component} v{update.version} published successfully'
            })

        except Exception as e:
            self.logger.error(f"Error publishing update: {e}")
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )

    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'updates_available': len(self.updates)
        })

    async def publish_update(
        self,
        component: str,
        version: str,
        file_path: Path,
        release_notes: str,
        priority: str = 'medium',
        requires_restart: bool = False,
        compatible_versions: List[str] = None,
        platform_requirements: Dict[str, Any] = None
    ) -> bool:
        """Publish a new update."""
        try:
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)

            # Get file size
            size = file_path.stat().st_size

            # Copy file to updates directory
            filename = f"{component}_{version}.update"
            update_file = self.updates_dir / filename
            self.updates_dir.mkdir(parents=True, exist_ok=True)
            update_file.write_bytes(file_path.read_bytes())

            # Create metadata
            update = UpdateMetadata(
                component=component,
                version=version,
                filename=filename,
                checksum=checksum,
                size=size,
                release_date=datetime.now(),
                release_notes=release_notes,
                priority=priority,
                requires_restart=requires_restart,
                compatible_versions=compatible_versions or [],
                dependencies=[],
                platform_requirements=platform_requirements or {}
            )

            # Store update
            update_key = f"{component}_{version}"
            self.updates[update_key] = update

            # Save metadata
            await self._save_metadata()

            self.logger.info(f"Published update: {component} v{version}")
            return True

        except Exception as e:
            self.logger.error(f"Error publishing update: {e}")
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_update_info(self, component: str, version: str) -> Optional[UpdateMetadata]:
        """Get information about a specific update."""
        return self.updates.get(f"{component}_{version}")

    def list_updates(self, component: str = None) -> List[UpdateMetadata]:
        """List available updates, optionally filtered by component."""
        updates = list(self.updates.values())
        if component:
            updates = [u for u in updates if u.component == component]
        return sorted(updates, key=lambda u: u.release_date, reverse=True)


# CLI interface for update server
async def main():
    """Main entry point for update server."""
    import argparse

    parser = argparse.ArgumentParser(description="Ailoos Update Server")
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--updates-dir', default='/var/lib/ailoos/updates', help='Updates directory')

    args = parser.parse_args()

    config = {
        'host': args.host,
        'port': args.port,
        'updates_dir': args.updates_dir
    }

    server = UpdateServer(config)

    try:
        await server.start()

        # Keep server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down update server...")
    finally:
        await server.stop()


if __name__ == '__main__':
    asyncio.run(main())