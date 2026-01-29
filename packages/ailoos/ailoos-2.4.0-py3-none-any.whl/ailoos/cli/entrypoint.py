#!/usr/bin/env python3
"""
Unified CLI entrypoint for Ailoos commands.
"""

import asyncio
import click

from .main import AILOOSCLI
from .commands.rewards import rewards
from .commands.node import node
from .commands.model import model
from .commands.coordinator import coordinator
from .commands.federated import federated
from .commands.marketplace import marketplace
from .commands.logs import logs
from .commands.cli_config import cli_config


@click.group()
def cli():
    """Ailoos CLI (bridge-aware commands + terminal)."""


@cli.command()
@click.option('--user-id', default='default_user', help='User ID for the session')
def terminal(user_id):
    """Launch the interactive neural link terminal."""
    asyncio.run(AILOOSCLI(user_id).run())


cli.add_command(rewards)
cli.add_command(node)
cli.add_command(model)
cli.add_command(coordinator)
cli.add_command(federated)
cli.add_command(marketplace)
cli.add_command(logs)
cli.add_command(cli_config)


if __name__ == "__main__":
    cli()
