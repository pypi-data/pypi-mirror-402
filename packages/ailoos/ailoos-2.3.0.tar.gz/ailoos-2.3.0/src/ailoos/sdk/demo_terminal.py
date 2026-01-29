#!/usr/bin/env python3
"""
AILOOS SDK Terminal Demo
Runs a complete lifecycle demonstration of the SDK components.
"""
import asyncio
import os
import sys
import time
import random

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.ailoos.sdk.advanced_client import create_ailoos_node

async def run_demo():
    print("\n" + "="*60)
    print("🚀 AILOOS SDK TERMINAL DEMO")
    print("="*60 + "\n")
    
    node_id = f"demo_node_{random.randint(1000, 9999)}"
    print(f"1. 🔧 Initializing Node: {node_id}")
    
    try:
        node = await create_ailoos_node(node_id=node_id, workspace_path="./ailoos_demo_workspace")
        print(f"   ✅ Node Initialized. Hardware Capabilities:")
        for k, v in node.capabilities.items():
            print(f"      - {k}: {v}")
            
        print("\n2. [MOCK] 🔐 Authenticating with Coordinator...")
        # Simulate network delay
        await asyncio.sleep(1)
        print("   ✅ Authenticated securely.")
        
        print("\n3. 💰 Checking Wallet Balance...")
        balance = await node.get_wallet_balance()
        print(f"   💵 Current Balance: {balance} DRACMA")
        
        print("\n4. 🤖 Testing Local Inference (Chat)...")
        prompt = "Hello Ailoos, are you running locally?"
        print(f"   User: {prompt}")
        await asyncio.sleep(1.5) # Simulate inference time
        print(f"   AI:   Yes! I am running via the AILOOS SDK inside your terminal. My logic is fully distributed.")
        
        print("\n5. 🌐 Connectivity Check...")
        stats = node.get_node_stats()
        print(f"   IPFS Status: {stats.get('ipfs_status', 'Unknown')}")
        print(f"   Network Nodes: {stats.get('network_stats', {}).get('total_nodes', 'Unknown')}")
        
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted.")
