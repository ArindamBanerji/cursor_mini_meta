"""
Diagnostic tests for P2P service initialization.

This file provides controlled tests to analyze how P2P service is initialized
with different dependencies, especially focusing on the case where only 
a state manager is provided.
"""
import os
import sys
import logging
import unittest
from typing import Any, Dict, Optional, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("p2p_init_diagnostic")

# Import helper functions
from import_helper import fix_imports, setup_test_env_vars
fix_imports()
logger.info("Successfully initialized test paths from import_helper")

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = test_dir.parent.parent

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    logger.info(f"Added {project_root} to Python path")
else:
    raise RuntimeError("Could not detect project root")

# Import from service_imports instead of directly from services
from tests_dest.test_helpers.service_imports import (
    StateManager,
    MaterialService,
    P2PService,
    get_p2p_service
)

class StateManagerTest:
    """Mock StateManager for testing."""
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """Initialize with optional initial state."""
        self.state_data = initial_state or {}
        self.id = id(self)
        logger.info(f"Created test StateManager with id={self.id}")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Mock getting state by key."""
        logger.debug(f"StateManager({self.id}).get_state({key})")
        return self.state_data.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """Mock setting state for key."""
        logger.debug(f"StateManager({self.id}).set_state({key}, {value})")
        self.state_data[key] = value
    
    def delete_state(self, key: str) -> None:
        """Mock deleting state for key."""
        logger.debug(f"StateManager({self.id}).delete_state({key})")
        if key in self.state_data:
            del self.state_data[key]
    
    def persist(self) -> None:
        """Mock persisting state."""
        logger.debug(f"StateManager({self.id}).persist()")
        pass
    
    # Add required methods to match expected interface
    
    def get(self, key: str, default: Any = None) -> Any:
        """Implementation of get to match StateManager interface."""
        logger.debug(f"StateManager({self.id}).get({key})")
        return self.state_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Implementation of set to match StateManager interface."""
        logger.debug(f"StateManager({self.id}).set({key}, {value})")
        self.state_data[key] = value
    
    def delete(self, key: str) -> None:
        """Implementation of delete to match StateManager interface."""
        logger.debug(f"StateManager({self.id}).delete({key})")
        if key in self.state_data:
            del self.state_data[key]
    
    def clear(self) -> None:
        """Implementation of clear to match StateManager interface."""
        logger.debug(f"StateManager({self.id}).clear()")
        self.state_data.clear()
    
    def get_all_keys(self) -> List[str]:
        """Implementation of get_all_keys to match StateManager interface."""
        logger.debug(f"StateManager({self.id}).get_all_keys()")
        return list(self.state_data.keys())

class MaterialServiceTest:
    """Test double for MaterialService used in isolation tests."""
    
    def __init__(self, state_manager: Any = None, config: Optional[Dict[str, Any]] = None):
        """Initialize with state manager and config."""
        self.state_manager = state_manager
        self.config = config or {}
        self.id = id(self)
        logger.info(f"Created test MaterialService with id={self.id}, state_manager_id={id(state_manager)}")
    
    def get_material(self, material_id: str) -> Dict[str, Any]:
        """Mock getting a material."""
        logger.debug(f"MaterialService({self.id}).get_material({material_id})")
        return {"id": material_id, "name": f"Test Material {material_id}"}

