"""
Model management commands for Ailoos CLI.
Handles model downloading, verification, listing, and management.
"""

import asyncio
import click
import json
import os
from pathlib import Path
from typing import Optional
try:
    from ...models.registry import ModelRegistry, ModelInfo
    from ...utils.logging import AiloosLogger
except ImportError:
    # Fallback for when models are not available
    ModelRegistry = None
    ModelInfo = None
    AiloosLogger = None


@click.group()
def model():
    """Model management commands."""
    pass


@model.command()
@click.option('--remote', is_flag=True, help='List remote models available')
@click.option('--local', is_flag=True, help='List locally downloaded models')
@click.option('--filter', help='Filter by name or type (e.g., "vision", "text")')
@click.option('--category', help='Filter by category (language, medical, biotech, test)')
@click.option('--json', is_flag=True, help='Output in JSON format')
def list(remote, local, filter, category, json):
    """List available models."""
    if remote and local:
        click.echo("❌ Cannot use both --remote and --local")
        raise click.Abort()

    registry = ModelRegistry()

    if remote or (not remote and not local):
        # List remote models from registry
        click.echo("🌐 Fetching available models from repository...")
        registry.refresh_registry()

        models = registry.list_models(category)

        # Apply additional filter if specified
        if filter:
            models = [m for m in models
                     if filter.lower() in m.name.lower()
                     or filter.lower() in m.description.lower()]

        models_data = []
        for model in models:
            models_data.append({
                "name": model.name,
                "version": model.version,
                "status": "available",
                "size_mb": model.size_mb,
                "description": model.description,
                "category": model.category,
                "release_date": model.release_date,
                "downloaded": registry.is_downloaded(model)
            })

    else:
        # List local models
        click.echo("💻 Scanning local models...")
        models_data = []

        downloaded_models = registry.get_downloaded_models()
        for model in downloaded_models:
            model_path = registry.models_dir / f"{model.name.lower().replace(' ', '_')}_v{model.version}.pth"
            models_data.append({
                "name": model.name,
                "version": model.version,
                "status": "downloaded",
                "local_path": str(model_path),
                "size_mb": model.size_mb,
                "last_used": "unknown",  # Could track this in future
                "category": model.category
            })

    if json:
        click.echo(json.dumps({"models": models_data}, indent=2))
    else:
        if remote or (not remote and not local):
            click.echo("📦 Modelos Disponibles en Repositorio")
        else:
            click.echo("💾 Modelos Descargados Localmente")

        click.echo("=" * 90)
        click.echo("<15")
        click.echo("-" * 90)

        for model in models_data:
            if remote or (not remote and not local):
                status_emoji = "✅" if model['status'] == 'available' else "⏳"
                downloaded_indicator = " (Downloaded)" if model.get('downloaded', False) else ""
                click.echo("<15")
            else:
                click.echo("<15")


@model.command()
@click.option('--interactive', '-i', is_flag=True, help='Interactive model selection')
@click.argument('model_name', required=False)
@click.option('--version', help='Specific version to download')
@click.option('--category', help='Filter by category (language, medical, biotech, test)')
def download(interactive, model_name, version, category):
    """Download models from the repository."""
    registry = ModelRegistry()

    if interactive or (not model_name):
        # Interactive mode
        return download_interactive(registry, category)
    else:
        # Direct download mode
        return download_direct(registry, model_name, version)


def download_interactive(registry: ModelRegistry, category: Optional[str] = None):
    """Interactive model download with menu selection."""
    try:
        import questionary
    except ImportError:
        click.echo("❌ Interactive mode requires 'questionary' package")
        click.echo("Install with: pip install questionary")
        raise click.Abort()

    # Refresh registry
    click.echo("🔄 Refreshing model registry...")
    registry.refresh_registry()

    # Get available models
    models = registry.list_models(category)

    if not models:
        click.echo("❌ No models available")
        return

    # Create selection options
    choices = []
    for model in models:
        downloaded = registry.is_downloaded(model)
        status = "✅ Downloaded" if downloaded else "📥 Available"

        choice_text = f"{model.display_name} {model.release_date} {model.size_str} - {status}"
        if model.description:
            choice_text += f"\n   {model.description}"

        choices.append({
            'name': choice_text,
            'value': model,
            'disabled': downloaded  # Disable if already downloaded
        })

    # Show interactive menu
    selected = questionary.checkbox(
        "Select models to download (use space to select, enter to confirm):",
        choices=choices
    ).ask()

    if not selected:
        click.echo("ℹ️  No models selected")
        return

    # Download selected models
    for model in selected:
        click.echo(f"\n📥 Downloading {model.display_name}...")
        model_path = registry.download_model(model)

        if model_path:
            click.echo(f"✅ Successfully downloaded {model.display_name}")
            click.echo(f"📍 Location: {model_path}")
        else:
            click.echo(f"❌ Failed to download {model.display_name}")


