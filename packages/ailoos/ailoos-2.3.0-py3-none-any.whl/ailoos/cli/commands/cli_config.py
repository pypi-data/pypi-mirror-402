"""
Configuration management commands for Ailoos CLI.
Handles settings, preferences, and environment configuration.
"""

import click
import json
import os
from pathlib import Path
from typing import Dict, Any
import yaml


@click.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option('--global', 'is_global', is_flag=True, help='Use global configuration')
@click.option('--local', is_flag=True, help='Use local configuration (default)')
def show(is_global, local):
    """Show current configuration."""
    config_file = _get_config_file(is_global)

    if not config_file.exists():
        click.echo(f"❌ Configuration file not found: {config_file}")
        click.echo("💡 Use 'ailoos config init' to create a new configuration")
        return

    try:
        with open(config_file, 'r') as f:
            if config_file.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        click.echo(f"⚙️  Configuration ({'global' if is_global else 'local'}):")
        click.echo(f"📁 File: {config_file}")
        click.echo("=" * 60)

        _display_config(config)

    except Exception as e:
        click.echo(f"❌ Error reading configuration: {e}")
        raise click.ClickException(f"Configuration read failed: {e}")


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--global', 'is_global', is_flag=True, help='Set in global configuration')
def set(key, value, is_global):
    """Set a configuration value."""
    config_file = _get_config_file(is_global)

    # Load existing config
    config = _load_config(config_file)

    # Parse and set value
    parsed_value = _parse_value(value)
    _set_nested_config(config, key.split('.'), parsed_value)

    # Save config
    _save_config(config_file, config)

    click.echo(f"✅ Set {key} = {parsed_value}")
    click.echo(f"📁 Updated: {config_file}")


@config.command()
@click.argument('key')
@click.option('--global', 'is_global', is_flag=True, help='Get from global configuration')
def get(key, is_global):
    """Get a configuration value."""
    config_file = _get_config_file(is_global)
    config = _load_config(config_file)

    try:
        value = _get_nested_config(config, key.split('.'))
        click.echo(f"{key}: {value}")
    except KeyError:
        click.echo(f"❌ Key '{key}' not found in configuration")
        raise click.Abort()


@config.command()
@click.argument('key')
@click.option('--global', 'is_global', is_flag=True, help='Remove from global configuration')
@click.option('--force', is_flag=True, help='Skip confirmation')
def unset(key, is_global, force):
    """Remove a configuration key."""
    if not force:
        if not click.confirm(f"Remove configuration key '{key}'?"):
            return

    config_file = _get_config_file(is_global)
    config = _load_config(config_file)

    try:
        _unset_nested_config(config, key.split('.'))
        _save_config(config_file, config)
        click.echo(f"✅ Removed {key}")
    except KeyError:
        click.echo(f"❌ Key '{key}' not found")
        raise click.Abort()


@config.command()
@click.option('--global', 'is_global', is_flag=True, help='Initialize global config')
@click.option('--template', type=click.Choice(['basic', 'advanced', 'development']),
              default='basic', help='Configuration template')
def init(is_global, template):
    """Initialize a new configuration file."""
    config_file = _get_config_file(is_global)

    if config_file.exists():
        if not click.confirm(f"Configuration file already exists. Overwrite {config_file}?"):
            return

    # Create template configuration
    config = _create_template_config(template)

    # Save configuration
    _save_config(config_file, config)

    click.echo(f"✅ Initialized {'global' if is_global else 'local'} configuration")
    click.echo(f"📁 Created: {config_file}")
    click.echo(f"📋 Template: {template}")


@config.command()
@click.argument('source')
@click.argument('destination')
@click.option('--force', is_flag=True, help='Overwrite destination')
def copy(source, destination, force):
    """Copy configuration between files."""
    src_file = Path(source)
    dst_file = Path(destination)

    if not src_file.exists():
        click.echo(f"❌ Source file not found: {src_file}")
        raise click.Abort()

    if dst_file.exists() and not force:
        if not click.confirm(f"Destination file exists. Overwrite {dst_file}?"):
            return

    try:
        # Copy file
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        dst_file.write_text(src_file.read_text())

        click.echo(f"✅ Copied configuration")
        click.echo(f"📁 From: {src_file}")
        click.echo(f"📁 To: {dst_file}")

    except Exception as e:
        click.echo(f"❌ Copy failed: {e}")
        raise click.ClickException(f"Configuration copy failed: {e}")


