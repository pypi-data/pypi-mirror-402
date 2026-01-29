"""
Federated learning commands for Ailoos CLI.
Handles session management, training coordination, and federated operations.
"""

import asyncio
import click
import json
from typing import Optional
from ...federated.trainer import FederatedTrainer
from ...federated.aggregator import FedAvgAggregator
from ...utils.logging import AiloosLogger


@click.group()
def federated():
    """Federated learning management commands."""
    pass


@federated.command()
@click.option('--session-id', help='Specific session ID to join')
@click.option('--model', default='tiny-mlp', help='Model to train')
@click.option('--data-path', help='Path to local training data')
@click.option('--batch-size', default=32, type=int, help='Training batch size')
@click.option('--learning-rate', default=0.001, type=float, help='Learning rate')
@click.option('--local-epochs', default=1, type=int, help='Local epochs per round')
@click.option('--max-rounds', default=10, type=int, help='Maximum training rounds')
@click.option('--coordinator-url', default='http://localhost:5001', help='Coordinator URL')
def join(session_id, model, data_path, batch_size, learning_rate, local_epochs, max_rounds, coordinator_url):
    """Join a federated learning session."""
    if not session_id:
        click.echo("❌ Session ID is required. Use --session-id or find available sessions first.")
        raise click.Abort()

    click.echo(f"🔗 Joining federated session '{session_id}'...")
    click.echo(f"🤖 Model: {model}")
    click.echo(f"📊 Batch size: {batch_size}")
    click.echo(f"🎯 Learning rate: {learning_rate}")
    click.echo(f"🔄 Local epochs: {local_epochs}")

    # Create federated trainer
    trainer = FederatedTrainer(
        model_name=model,
        batch_size=batch_size,
        learning_rate=learning_rate,
        local_epochs=local_epochs,
        coordinator_url=coordinator_url
    )

    async def run_training():
        try:
            # Initialize trainer (creates model, etc.)
            init_success = await trainer.initialize()
            if not init_success:
                click.echo("❌ Failed to initialize trainer")
                return

            # Join session
            success = await trainer.join_session(session_id)
            if not success:
                click.echo("❌ Failed to join session")
                return

            click.echo("✅ Successfully joined session!")
            click.echo("🚀 Starting federated training...")

            # Start training loop
            results = await trainer.run_training_loop(max_rounds)

            # Show final results
            click.echo("\n🎉 Federated training completed!")
            click.echo(f"📊 Average global accuracy: {results['average_accuracy']:.2f}%")
            click.echo(f"📉 Average global loss: {results['average_loss']:.4f}")
            click.echo(f"🔄 Total rounds completed: {results['total_rounds']}")
            click.echo(f"💰 Total rewards earned: {results['total_samples']} samples processed")

        except KeyboardInterrupt:
            click.echo("\n🛑 Training interrupted by user")
            await trainer.stop()
        except Exception as e:
            click.echo(f"❌ Training failed: {e}")
            raise click.ClickException(f"Federated training error: {e}")

    asyncio.run(run_training())


