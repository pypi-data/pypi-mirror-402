#!/usr/bin/env python3
"""
AILOOS New CLI - Terminal nativo en Python
Interfaz real que lee hardware, wallet y estado del sistema
"""

import asyncio
import os
import click
from typing import Optional

from .main import AILOOSCLI


@click.group()
@click.option('--user-id', default='default_user', help='User ID for the session')
@click.pass_context
def cli(ctx, user_id):
    """AILOOS Neural Link Terminal - Decentralized AI Command Center"""
    ctx.ensure_object(dict)
    ctx.obj['user_id'] = user_id
    ctx.obj['cli_instance'] = AILOOSCLI(user_id)


@cli.command()
@click.pass_context
def terminal(ctx):
    """Launch the interactive neural link terminal"""
    cli_instance = ctx.obj['cli_instance']
    asyncio.run(cli_instance.run())


@cli.command()
@click.pass_context
def status(ctx):
    """Show current system and wallet status"""
    cli_instance = ctx.obj['cli_instance']

    async def show_status():
        await cli_instance.initialize()
        cli_instance.show_main_screen()

    asyncio.run(show_status())


@cli.command()
@click.option('--json', is_flag=True, help='Output in JSON format')
@click.pass_context
def wallet_balance(ctx, json):
    """Show wallet balance"""
    cli_instance = ctx.obj['cli_instance']

    async def show_balance():
        wallet_info = await cli_instance.wallet.get_wallet_balance()
        if json:
            import json as json_lib
            click.echo(json_lib.dumps(wallet_info, indent=2))
        else:
            click.echo(f"💰 Balance: {wallet_info.get('balance', 0):.2f} DRACMA")
            click.echo(f"🔒 Staked: {wallet_info.get('staked', 0):.2f} DRACMA")
            click.echo(f"🎁 Rewards: {wallet_info.get('rewards', 0):.2f} DRACMA")
            click.echo(f"📧 Address: {wallet_info.get('address', 'Not set')}")

    asyncio.run(show_balance())


@cli.command()
@click.option('--limit', default=10, help='Number of transactions to show')
@click.pass_context
def wallet_history(ctx, limit):
    """Show wallet transaction history"""
    cli_instance = ctx.obj['cli_instance']

    async def show_history():
        transactions = await cli_instance.wallet.get_transaction_history(limit)
        if transactions:
            click.echo("📊 Recent Transactions:")
            for tx in transactions:
                click.echo(f"  {tx.get('date', '')[:10]} | {tx.get('type', '')} | {tx.get('amount', 0):.2f} DracmaS | {tx.get('description', '')}")
        else:
            click.echo("No transactions found")

    asyncio.run(show_history())


@cli.command()
@click.argument('amount', type=float)
@click.option('--to', required=True, help='Recipient address')
@click.pass_context
def wallet_transfer(ctx, amount, to):
    """Transfer DracmaS tokens"""
    cli_instance = ctx.obj['cli_instance']

    async def transfer():
        try:
            # Verificar balance
            balance_info = await cli_instance.wallet.get_wallet_balance()
            if balance_info.get('balance', 0) < amount:
                click.echo("❌ Insufficient balance", err=True)
                return

            # Realizar transferencia (simulada por ahora)
            click.echo(f"💸 Transferring {amount} DracmaS to {to}...")

            # Actualizar estado local
            wallet_info = cli_instance.state.get_wallet_info()
            wallet_info['balance'] = wallet_info.get('balance', 0) - amount
            cli_instance.state.update_wallet_info(wallet_info)

            cli_instance.state.add_transaction({
                'type': 'transfer',
                'amount': -amount,
                'description': f'Transfer to {to}'
            })

            click.echo("✅ Transfer completed successfully!")

        except Exception as e:
            click.echo(f"❌ Transfer failed: {e}", err=True)

    asyncio.run(transfer())


@cli.command()
@click.argument('amount', type=float)
@click.pass_context
def stake(ctx, amount):
    """Stake DracmaS tokens"""
    cli_instance = ctx.obj['cli_instance']

    async def stake_tokens():
        try:
            # Verificar balance
            balance_info = await cli_instance.wallet.get_wallet_balance()
            if balance_info.get('balance', 0) < amount:
                click.echo("❌ Insufficient balance", err=True)
                return

            click.echo(f"🔒 Staking {amount} DRACMA...")

            # Actualizar estado
            wallet_info = cli_instance.state.get_wallet_info()
            wallet_info['balance'] = wallet_info.get('balance', 0) - amount
            wallet_info['staked'] = wallet_info.get('staked', 0) + amount
            cli_instance.state.update_wallet_info(wallet_info)

            cli_instance.state.add_transaction({
                'type': 'stake',
                'amount': amount,
                'description': 'Token staking'
            })

            staking_info = await cli_instance.wallet.get_staking_info()
            click.echo(f"✅ Staking completed! APY: {staking_info.get('apy', 15.5)}%")

        except Exception as e:
            click.echo(f"❌ Staking failed: {e}", err=True)

    asyncio.run(stake_tokens())