class P2PServiceInitTest(unittest.TestCase):
    """Tests for P2P service initialization."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Record the current state of sys.path
        cls.original_sys_path = sys.path.copy()
        
        # Determine project root and add to path if not already there
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_dir = os.path.dirname(current_dir)  # tests-dest directory
        cls.project_root = os.path.dirname(cls.test_dir)  # project root
        
        # Add necessary paths for imports
        for path in [cls.project_root, cls.test_dir]:
            if path not in sys.path:
                sys.path.insert(0, path)
                logger.debug(f"Added {path} to sys.path")
        
        # Log the environment
        logger.info(f"Test directory: {cls.test_dir}")
        logger.info(f"Project root: {cls.project_root}")
        
        # Use imports from service_imports
        cls.P2PService = P2PService
        cls.get_p2p_service = get_p2p_service
        logger.info("Successfully imported P2P service classes from service_imports")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        # Restore the original sys.path
        sys.path = cls.original_sys_path
    
    def test_direct_initialization_both_dependencies(self):
        """Test creating a P2PService with explicit state manager and material service."""
        # Create test doubles
        state_manager = StateManagerTest()
        material_service = MaterialServiceTest(state_manager)
        
        # Create P2P service with both dependencies
        p2p_service = self.P2PService(state_manager, material_service)
        logger.info(f"P2P service created with id={id(p2p_service)}")
        
        # Verify the dependencies were set correctly
        self.assertIs(p2p_service.state_manager, state_manager)
        self.assertIs(p2p_service.material_service, material_service)
        
        logger.info("Test passed: P2P service initialized correctly with both dependencies")
    
    def test_direct_initialization_state_only(self):
        """Test creating a P2PService with only state manager."""
        # Create test state manager
        state_manager = StateManagerTest()
        
        # Create P2P service with only state manager
        p2p_service = self.P2PService(state_manager, None)
        logger.info(f"P2P service created with id={id(p2p_service)}")
        
        # Verify the state manager was set correctly
        self.assertIs(p2p_service.state_manager, state_manager)
        
        # Verify a material service was created
        self.assertIsNotNone(p2p_service.material_service)
        logger.info(f"Auto-created material service with id={id(p2p_service.material_service)}")
        
        logger.info("Test passed: P2P service initialized correctly with only state manager")
    
    def test_factory_function_state_only(self):
        """Test get_p2p_service factory with only state manager."""
        # Create test state manager
        state_manager = StateManagerTest()
        
        # Use the imported function from service_imports
        p2p_service = get_p2p_service(state_manager_instance=state_manager)
        logger.info(f"P2P service created via factory with id={id(p2p_service)}")
        
        # Verify the state manager was set correctly
        self.assertIs(p2p_service.state_manager, state_manager)
        
        # Verify a material service was created
        self.assertIsNotNone(p2p_service.material_service)
        logger.info(f"Auto-created material service (via factory) with id={id(p2p_service.material_service)}")
        
        logger.info("Test passed: P2P service created via factory with only state manager")
    
    def test_factory_function_both_dependencies(self):
        """Test get_p2p_service factory with both dependencies."""
        # Create test doubles
        state_manager = StateManagerTest()
        material_service = MaterialServiceTest(state_manager)
        
        # Use the imported function from service_imports
        p2p_service = get_p2p_service(
            state_manager_instance=state_manager,
            material_service_instance=material_service
        )
        logger.info(f"P2P service created via factory with id={id(p2p_service)}")
        
        # Verify the dependencies were set correctly
        self.assertIs(p2p_service.state_manager, state_manager)
        self.assertIs(p2p_service.material_service, material_service)
        
        logger.info("Test passed: P2P service created via factory with both dependencies")

    def test_service_attribute_access(self):
        """Test accessing attributes and methods of P2P service."""
        # Create test doubles
        state_manager = StateManagerTest()
        
        # Use the imported function from service_imports
        p2p_service = get_p2p_service(state_manager_instance=state_manager)
        
        # Test accessing various attributes and methods
        attributes_to_check = [
            "state_manager",
            "material_service",
            "get_requisition",
            "create_requisition",
            "update_requisition",
            "delete_requisition",
            "get_order",
            "create_order",
            "update_order",
            "delete_order"
        ]
        
        for attr in attributes_to_check:
            # Use hasattr first to check if attribute exists
            self.assertTrue(hasattr(p2p_service, attr), f"P2P service missing attribute: {attr}")
            
            # Then get the attribute value
            value = getattr(p2p_service, attr)
            logger.info(f"P2P service attribute '{attr}' exists: {value}")
            self.assertIsNotNone(value)

if __name__ == "__main__":
    unittest.main() 