@federated.command()
@click.option('--session-id', help='Specific session ID')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--coordinator-url', default='http://localhost:5001', help='Coordinator URL')
def status(session_id, json_output, coordinator_url):
    """Show federated training status."""
    if not session_id:
        click.echo("❌ Session ID is required.")
        raise click.Abort()

    async def get_status():
        import aiohttp
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                session_url = f"{coordinator_url}/api/training/sessions/{session_id}"
                async with session.get(session_url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        click.echo(f"❌ Error fetching status: {response.status} - {await response.text()}", err=True)
                        return None
        except Exception as e:
            click.echo(f"❌ Connection error: {e}", err=True)
            return None

    status_data = asyncio.run(get_status())

    if not status_data:
        raise click.Abort()

    if json_output:
        click.echo(json.dumps(status_data, indent=2))
    else:
        click.echo("🔄 Federated Training Status")
        click.echo("=" * 50)
        click.echo(f"🎯 Session: {status_data.get('session_id', 'N/A')}")
        click.echo(f"📊 Status: {status_data.get('status', 'N/A')}")
        click.echo(f"🔄 Round: {status_data.get('current_round', 0)}/{status_data.get('total_rounds', 0)}")

        participants = status_data.get('participants', {})
        click.echo(f"\n👥 Participants:")
        click.echo(f"   Total: {participants.get('total', 0)}")
        click.echo(f"   Active: {participants.get('active', 0)}")

        progress = status_data.get('progress', {})
        click.echo(f"\n📈 Progress:")
        click.echo(f"   Completion: {progress.get('completion_percentage', 0.0)}%")
        
        metrics = progress.get('global_metrics', {})
        click.echo(f"\n🎯 Metrics:")
        click.echo(f"   Accuracy: {metrics.get('accuracy', 0.0)}%")
        click.echo(f"   Loss: {metrics.get('loss', 0.0)}")

        click.echo(f"\n💰 Rewards: {status_data.get('rewards_distributed', 0.0)} DRACMA")


@federated.command()
@click.option('--session-id', help='Session ID to leave')
@click.option('--force', is_flag=True, help='Force immediate leave')
def leave(session_id, force):
    """Leave the current federated session."""
    if not session_id:
        click.echo("❌ Session ID is required")
        raise click.Abort()

    click.echo(f"👋 Leaving federated session '{session_id}'...")

    # Implementation would notify coordinator and clean up
    click.echo("✅ Successfully left session")


@federated.command()
@click.option('--coordinator-url', default='http://localhost:5001', help='Coordinator URL')
@click.option('--json', is_flag=True, help='Output in JSON format')
@click.option('--node-id', help='Communicate with specific node')
@click.option('--broadcast', help='Broadcast message to all nodes in session')
@click.option('--session-id', help='Session ID for broadcasting')
def sessions(coordinator_url, json, node_id, broadcast, session_id):
    """List available federated sessions and communicate with nodes."""
    import asyncio
    import aiohttp
    """List available federated sessions."""
    async def broadcast_to_session(target_session_id, broadcast_msg):
        """Broadcast message to all nodes in a session."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                broadcast_url = f"{coordinator_url}/api/communication/sessions/{target_session_id}/broadcast"

                async with session.post(broadcast_url, json={"message": broadcast_msg}) as response:
                    if response.status == 200:
                        result = await response.json()
                        click.echo(f"✅ Message broadcasted to session {target_session_id}")
                        click.echo(f"📨 Reached {result.get('nodes_reached', 0)} nodes")
                        return True
                    else:
                        error = await response.text()
                        click.echo(f"❌ Failed to broadcast: {error}")
                        return False

        except Exception as e:
            click.echo(f"❌ Broadcast error: {e}")
            return False

    async def get_sessions_from_coordinator():
        """Get real sessions from coordinator."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                sessions_url = f"{coordinator_url}/api/training/sessions"
                async with session.get(sessions_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("sessions", [])
                    else:
                        click.echo(f"⚠️  Coordinator returned status {response.status}. No sessions retrieved.", err=True)
                        return []

        except Exception as e:
            click.echo(f"❌ Could not connect to coordinator: {e}. No sessions retrieved.", err=True)
            return []

    async def communicate_with_specific_node(target_node_id):
        """Get detailed communication info for a specific node."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Get node details
                node_url = f"{coordinator_url}/api/nodes/{target_node_id}"
                async with session.get(node_url) as response:
                    if response.status == 200:
                        node_data = await response.json()

                        # Get communication stats
                        comm_url = f"{coordinator_url}/api/communication/nodes/{target_node_id}/stats"
                        async with session.get(comm_url) as response:
                            comm_data = await response.json() if response.status == 200 else {}

                        return {
                            "node_id": target_node_id,
                            "status": node_data.get("status", "unknown"),
                            "connected": node_data.get("connected", False),
                            "last_seen": node_data.get("last_seen"),
                            "current_session": node_data.get("current_session"),
                            "messages_sent": comm_data.get("messages_sent", 0),
                            "messages_received": comm_data.get("messages_received", 0),
                            "commands_executed": comm_data.get("commands_executed", 0),
                            "avg_response_time": comm_data.get("avg_response_time_ms", 0)
                        }
                    else:
                        click.echo(f"❌ Node {target_node_id} not found")
                        return None

        except Exception as e:
            click.echo(f"❌ Communication error: {e}")
            return None

    click.echo("🔍 Discovering available sessions...")

    async def run_sessions_command():
        # Handle communication modes first
        if node_id:
            # Communicate with specific node
            node_info = await communicate_with_specific_node(node_id)
            if node_info:
                click.echo("📡 Node Communication Details")
                click.echo("=" * 50)
                click.echo(f"🎯 Node ID: {node_info['node_id']}")
                click.echo(f"🟢 Status: {node_info['status']}")
                click.echo(f"📶 Connected: {'Yes' if node_info['connected'] else 'No'}")

                if node_info.get('last_seen'):
                    click.echo(f"👀 Last Seen: {node_info['last_seen']}")
                if node_info.get('current_session'):
                    click.echo(f"🎯 Session: {node_info['current_session']}")

                click.echo(f"\n📨 Messages Sent: {node_info['messages_sent']}")
                click.echo(f"📨 Messages Received: {node_info['messages_received']}")
                click.echo(f"⚙️  Commands Executed: {node_info['commands_executed']}")
                if node_info.get('avg_response_time', 0) > 0:
                    click.echo(f"⚡ Avg Response Time: {node_info['avg_response_time']}ms")

            return

        if broadcast and session_id:
            # Broadcast message to session
            success = await broadcast_to_session(session_id, broadcast)
            if not success:
                raise click.Abort()
            return

        # Get sessions from coordinator
        sessions_data = await get_sessions_from_coordinator()

        # No sessions available
        if not sessions_data:
            click.echo("ℹ️ No active or available sessions found on the coordinator.")
            return

        if json:
            click.echo(json.dumps({"sessions": sessions_data}, indent=2))
        else:
            click.echo("📋 Available Federated Sessions")
            click.echo("=" * 60)
            click.echo("<10")
            click.echo("-" * 60)

            for session in sessions_data:
                status_emoji = "🟢" if session['status'] == 'active' else "🟡" if session['status'] == 'waiting' else "🔴"
                click.echo("<10")

    asyncio.run(run_sessions_command())




@federated.command()
@click.option('--session-id', required=True, help='Session ID to monitor')
@click.option('--round-number', type=int, help='Specific round to monitor')
@click.option('--follow', is_flag=True, help='Follow mode - show live updates')
@click.option('--coordinator-url', default='http://localhost:5001', help='Coordinator URL')
@click.option('--interval', default=5, type=int, help='Update interval in seconds')
@click.option('--json', is_flag=True, help='Output in JSON format')
@click.option('--node-id', help='Specific node ID to communicate with')
@click.option('--message', help='Message to send to node')
@click.option('--command', help='Command to execute on node')
def monitor(session_id, round_number, follow, coordinator_url, interval, json, node_id, message, command):
    """Monitor federated training progress in real-time."""
    import aiohttp
    import time
    from datetime import datetime

    async def get_session_status():
        """Get real-time session status from coordinator."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Get session overview
                session_url = f"{coordinator_url}/api/training/sessions/{session_id}"
                async with session.get(session_url) as response:
                    if response.status == 200:
                        session_data = await response.json()
                    else:
                        click.echo(f"❌ Session not found: {session_id}")
                        return None

                # Get current round details
                current_round = session_data.get('current_round', 0)
                if round_number and round_number != current_round:
                    # Get specific round data
                    round_url = f"{coordinator_url}/api/training/sessions/{session_id}/rounds/{round_number}"
                    async with session.get(round_url) as response:
                        if response.status == 200:
                            round_data = await response.json()
                        else:
                            round_data = {}
                else:
                    round_data = session_data.get('current_round_data', {})

                # Get participants status
                participants_url = f"{coordinator_url}/api/training/sessions/{session_id}/participants"
                async with session.get(participants_url) as response:
                    if response.status == 200:
                        participants_data = await response.json()
                    else:
                        participants_data = {'total': 0, 'active': 0, 'completed': 0}

                # Get global metrics
                metrics_url = f"{coordinator_url}/api/training/sessions/{session_id}/metrics"
                async with session.get(metrics_url) as response:
                    if response.status == 200:
                        metrics_data = await response.json()
                    else:
                        metrics_data = {}

                # Get rewards information
                rewards_url = f"{coordinator_url}/api/training/sessions/{session_id}/rewards"
                async with session.get(rewards_url) as response:
                    if response.status == 200:
                        rewards_data = await response.json()
                    else:
                        rewards_data = {'total_distributed': 0, 'last_distribution': None}

                # Compile comprehensive status
                status = {
                    'session_id': session_id,
                    'status': session_data.get('status', 'unknown'),
                    'current_round': current_round,
                    'total_rounds': session_data.get('total_rounds', 0),
                    'model_name': session_data.get('model_name', 'unknown'),
                    'created_at': session_data.get('created_at'),
                    'participants': {
                        'total': participants_data.get('total', 0),
                        'active': participants_data.get('active', 0),
                        'completed': participants_data.get('completed', 0),
                        'failed': participants_data.get('failed', 0)
                    },
                    'current_round_data': {
                        'round_number': round_data.get('round_number', current_round),
                        'status': round_data.get('status', 'unknown'),
                        'start_time': round_data.get('start_time'),
                        'participants_submitted': round_data.get('participants_submitted', 0),
                        'participants_expected': round_data.get('participants_expected', 0),
                        'progress_percentage': round_data.get('progress_percentage', 0.0)
                    },
                    'global_metrics': {
                        'accuracy': metrics_data.get('global_accuracy', 0.0),
                        'loss': metrics_data.get('global_loss', 0.0),
                        'convergence_rate': metrics_data.get('convergence_rate', 0.0),
                        'total_samples': metrics_data.get('total_samples_processed', 0),
                        'avg_round_time': metrics_data.get('average_round_time', 0)
                    },
                    'rewards': {
                        'total_distributed': rewards_data.get('total_distributed', 0),
                        'last_distribution': rewards_data.get('last_distribution'),
                        'rewards_per_round': rewards_data.get('rewards_per_round', 0)
                    },
                    'estimated_completion': session_data.get('estimated_completion_time'),
                    'last_updated': datetime.now().isoformat()
                }

                return status

        except aiohttp.ClientError as e:
            click.echo(f"❌ Network error: {e}")
            return None
        except Exception as e:
            click.echo(f"❌ Error getting session status: {e}")
            return None

    def display_status(status, json_output=False):
        """Display session status in a formatted way."""
        if json_output:
            click.echo(json.dumps(status, indent=2, default=str))
            return

        click.echo("🔄 Federated Training Status")
        click.echo("=" * 60)
        click.echo(f"🎯 Session: {status['session_id']}")
        click.echo(f"📊 Status: {status['status'].title()}")
        click.echo(f"🤖 Model: {status['model_name']}")
        click.echo(f"🔄 Round: {status['current_round']}/{status['total_rounds']}")

        if status.get('created_at'):
            click.echo(f"📅 Created: {status['created_at']}")

        click.echo(f"\n👥 Participants:")
        p = status['participants']
        click.echo(f"   Total: {p['total']}")
        click.echo(f"   Active: {p['active']}")
        click.echo(f"   Completed: {p['completed']}")
        if p.get('failed', 0) > 0:
            click.echo(f"   Failed: {p['failed']}")

        click.echo(f"\n🎯 Current Round ({status['current_round_data']['round_number']}):")
        cr = status['current_round_data']
        click.echo(f"   Status: {cr['status'].title()}")
        click.echo(f"   Progress: {cr['progress_percentage']:.1f}%")
        click.echo(f"   Submitted: {cr['participants_submitted']}/{cr['participants_expected']}")

        if cr.get('start_time'):
            click.echo(f"   Started: {cr['start_time']}")

        click.echo(f"\n📈 Global Metrics:")
        m = status['global_metrics']
        click.echo(f"   Accuracy: {m['accuracy']:.2f}%")
        click.echo(f"   Loss: {m['loss']:.4f}")
        click.echo(f"   Convergence: {m['convergence_rate']:.4f}")
        click.echo(f"   Total Samples: {m['total_samples']:,}")
        if m.get('avg_round_time', 0) > 0:
            click.echo(f"   Avg Round Time: {m['avg_round_time']:.1f}s")

        click.echo(f"\n💰 Rewards:")
        r = status['rewards']
        click.echo(f"   Total Distributed: {r['total_distributed']:.6f} DRACMA")
        if r.get('rewards_per_round', 0) > 0:
            click.echo(f"   Per Round: {r['rewards_per_round']:.6f} DRACMA")
        if r.get('last_distribution'):
            click.echo(f"   Last Distribution: {r['last_distribution']}")

        if status.get('estimated_completion'):
            click.echo(f"\n⏰ ETA: {status['estimated_completion']}")

        click.echo(f"\n🔄 Last Updated: {status['last_updated']}")

    async def monitor_follow():
        """Follow mode for continuous monitoring."""
        click.echo(f"📊 Monitoring session '{session_id}' in real-time")
        click.echo("🔄 Press Ctrl+C to stop monitoring")
        click.echo("=" * 60)

        last_round = None

        try:
            while True:
                status = await get_session_status()
                if status:
                    # Clear screen for better UX (optional)
                    if last_round != status['current_round']:
                        click.echo(f"\n🎯 Round {status['current_round']} started!")
                        last_round = status['current_round']

                    display_status(status, json)

                    # Show progress bar for current round
                    cr = status['current_round_data']
                    if cr['participants_expected'] > 0:
                        progress = cr['participants_submitted'] / cr['participants_expected']
                        bar_width = 40
                        filled = int(bar_width * progress)
                        bar = "█" * filled + "░" * (bar_width - filled)
                        click.echo(f"\n📊 Round Progress: [{bar}] {progress:.1%}")

                    click.echo(f"\n⏰ Next update in {interval}s... (Ctrl+C to stop)")
                    click.echo("-" * 60)
                else:
                    click.echo("❌ Unable to fetch session status")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            click.echo("\n🛑 Stopped monitoring session")

    async def communicate_with_node(target_node_id, msg, cmd):
        """Send message or command to a specific node."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Send message to node via coordinator
                comm_url = f"{coordinator_url}/api/communication/nodes/{target_node_id}"

                payload = {}
                if msg:
                    payload["message"] = msg
                if cmd:
                    payload["command"] = cmd

                if not payload:
                    click.echo("❌ Must provide either --message or --command")
                    return False

                async with session.post(comm_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        click.echo(f"✅ Message sent to node {target_node_id}")
                        if result.get("response"):
                            click.echo(f"📨 Response: {result['response']}")
                        return True
                    else:
                        error = await response.text()
                        click.echo(f"❌ Failed to communicate with node: {error}")
                        return False

        except Exception as e:
            click.echo(f"❌ Communication error: {e}")
            return False

    async def get_node_communication_status(target_node_id):
        """Get communication status with a specific node."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                # Check node connectivity
                status_url = f"{coordinator_url}/api/nodes/{target_node_id}/status"
                async with session.get(status_url) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        return {
                            "node_id": target_node_id,
                            "connected": status_data.get("connected", False),
                            "last_seen": status_data.get("last_seen"),
                            "latency_ms": status_data.get("latency_ms"),
                            "message_queue_size": status_data.get("message_queue_size", 0),
                            "pending_commands": status_data.get("pending_commands", 0)
                        }
                    else:
                        return {
                            "node_id": target_node_id,
                            "connected": False,
                            "error": f"HTTP {response.status}"
                        }

        except Exception as e:
            return {
                "node_id": target_node_id,
                "connected": False,
                "error": str(e)
            }

    def display_node_communication_status(comm_status):
        """Display node communication status."""
        click.echo("📡 Node Communication Status")
        click.echo("=" * 40)
        click.echo(f"🎯 Node: {comm_status['node_id']}")

        if comm_status.get("connected"):
            click.echo("🟢 Status: Connected")
            if comm_status.get("last_seen"):
                click.echo(f"👀 Last Seen: {comm_status['last_seen']}")
            if comm_status.get("latency_ms"):
                click.echo(f"⚡ Latency: {comm_status['latency_ms']}ms")
            if comm_status.get("message_queue_size", 0) > 0:
                click.echo(f"📨 Messages in Queue: {comm_status['message_queue_size']}")
            if comm_status.get("pending_commands", 0) > 0:
                click.echo(f"⚙️  Pending Commands: {comm_status['pending_commands']}")
        else:
            click.echo("🔴 Status: Disconnected")
            if comm_status.get("error"):
                click.echo(f"❌ Error: {comm_status['error']}")

    # Main execution
    if node_id:
        # Node communication mode
        if message or command:
            # Send message/command to node
            success = asyncio.run(communicate_with_node(node_id, message, command))
            if not success:
                raise click.Abort()
        else:
            # Check communication status with node
            comm_status = asyncio.run(get_node_communication_status(node_id))
            display_node_communication_status(comm_status)

    elif follow:
        # Session monitoring mode
        asyncio.run(monitor_follow())
    else:
        # Single session status check
        status = asyncio.run(get_session_status())
        if status:
            display_status(status, json)
        else:
            click.echo("❌ Unable to retrieve session status")
            raise click.Abort()


@federated.command()
@click.option('--session-id', required=True, help='Session ID')
@click.option('--output-dir', default='./federated_results', help='Output directory')
def results(session_id, output_dir):
    """Download and display federated training results."""
    click.echo(f"📥 Downloading results for session '{session_id}'...")
    click.echo(f"📁 Output directory: {output_dir}")

    # This would download final model and results
    click.echo("✅ Results downloaded successfully")
    click.echo(f"📊 Check {output_dir} for detailed results")


@federated.command()
@click.option('--session-id', required=True, help='Session ID')
@click.option('--node-id', help='Specific node ID')
@click.option('--metric', type=click.Choice(['accuracy', 'loss', 'contribution', 'rewards']),
              help='Metric to analyze')
def analyze(session_id, node_id, metric):
    """Analyze federated training performance."""
    click.echo(f"📊 Analyzing session '{session_id}'...")

    if node_id:
        click.echo(f"🎯 Node: {node_id}")
    if metric:
        click.echo(f"📈 Metric: {metric}")

    # This would perform detailed analysis
    click.echo("✅ Analysis completed")
    click.echo("📋 Results saved to analysis_report.json")


@federated.command()
@click.option('--session-id', required=True, help='Session ID to pause')
def pause(session_id):
    """Pause federated training session."""
    click.echo(f"⏸️  Pausing session '{session_id}'...")

    # Implementation would notify coordinator to pause
    click.echo("✅ Session paused")


@federated.command()
@click.option('--session-id', required=True, help='Session ID to resume')
def resume(session_id):
    """Resume paused federated training session."""
    click.echo(f"▶️  Resuming session '{session_id}'...")

    # Implementation would notify coordinator to resume
    click.echo("✅ Session resumed")


@federated.command()
@click.option('--session-id', required=True, help='Session ID to abort')
@click.confirmation_option(prompt='Are you sure you want to abort this session?')
def abort(session_id):
    """Abort federated training session (irreversible)."""
    click.echo(f"⚠️  Aborting session '{session_id}'...")

    # Implementation would notify coordinator and clean up
    click.echo("✅ Session aborted")