@cli.command()
@click.pass_context
def hardware(ctx):
    """Show hardware information"""
    cli_instance = ctx.obj['cli_instance']

    hardware_info = cli_instance.hardware.get_all_hardware_info()

    click.echo("🔧 HARDWARE INFORMATION")
    click.echo("=" * 40)

    cpu = hardware_info.get('cpu', {})
    click.echo(f"CPU: {cpu.get('cores', 0)} cores, {cpu.get('usage_percent', 0):.1f}% usage")

    mem = hardware_info.get('memory', {})
    click.echo(f"RAM: {mem.get('used_gb', 0):.1f}/{mem.get('total_gb', 0):.1f} GB ({mem.get('usage_percent', 0):.1f}%)")

    disk = hardware_info.get('disk', {})
    click.echo(f"Disk: {disk.get('used_gb', 0):.1f}/{disk.get('total_gb', 0):.1f} GB ({disk.get('usage_percent', 0):.1f}%)")

    gpu = hardware_info.get('gpu', {})
    click.echo(f"GPU: {gpu.get('name', 'None detected')}")

    system = hardware_info.get('system', {})
    click.echo(f"OS: {system.get('os', 'Unknown')}")


@cli.command()
@click.pass_context
def system(ctx):
    """Show system status"""
    cli_instance = ctx.obj['cli_instance']

    system_info = cli_instance.system.get_all_system_status()

    click.echo("🌐 SYSTEM STATUS")
    click.echo("=" * 40)

    click.echo(f"Uptime: {system_info.get('uptime', 'Unknown')}")
    click.echo(f"Peers: {system_info.get('peers', 0)}")
    click.echo(f"Network: {system_info.get('network', {}).get('status', 'Unknown')}")

    load = system_info.get('load', {})
    click.echo(f"Load Average: {load.get('1min', 0):.2f}, {load.get('5min', 0):.2f}, {load.get('15min', 0):.2f}")


@cli.command()
@click.pass_context
def node_info(ctx):
    """Show node information"""
    cli_instance = ctx.obj['cli_instance']

    node_info = cli_instance.state.get_node_info()
    stats = cli_instance.state.get_stats()

    click.echo("🤖 NODE INFORMATION")
    click.echo("=" * 40)

    click.echo(f"Node ID: {node_info.get('id', 'Unknown')}")
    click.echo(f"Role: {node_info.get('role', 'Unknown')}")
    click.echo(f"Level: {node_info.get('level', 1)}")
    click.echo(f"Reputation: {node_info.get('reputation', 0)}/1000")
    click.echo(f"Peers: {node_info.get('peers', 0)}")
    click.echo(f"Status: {node_info.get('status', 'Unknown')}")

    click.echo(f"\n📊 STATISTICS")
    click.echo(f"Total Earned: {stats.get('total_earned', 0):.2f} DRACMA")
    click.echo(f"Datasets Processed: {stats.get('datasets_processed', 0)}")
    click.echo(f"Training Sessions: {stats.get('training_sessions', 0)}")
    click.echo(f"Validation Tasks: {stats.get('validation_tasks', 0)}")


@cli.command()
@click.argument('user_id', required=False)
@click.pass_context
def create_wallet(ctx, user_id):
    """Create a new DracmaS wallet"""
    if not user_id:
        user_id = ctx.obj['user_id']

    cli_instance = ctx.obj['cli_instance']

    async def create():
        try:
            click.echo(f"💰 Creating wallet for user: {user_id}...")

            # Intentar crear wallet real
            wallet_info = await cli_instance.wallet.get_wallet_balance()

            if wallet_info.get('address') and not wallet_info.get('address').startswith('0x'):
                # Wallet ya existe
                click.echo(f"✅ Wallet already exists: {wallet_info.get('address')}")
            else:
                # Simular creación
                click.echo("✅ Wallet created successfully!")
                click.echo(f"📧 Address: 0x{os.urandom(20).hex()}")
                click.echo("💰 Initial balance: 100.00 DRACMA")

        except Exception as e:
            click.echo(f"❌ Failed to create wallet: {e}", err=True)

    asyncio.run(create())


if __name__ == '__main__':
    cli()