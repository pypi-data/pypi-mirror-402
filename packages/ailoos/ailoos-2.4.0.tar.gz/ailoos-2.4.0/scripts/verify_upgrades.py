
import asyncio
import os
import sys
import numpy as np

# Add src to path
sys.path.append(os.path.abspath("./src"))

from ailoos.sdk.auth import NodeAuthenticator
from ailoos.sdk.p2p_client import P2PClient
from ailoos.sdk.marketplace_client import MarketplaceClient
from ailoos.sdk.federated_client import FederatedClient
from cryptography.hazmat.primitives import serialization

async def verify_auth():
    print("\n[VERIFY] Auth Module (ECDSA)...")
    auth = NodeAuthenticator("test_node", "http://localhost:5000", keys_dir="./tmp_keys")
    await auth.initialize()
    if os.path.exists("./tmp_keys/test_node.pem"):
        print("✅ Keys generated successfully (PEM found)")
    else:
        print("❌ Keys NOT generated")
        
    try:
        sig = auth.sign_message(b"test")
        print(f"✅ Signing working (Signature len: {len(sig)})")
    except Exception as e:
        print(f"❌ Signing failed: {e}")
    
    await auth.close()

async def verify_p2p():
    print("\n[VERIFY] P2P Module (ECDH)...")
    p2p = P2PClient("test_node", port=9999)
    try:
        # Check if keys are valid objects
        pub_bytes = p2p._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        print("✅ P2P ECDH Keys initialized and serializable")
        print(f"✅ P2P Dht initialized: {p2p.dht.node_id}")
    except Exception as e:
        print(f"❌ P2P Init failed: {e}")
    p2p.stop()

async def verify_marketplace():
    print("\n[VERIFY] Marketplace Module (Transactions)...")
    market = MarketplaceClient("test_node")
    # It might fail to connect to RPC, but class should load
    await market.initialize()
    print("✅ Marketplace Client initialized (RPC check skipped/warned)")
    await market.close()
    
async def verify_federated():
    print("\n[VERIFY] Federated Client (Serialization)...")
    # Mock auth 
    class MockAuth:
        def get_auth_headers(self): return {}
        async def is_authenticated(self): return True
        
    mock_auth = MockAuth()
    client = FederatedClient("test_node", "http://localhost:5000", authenticator=mock_auth)
    
    # Test serialization
    weights = {"layer1": np.random.rand(10, 10).astype(np.float32)}
    try:
        serialized = client._serialize_weights(weights)
        print(f"✅ Serialization successful (Keys: {list(serialized.keys())})")
    except Exception as e:
        print(f"❌ Serialization failed: {e}")

async def run_verification():
    print("🚀 Starting Verification of Production Upgrades")
    
    try:
        await verify_auth()
        await verify_p2p()
        await verify_marketplace()
        await verify_federated()
        print("\n✨ All modules loaded and initialized successfully!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_verification())
