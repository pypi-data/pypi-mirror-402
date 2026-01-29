"""
Setup script for Ailoos - Sovereign Decentralized AI Library with Wallet & Staking
"""

from setuptools import setup, find_packages
import os

# Read README
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = """
    Ailoos - Sovereign Decentralized AI Library with Wallet & Staking
    =============================================================

    Ailoos is a comprehensive library for decentralized AI training and inference,
    featuring a complete blockchain-based economic system with DracmaS tokens,
    wallet management, staking rewards, and smart contract simulation.

    Key Features:
    - Federated Learning with FedAvg algorithm
    - Complete DracmaS wallet system with security
    - Staking with automatic rewards distribution
    - Smart contract simulation for DeFi operations
    - Governance system with stake-based voting
    - Decentralized marketplace for AI datasets
    - EmpoorioLM model training and inference
    - Easy-to-use APIs for developers
    - VS Code integration support
    - CLI tools for quick node activation
    """

# Read requirements
def read_requirements(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []

setup(
    name="ailoos",
    version="2.3.0",  # Sincronización oficial SDK v2.3.0
    author="Empoorio",
    author_email="dev@empoorio.com",
    description="Unified SDK experience for computer nodes only",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/empoorio/ailoos",
    project_urls={
        "Bug Tracker": "https://github.com/empoorio/ailoos/issues",
        "Documentation": "https://ailoos.dev/docs",
        "Source Code": "https://github.com/empoorio/ailoos",
        "Discord": "https://discord.gg/ailoos",
        "PyPI": "https://pypi.org/project/ailoos/",
        "Dashboard Demo": "https://dashboard.ailoos.dev",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Security :: Cryptography",
    ],
    install_requires=[
        # Core dependencies
        "aiohttp>=3.8.0",
        "psutil>=5.9.0",
        "numpy>=1.21.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "tqdm>=4.64.0",
        "structlog>=21.1.0",
        "tenseal>=0.3.0",
        # ML Core Dependencies
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "pandas>=2.0.0",
        # Dashboard dependencies
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "websockets>=12.0",
        "pydantic>=2.0.0",
        "rich>=13.0.0",
        "questionary>=2.0.0",
        # Blockchain dependencies
        "cryptography>=41.0.0",
        "PyJWT>=2.0.0",
        "passlib[bcrypt]>=1.7.0",
        "nest_asyncio>=1.5.0",  # Fix: Required for terminal async loop
    ],
    keywords="ai, machine-learning, federated-learning, decentralized, blockchain, wallet, staking, defi, dashboard, web-ui, websocket, empoorio, sovereign-ai, dracma, interactive-dashboard",
    packages=find_packages(where="src", exclude=[
        "ailoos.coordinator*", 
        "ailoos.infrastructure*",
        "ailoos.zero_trust*",
        "ailoos.active_learning*",
        "ailoos.blue_green_deployment*",
        "ailoos.scripts*"    # Admin scripts
    ]),
    package_dir={"": "src"},
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "gpu": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "torchaudio>=2.0.0",
        ],
        "ai": [
            "transformers>=4.21.0",
            "accelerate>=0.12.0",
            "datasets>=2.4.0",
        ],
        "dashboard": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "websockets>=12.0",
            "pydantic>=2.0.0",
        ],
        "full": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "torchaudio>=2.0.0",
            "transformers>=4.21.0",
            "datasets>=2.4.0",
            "accelerate>=0.12.0",
            "pandas>=1.5.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "scikit-learn>=1.1.0",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "websockets>=12.0",
            "pydantic>=2.0.0",
        ],
        "blockchain": [
            "cryptography>=41.0.0",
        ],
        "bridge": [
            "requests>=2.28.0",
            "urllib3>=1.26.0",
        ],
        "lite": [],  # No additional dependencies for lite version
    },
    entry_points={
        "console_scripts": [
            "ailoos=ailoos.cli.main:main",
            "ailoos-dashboard=ailoos.api.dashboard_api:create_dashboard_app",
            "ailoos-api=ailoos.api.main:main",
            "ailoos-wallet-api=ailoos.api.wallet_api:create_wallet_app",
            "ailoos-federated-api=ailoos.api.federated_api:create_federated_app",
            "ailoos-gateway-api=ailoos.api.gateway:create_gateway_app",
            "ailoos-wallet=ailoos.blockchain.wallet_manager:main",
            "ailoos-stake=ailoos.blockchain.staking_manager:main",
            "ailoos-terminal=ailoos.cli.terminal:main",  # Pointing to new location
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="Proprietary - Ailoos Technologies & Empoorio Ecosystem",
    platforms=["any"],
)