def download_direct(registry: ModelRegistry, model_name: str, version: Optional[str] = None):
    """Direct download of a specific model."""
    # Find the model
    models = registry.list_models()
    target_model = None

    for model in models:
        if model.name == model_name and (version is None or model.version == version):
            target_model = model
            break

    if not target_model:
        click.echo(f"❌ Model '{model_name}' v{version or 'latest'} not found")
        # Show available models with similar name
        similar = [m for m in models if model_name.lower() in m.name.lower()]
        if similar:
            click.echo("\n📋 Did you mean:")
            for m in similar[:5]:
                click.echo(f"   • {m.display_name}")
        raise click.Abort()

    # Check if already downloaded
    if registry.is_downloaded(target_model):
        click.echo(f"✅ Model {target_model.display_name} already downloaded")
        return

    # Download the model
    click.echo(f"📥 Downloading {target_model.display_name} ({target_model.size_str})...")
    model_path = registry.download_model(target_model)

    if model_path:
        click.echo(f"✅ Successfully downloaded {target_model.display_name}")
        click.echo(f"📍 Location: {model_path}")
    else:
        click.echo(f"❌ Failed to download {target_model.display_name}")
        raise click.Abort()


@model.command()
@click.argument('model_name')
@click.option('--version', default='latest', help='Model version')
@click.option('--json', is_flag=True, help='Output in JSON format')
def info(model_name, version, json):
    """Show detailed information about a model."""
    click.echo(f"ℹ️  Getting info for model: {model_name}")

    manager = ModelManager()

    # Mock model info - in real implementation this would fetch from API/local
    model_info = {
        "name": model_name,
        "version": version,
        "description": "Modelo de prueba básico para clasificación",
        "parameters": 50000,
        "size_gb": 0.045,
        "capabilities": ["classification"],
        "requirements": {
            "min_memory_gb": 0.5,
            "recommended_gpu": None,
            "python_version": ">=3.8"
        },
        "performance": {
            "accuracy": 0.89,
            "latency_ms": 15,
            "throughput_samples_per_sec": 1000
        },
        "training": {
            "dataset": "MNIST",
            "epochs": 10,
            "batch_size": 32,
            "optimizer": "Adam",
            "learning_rate": 0.001
        },
        "checksum": "sha256:abc123...",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

    if json:
        click.echo(json.dumps(model_info, indent=2))
    else:
        click.echo("📋 Model Information")
        click.echo("=" * 50)
        click.echo(f"🤖 Name: {model_info['name']}")
        click.echo(f"📋 Version: {model_info['version']}")
        click.echo(f"📝 Description: {model_info['description']}")
        click.echo(f"🧠 Parameters: {model_info['parameters']:,}")
        click.echo(f"💾 Size: {model_info['size_gb']} GB")

        click.echo(f"\n🎯 Capabilities:")
        for cap in model_info['capabilities']:
            click.echo(f"   • {cap}")

        click.echo(f"\n⚙️  Requirements:")
        req = model_info['requirements']
        click.echo(f"   RAM: {req['min_memory_gb']} GB minimum")
        if req['recommended_gpu']:
            click.echo(f"   GPU: {req['recommended_gpu']} recommended")
        click.echo(f"   Python: {req['python_version']}")

        click.echo(f"\n📊 Performance:")
        perf = model_info['performance']
        click.echo(f"   Accuracy: {perf['accuracy']:.2%}")
        click.echo(f"   Latency: {perf['latency_ms']}ms")
        click.echo(f"   Throughput: {perf['throughput_samples_per_sec']} samples/sec")


@model.command()
@click.argument('model_name')
@click.option('--version', default='latest', help='Model version')
@click.option('--force', is_flag=True, help='Skip confirmation')
def remove(model_name, version, force):
    """Remove a locally downloaded model."""
    if not force:
        if not click.confirm(f"Are you sure you want to remove model '{model_name}'?"):
            return

    click.echo(f"🗑️  Removing model: {model_name} v{version}")

    manager = ModelManager()

    try:
        success = manager.remove_model(model_name, version)
        if success:
            click.echo("✅ Model removed successfully")
        else:
            click.echo("❌ Model not found or removal failed")
            raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Removal error: {e}")
        raise click.ClickException(f"Model removal failed: {e}")


@model.command()
@click.argument('model_name')
@click.option('--version', default='latest', help='Model version')
def verify(model_name, version):
    """Verify integrity of a downloaded model."""
    click.echo(f"🔐 Verifying model: {model_name} v{version}")

    manager = ModelManager()

    try:
        is_valid = manager.verify_model(model_name, version)
        if is_valid:
            click.echo("✅ Model integrity verified")
            click.echo("🔒 Checksum matches expected value")
        else:
            click.echo("❌ Model integrity check failed")
            click.echo("⚠️  Model may be corrupted - consider re-downloading")
            raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Verification error: {e}")
        raise click.ClickException(f"Model verification failed: {e}")


@model.command()
@click.argument('model_name')
@click.option('--version', default='latest', help='Model version')
@click.option('--data-path', help='Path to test data')
@click.option('--batch-size', default=32, type=int, help='Batch size for testing')
def test(model_name, version, data_path, batch_size):
    """Test a downloaded model with sample data."""
    click.echo(f"🧪 Testing model: {model_name} v{version}")

    if not data_path:
        click.echo("❌ Data path is required for testing")
        raise click.Abort()

    manager = ModelManager()

    try:
        results = manager.test_model(
            model_name=model_name,
            version=version,
            data_path=data_path,
            batch_size=batch_size
        )

        click.echo("✅ Model testing completed")
        click.echo("📊 Results:")
        click.echo(f"   Accuracy: {results['accuracy']:.2%}")
        click.echo(f"   Loss: {results['loss']:.4f}")
        click.echo(f"   Samples tested: {results['samples_tested']}")
        click.echo(f"   Inference time: {results['avg_inference_time']:.2f}ms per sample")

    except Exception as e:
        click.echo(f"❌ Testing error: {e}")
        raise click.ClickException(f"Model testing failed: {e}")


@model.command()
@click.argument('source_model')
@click.argument('target_path')
@click.option('--format', type=click.Choice(['pytorch', 'onnx', 'tensorflow']),
              default='pytorch', help='Export format')
@click.option('--optimize', is_flag=True, help='Apply optimization for inference')
def export(source_model, target_path, format, optimize):
    """Export a model to different formats."""
    click.echo(f"📤 Exporting model: {source_model}")
    click.echo(f"🎯 Format: {format}")
    click.echo(f"📁 Target: {target_path}")

    manager = ModelManager()

    try:
        success = manager.export_model(
            model_name=source_model,
            target_path=target_path,
            format=format,
            optimize=optimize
        )

        if success:
            click.echo("✅ Model exported successfully")
            if optimize:
                click.echo("⚡ Optimizations applied for better inference performance")
        else:
            click.echo("❌ Export failed")
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Export error: {e}")
        raise click.ClickException(f"Model export failed: {e}")


@model.command()
@click.option('--cache-dir', help='Cache directory to clean')
@click.option('--older-than', help='Remove models older than (e.g., "30d", "1w")')
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned without doing it')
def clean(cache_dir, older_than, dry_run):
    """Clean up old or unused model files."""
    click.echo("🧹 Cleaning model cache...")

    if dry_run:
        click.echo("🔍 Dry run mode - no files will be deleted")

    manager = ModelManager()

    try:
        cleaned_info = manager.clean_cache(
            cache_dir=cache_dir,
            older_than=older_than,
            dry_run=dry_run
        )

        if dry_run:
            click.echo("📋 Would clean:")
        else:
            click.echo("✅ Cleaned:")

        click.echo(f"   Models: {cleaned_info['models_removed']}")
        click.echo(f"   Space freed: {cleaned_info['space_freed_gb']:.2f} GB")
        click.echo(f"   Errors: {cleaned_info['errors']}")

    except Exception as e:
        click.echo(f"❌ Clean error: {e}")
        raise click.ClickException(f"Cache cleaning failed: {e}")