@config.command()
@click.option('--global', 'is_global', is_flag=True, help='Validate global config')
@click.option('--strict', is_flag=True, help='Strict validation (fail on warnings)')
def validate(is_global, strict):
    """Validate configuration file."""
    config_file = _get_config_file(is_global)

    if not config_file.exists():
        click.echo(f"❌ Configuration file not found: {config_file}")
        raise click.Abort()

    try:
        config = _load_config(config_file)

        # Validate configuration
        errors, warnings = _validate_config(config)

        if errors:
            click.echo("❌ Configuration validation failed:")
            for error in errors:
                click.echo(f"   • {error}")
            raise click.Abort()

        if warnings and (strict or click.confirm("Show warnings?")):
            click.echo("⚠️  Configuration warnings:")
            for warning in warnings:
                click.echo(f"   • {warning}")

        click.echo("✅ Configuration is valid")

    except Exception as e:
        click.echo(f"❌ Validation error: {e}")
        raise click.ClickException(f"Configuration validation failed: {e}")


@config.command()
@click.argument('backup_file')
@click.option('--global', 'is_global', is_flag=True, help='Backup global config')
def backup(backup_file, is_global):
    """Create a backup of the configuration."""
    config_file = _get_config_file(is_global)
    backup_path = Path(backup_file)

    if not config_file.exists():
        click.echo(f"❌ Configuration file not found: {config_file}")
        raise click.Abort()

    try:
        # Create backup
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(config_file.read_text())

        click.echo(f"✅ Configuration backed up")
        click.echo(f"📁 Original: {config_file}")
        click.echo(f"💾 Backup: {backup_path}")

    except Exception as e:
        click.echo(f"❌ Backup failed: {e}")
        raise click.ClickException(f"Configuration backup failed: {e}")


@config.command()
@click.argument('backup_file')
@click.option('--global', 'is_global', is_flag=True, help='Restore global config')
@click.option('--force', is_flag=True, help='Overwrite existing config')
def restore(backup_file, is_global, force):
    """Restore configuration from backup."""
    config_file = _get_config_file(is_global)
    backup_path = Path(backup_file)

    if not backup_path.exists():
        click.echo(f"❌ Backup file not found: {backup_path}")
        raise click.Abort()

    if config_file.exists() and not force:
        if not click.confirm(f"Configuration file exists. Overwrite {config_file}?"):
            return

    try:
        # Restore backup
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(backup_path.read_text())

        click.echo(f"✅ Configuration restored")
        click.echo(f"💾 From backup: {backup_path}")
        click.echo(f"📁 To: {config_file}")

    except Exception as e:
        click.echo(f"❌ Restore failed: {e}")
        raise click.ClickException(f"Configuration restore failed: {e}")


@config.command()
@click.option('--global', 'is_global', is_flag=True, help='Migrate global config')
def migrate(is_global):
    """Migrate configuration to latest format."""
    config_file = _get_config_file(is_global)

    if not config_file.exists():
        click.echo(f"❌ Configuration file not found: {config_file}")
        raise click.Abort()

    try:
        config = _load_config(config_file)

        # Apply migrations
        migrated_config, changes = _migrate_config(config)

        if changes:
            # Save migrated config
            _save_config(config_file, migrated_config)

            click.echo("✅ Configuration migrated")
            click.echo("📋 Changes applied:")
            for change in changes:
                click.echo(f"   • {change}")
        else:
            click.echo("ℹ️  Configuration already up to date")

    except Exception as e:
        click.echo(f"❌ Migration failed: {e}")
        raise click.ClickException(f"Configuration migration failed: {e}")


# Helper functions

def _get_config_file(is_global: bool) -> Path:
    """Get the configuration file path."""
    if is_global:
        # Global config in user home
        config_dir = Path.home() / '.ailoos'
        config_dir.mkdir(exist_ok=True)
        return config_dir / 'config.yaml'
    else:
        # Local config in current directory
        return Path('./ailoos.yaml')


