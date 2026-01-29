#!/usr/bin/env python3
"""
AILOOS SDK Command Line Interface
"""
import argparse
import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.ailoos.sdk.advanced_client import get_default_node, create_ailoos_node
from src.ailoos.sdk.node_sdk import NodeSDK

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ailoos.cli')

async def cmd_init(args):
    """Initialize a new node configuration."""
    print(f"🚀 Initializing AILOOS Node: {args.node_id}")
    node = await get_default_node(node_id=args.node_id)
    print(f"✅ Node initialized in {node.workspace_path}")
    print(f"   Capabilities: {node.capabilities}")
    
async def cmd_status(args):
    """Show node status."""
    node = await get_default_node(node_id=args.node_id)
    stats = node.get_full_status() if hasattr(node, "get_full_status") else await extract_status(node)
    
    print("\n📊 AILOOS NODE STATUS")
    print("=" * 40)
    print(json.dumps(stats, indent=2, default=str))

async def extract_status(node):
    """Helper to get status from AILOOSNode if get_full_status is missing/different."""
    # AILOOSNode has get_node_stats() and get_full_status()
    if hasattr(node, "get_full_status"):
        return await node.get_full_status()
    # Fallback
    return {
        "node_id": node.node_id,
        "initialized": node.initialized,
        "capabilities": node.capabilities,
        "stats": node.stats
    }

async def cmd_chat(args):
    """Test inference/chat functionality."""
    print(f"💬 Sending chat request to model '{args.model}'...")
    print(f"   Prompt: {args.message}")
    
    # Here we would normally use node.inference.generate or similar.
    # Since AILOOSNode wraps many clients, we check for inference capability or Mock it for the CLI test
    # if the backend isn't running.
    
    # For now, let's use the NodeSDK directly if we want pure inference, or mock interaction via AILOOSNode
    # Let's try to simulate a specialized chat interaction
    
    print("\n[MOCK RESPONSE] 🤖 AI: Hello! I am a simulated response from the AILOOS Local SDK. I received your message: " + args.message)

async def cmd_wallet(args):
    """Show wallet balance."""
    node = await get_default_node(node_id=args.node_id)
    try:
        balance = await node.get_wallet_balance()
        print(f"\n💰 Wallet Balance: {balance} DRACMA")
    except Exception as e:
        print(f"\n❌ Error fetching balance: {e}")

async def main():
    parser = argparse.ArgumentParser(description="AILOOS SDK CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Global args
    parser.add_argument("--node-id", default="cli_user_node", help="Node ID to use")

    # Command: init
    parser_init = subparsers.add_parser("init", help="Initialize the node")
    
    # Command: status
    parser_status = subparsers.add_parser("status", help="Show node status")
    
    # Command: chat
    parser_chat = subparsers.add_parser("chat", help="Send a chat message")
    parser_chat.add_argument("--message", "-m", required=True, help="Message to send")
    parser_chat.add_argument("--model", default="empoorio-lm", help="Model to use")
    
    # Command: wallet
    parser_wallet = subparsers.add_parser("wallet", help="Check wallet balance")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "init":
            await cmd_init(args)
        elif args.command == "status":
            await cmd_status(args)
        elif args.command == "chat":
            await cmd_chat(args)
        elif args.command == "wallet":
            await cmd_wallet(args)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
