#!/usr/bin/env python

"""
LUNA Adapter for bi_piper_follower Robot

This adapter allows using bi_piper_follower from luna's development directory
without modifying the installed lerobot package. Only bi_piper_follower and its
dependency (piper_follower) are loaded from the development directory, all other
modules use the installed lerobot package.
"""

import sys
import importlib
import importlib.util
from pathlib import Path

# Path to luna's development directory containing custom robots
LUNA_DEV_DIR = Path(__file__).parent.parent / "lerobot_dev"
LUNA_ROBOTS_DIR = LUNA_DEV_DIR / "robots"

# Modules to load from development directory (only bi_piper_follower and its dependency)
DEV_MODULES = ["piper_follower", "bi_piper_follower"]


def _load_module_from_dev_dir(module_name: str):
    """Load a module from luna's development directory."""
    module_dir = LUNA_ROBOTS_DIR / module_name
    module_path = module_dir / "__init__.py"
    
    if not module_path.exists():
        raise ImportError(
            f"Module {module_name} not found in development directory: {module_path}"
        )
    
    # Create a full module name
    full_module_name = f"lerobot.robots.{module_name}"
    
    # Remove from cache if already loaded
    if full_module_name in sys.modules:
        del sys.modules[full_module_name]
    
    # Also remove submodules
    for key in list(sys.modules.keys()):
        if key.startswith(f"{full_module_name}."):
            del sys.modules[key]
    
    # Ensure lerobot.robots is in sys.modules
    _ensure_lerobot_robots_package()
    
    # Create a loader that handles the module directory
    class DevModuleLoader(importlib.abc.Loader):
        def __init__(self, module_dir, module_path):
            self.module_dir = module_dir
            self.module_path = module_path
        
        def create_module(self, spec):
            # Return None to use default module creation
            return None
        
        def exec_module(self, module):
            # Set __package__, __path__, and __file__ before executing
            module.__package__ = full_module_name
            module.__path__ = [str(self.module_dir)]
            module.__file__ = str(self.module_path)
            
            # Execute the __init__.py file
            with open(self.module_path, 'rb') as f:
                code = compile(f.read(), str(self.module_path), 'exec')
                exec(code, module.__dict__)
    
    # Create spec with custom loader
    spec = importlib.util.spec_from_loader(
        full_module_name,
        DevModuleLoader(module_dir, module_path),
        origin=str(module_path)
    )
    
    if spec is None:
        raise ImportError(f"Could not create spec for {full_module_name}")
    
    module = importlib.util.module_from_spec(spec)
    
    # Register in sys.modules BEFORE executing (so relative imports work)
    sys.modules[full_module_name] = module
    
    # Execute the module
    spec.loader.exec_module(module)
    
    # Add module to lerobot.robots package namespace
    robots_pkg = sys.modules["lerobot.robots"]
    setattr(robots_pkg, module_name, module)
    
    return module


def _ensure_lerobot_robots_package():
    """Ensure lerobot.robots package is imported."""
    if "lerobot.robots" not in sys.modules:
        import lerobot.robots  # noqa: F401


def _load_dev_modules():
    """Load development modules in dependency order."""
    # First load piper_follower (dependency)
    _ensure_lerobot_robots_package()
    
    # Clear RobotConfig registry entries to avoid duplicate registration
    try:
        from lerobot.robots.config import RobotConfig
        if "piper_follower" in RobotConfig._choice_registry:
            del RobotConfig._choice_registry["piper_follower"]
        if "bi_piper_follower" in RobotConfig._choice_registry:
            del RobotConfig._choice_registry["bi_piper_follower"]
        if "bi_piper_follower_eepose" in RobotConfig._choice_registry:
            del RobotConfig._choice_registry["bi_piper_follower_eepose"]
    except (ImportError, AttributeError):
        pass
    
    # Load piper_follower first (it's a dependency of bi_piper_follower)
    _load_module_from_dev_dir("piper_follower")
    
    # Then load bi_piper_follower
    _load_module_from_dev_dir("bi_piper_follower")


# Load development modules
_load_dev_modules()

# Import the robot classes
try:
    from lerobot.robots.bi_piper_follower import (
        BiPIPERFollower,
        BiPIPERFollowerConfig,
        BiPIPERFollowerEepose,
        BiPIPERFollowerEeposeConfig,
    )
except ImportError as e:
    raise ImportError(
        f"Failed to import bi_piper_follower from development directory:\n"
        f"  Development directory: {LUNA_ROBOTS_DIR}\n"
        f"  Original error: {e}"
    )


# Explicitly register the config class with RobotConfig's choice registry
# This ensures draccus can find it during config parsing
def _register_config_class():
    """Explicitly register BiPIPERFollowerConfig and BiPIPERFollowerEeposeConfig with RobotConfig."""
    import logging
    from lerobot.robots.config import RobotConfig
    
    logger = logging.getLogger(__name__)
    
    # Register in the choice registry (used by draccus for parsing)
    if "bi_piper_follower" not in RobotConfig._choice_registry:
        RobotConfig._choice_registry["bi_piper_follower"] = BiPIPERFollowerConfig
        logger.debug("Registered bi_piper_follower config class with RobotConfig")
    
    # Register bi_piper_follower_eepose config class
    if "bi_piper_follower_eepose" not in RobotConfig._choice_registry:
        RobotConfig._choice_registry["bi_piper_follower_eepose"] = BiPIPERFollowerEeposeConfig
        logger.debug("Registered bi_piper_follower_eepose config class with RobotConfig")


# Register with make_robot_from_config by monkey patching
def _register_robot_factory():
    """Register bi_piper_follower and bi_piper_follower_eepose with lerobot's robot factory."""
    from lerobot.robots import utils
    
    # Store original function
    original_make_robot = utils.make_robot_from_config
    
    def make_robot_from_config_with_bi_piper(config):
        """Extended make_robot_from_config that includes bi_piper_follower variants."""
        if config.type == "bi_piper_follower":
            return BiPIPERFollower(config)
        elif config.type == "bi_piper_follower_eepose":
            return BiPIPERFollowerEepose(config)
        # Fall back to original function for other types
        return original_make_robot(config)
    
    # Replace the function
    utils.make_robot_from_config = make_robot_from_config_with_bi_piper


# Auto-register on import
_register_config_class()
_register_robot_factory()

# Export for use in config files
__all__ = [
    "BiPIPERFollower",
    "BiPIPERFollowerConfig",
    "BiPIPERFollowerEepose",
    "BiPIPERFollowerEeposeConfig",
]
