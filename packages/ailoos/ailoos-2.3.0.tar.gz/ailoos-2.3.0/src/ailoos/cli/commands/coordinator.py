#!/usr/bin/env python3
"""
Coordinator management commands for Ailoos CLI.
Simple coordinator without complex dependencies.
"""

import click
import requests
import time
from typing import Optional


@click.group()
@click.pass_context
def coordinator(ctx):
    """Federated learning coordinator management commands."""
    ctx.obj = ctx.obj or {}


@coordinator.command()
@click.option("--host", default="localhost", help="Host to bind coordinator to")
@click.option("--port", default=5001, type=int, help="Port to bind coordinator to")
@click.pass_context
def start(ctx, host: str, port: int):
    """Start a simple federated learning coordinator."""
    try:
        from ...coordinator.simple_coordinator import SimpleCoordinator

        click.echo(f"🚀 Starting Simple Ailoos Coordinator on {host}:{port}...")
        coordinator = SimpleCoordinator(host=host, port=port)
        coordinator.start()

    except KeyboardInterrupt:
        click.echo("\n👋 Coordinator stopped")
    except Exception as e:
        click.echo(f"❌ Failed to start coordinator: {e}", err=True)
        raise click.Abort()


@coordinator.command()
@click.option("--host", default="localhost", help="Coordinator host")
@click.option("--port", default=5001, type=int, help="Coordinator port")
@click.pass_context
def status(ctx, host: str, port: int):
    """Check coordinator status."""
    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            click.echo(f"✅ Coordinator is healthy: {data}")
        else:
            click.echo(f"❌ Coordinator returned status {response.status_code}")

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Cannot connect to coordinator: {e}")


@coordinator.command()
@click.option("--host", default="localhost", help="Coordinator host")
@click.option("--port", default=5001, type=int, help="Coordinator port")
@click.option("--model", default="tiny-model", help="Model name for the session")
@click.option("--rounds", default=3, type=int, help="Number of training rounds")
@click.option("--min-nodes", default=2, type=int, help="Minimum nodes required")
@click.option("--max-nodes", default=10, type=int, help="Maximum nodes allowed")
@click.pass_context
def create_session(ctx, host: str, port: int, model: str, rounds: int, min_nodes: int, max_nodes: int):
    """Create a new federated learning session."""
    try:
        data = {
            "model_name": model,
            "config": {
                "rounds": rounds,
                "min_nodes": min_nodes,
                "max_nodes": max_nodes
            }
        }

        response = requests.post(f"http://{host}:{port}/sessions", json=data, timeout=10)

        if response.status_code == 201:
            session_data = response.json()
            session_id = session_data["session_id"]
            click.echo(f"✅ Created session: {session_id}")
            click.echo(f"🎯 Model: {model} | Rounds: {rounds} | Nodes: {min_nodes}-{max_nodes}")
        else:
            click.echo(f"❌ Failed to create session: {response.text}")

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Cannot connect to coordinator: {e}")


@coordinator.command()
@click.option("--host", default="localhost", help="Coordinator host")
@click.option("--port", default=5001, type=int, help="Coordinator port")
@click.pass_context
def list_sessions(ctx, host: str, port: int):
    """List all federated learning sessions."""
    try:
        response = requests.get(f"http://{host}:{port}/sessions", timeout=10)

        if response.status_code == 200:
            data = response.json()
            sessions = data.get("sessions", [])

            if not sessions:
                click.echo("📭 No sessions found")
                return

            click.echo("🎯 Active Sessions:")
            click.echo("-" * 60)

            for session in sessions:
                status_emoji = {
                    "waiting": "⏳",
                    "training": "🚀",
                    "completed": "✅",
                    "failed": "❌"
                }.get(session["status"], "❓")

                click.echo(f"{status_emoji} {session['session_id']} | {session['model_name']} | "
                           f"{session['status']} | {session['nodes']} nodes | "
                           f"Round {session['current_round']}/{session['total_rounds']}")
        else:
            click.echo(f"❌ Failed to list sessions: {response.text}")

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Cannot connect to coordinator: {e}")


@coordinator.command()
@click.option("--host", default="localhost", help="Coordinator host")
@click.option("--port", default=5001, type=int, help="Coordinator port")
@click.argument("session_id")
@click.pass_context
def session_info(ctx, host: str, port: int, session_id: str):
    """Get detailed information about a session."""
    try:
        response = requests.get(f"http://{host}:{port}/sessions/{session_id}", timeout=10)

        if response.status_code == 200:
            session = response.json()
            click.echo(f"🎯 Session: {session['session_id']}")
            click.echo(f"📊 Status: {session['status']}")
            click.echo(f"👥 Nodes: {len(session['nodes'])}")
            click.echo(f"🎲 Current Round: {session['current_round']}")
            click.echo(f"🤝 Participants: {', '.join(session['nodes']) if session['nodes'] else 'None'}")
        else:
            click.echo(f"❌ Session not found: {response.text}")

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Cannot connect to coordinator: {e}")


@coordinator.command()
@click.option("--host", default="localhost", help="Coordinator host")
@click.option("--port", default=5001, type=int, help="Coordinator port")
@click.argument("session_id")
@click.pass_context
def start_session(ctx, host: str, port: int, session_id: str):
    """Start a federated learning session."""
    try:
        response = requests.post(f"http://{host}:{port}/sessions/{session_id}/start", timeout=10)

        if response.status_code == 200:
            click.echo(f"🚀 Started session {session_id}")
        else:
            click.echo(f"❌ Failed to start session: {response.text}")

    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Cannot connect to coordinator: {e}")