def _load_config(config_file: Path) -> Dict[str, Any]:
    """Load configuration from file."""
    if not config_file.exists():
        return {}

    with open(config_file, 'r', encoding='utf-8') as f:
        if config_file.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f) or {}
        else:
            return json.load(f) or {}


def _save_config(config_file: Path, config: Dict[str, Any]):
    """Save configuration to file."""
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w', encoding='utf-8') as f:
        if config_file.suffix in ['.yaml', '.yml']:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        else:
            json.dump(config, f, indent=2, ensure_ascii=False)


def _parse_value(value: str) -> Any:
    """Parse string value to appropriate type."""
    # Try to parse as JSON first
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    # Try to parse as boolean
    if value.lower() in ['true', 'false']:
        return value.lower() == 'true'

    # Try to parse as number
    try:
        # Check if it's an int
        if '.' not in value:
            return int(value)
        else:
            return float(value)
    except ValueError:
        pass

    # Return as string
    return value


def _set_nested_config(config: Dict[str, Any], keys: list, value: Any):
    """Set a nested configuration value."""
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def _get_nested_config(config: Dict[str, Any], keys: list) -> Any:
    """Get a nested configuration value."""
    current = config
    for key in keys:
        current = current[key]
    return current


def _unset_nested_config(config: Dict[str, Any], keys: list):
    """Remove a nested configuration key."""
    current = config
    for key in keys[:-1]:
        current = current[key]
    del current[keys[-1]]


def _display_config(config: Dict[str, Any], prefix: str = ""):
    """Display configuration in a readable format."""
    for key, value in config.items():
        if isinstance(value, dict):
            click.echo(f"{prefix}{key}:")
            _display_config(value, prefix + "  ")
        else:
            click.echo(f"{prefix}{key}: {value}")


def _create_template_config(template: str) -> Dict[str, Any]:
    """Create a template configuration."""
    base_config = {
        'version': '1.0',
        'node': {
            'id': None,  # Will be set when node starts
            'coordinator_url': 'http://localhost:5001',
            'data_dir': './data',
            'models_dir': './models',
            'log_level': 'INFO'
        },
        'federated': {
            'default_model': 'tiny-mlp',
            'batch_size': 32,
            'learning_rate': 0.001,
            'local_epochs': 1,
            'max_rounds': 10
        },
        'hardware': {
            'gpu_preference': 'auto',
            'cpu_threads': None,
            'memory_limit_gb': None
        },
        'rewards': {
            'auto_claim': True,
            'min_claim_amount': 0.01,
            'wallet_address': None
        }
    }

    if template == 'advanced':
        base_config.update({
            'security': {
                'tls_verify': True,
                'cert_path': './certs',
                'key_path': './keys'
            },
            'monitoring': {
                'metrics_interval': 30,
                'log_retention_days': 30,
                'alert_webhook': None
            },
            'performance': {
                'compression_enabled': True,
                'async_processing': True,
                'cache_size_mb': 512
            }
        })

    elif template == 'development':
        base_config.update({
            'debug': {
                'enabled': True,
                'verbose_logging': True,
                'test_mode': True
            },
            'development': {
                'auto_reload': True,
                'hot_reload': True,
                'debug_server': True
            }
        })

    return base_config


def _validate_config(config: Dict[str, Any]) -> tuple:
    """Validate configuration and return errors and warnings."""
    errors = []
    warnings = []

    # Check required fields
    required_fields = ['version', 'node']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Validate node configuration
    if 'node' in config:
        node_config = config['node']
        if 'coordinator_url' in node_config:
            url = node_config['coordinator_url']
            if not url.startswith(('http://', 'https://')):
                errors.append("coordinator_url must start with http:// or https://")

    # Check for deprecated fields
    deprecated_fields = ['old_field_name']
    for field in deprecated_fields:
        if field in config:
            warnings.append(f"Deprecated field: {field}")

    return errors, warnings


def _migrate_config(config: Dict[str, Any]) -> tuple:
    """Migrate configuration to latest format."""
    changes = []

    # Migration logic for different versions
    current_version = config.get('version', '0.0')

    if current_version == '0.0':
        # Migrate from unversioned to v1.0
        config['version'] = '1.0'
        changes.append("Added version field")

    # Add more migrations as needed

    return config, changes