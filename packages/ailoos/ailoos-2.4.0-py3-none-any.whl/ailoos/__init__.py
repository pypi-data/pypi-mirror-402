"""
AILOOS - Artificial Intelligence for Logistics and Supply Chain
"""

import warnings
import logging
import os

__version__ = "2.3.0"

# Configure logging first to capture startup events
logger = logging.getLogger(__name__)

# Suppress noisy 3rd party warnings for cleaner startup
# Only if not in debug mode
if os.getenv("DEBUG_MODE", "false").lower() != "true":
    # Bitsandbytes GPU warning (expected on simple setups)
    warnings.filterwarnings("ignore", message=".*bitsandbytes was compiled without GPU support.*")
    
    # PyNVML deprecation (internal to some libraries)
    warnings.filterwarnings("ignore", category=UserWarning, module="pynvml")
    
    # Flash Attention missing (we handle this gracefully now)
    warnings.filterwarnings("ignore", message=".*Flash Attention 2 not available.*")

# Initialize core packages if needed
# (Optional lazy loading logic could go here)
