"""
Service test fixtures and configurations.
"""
import pytest
import sys
import os

# Get project root from environment variable or use path calculation
project_root = os.environ.get("SAP_HARNESS_HOME")
if not project_root:
    # Add project root to path to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    print(f"SAP_HARNESS_HOME environment variable not set. Using calculated path: {project_root}")

# Add project root to Python path
sys.path.insert(0, project_root)

# Import directly from root conftest by getting the path and adding it to sys.path
root_conftest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_conftest_path)

# Now that paths are set up, import application modules
from models.material import (
    Material, MaterialCreate, MaterialType, MaterialStatus, UnitOfMeasure
)

# Import fixtures from parent conftest.py file
from conftest import (
    clean_services,
    state_manager_fixture,
    monitor_service_fixture,
    material_service_fixture,
    p2p_service_fixture,
    test_client,
    mock_datetime,
    async_state_manager,
    async_monitor_service,
    async_material_service,
    async_p2p_service
)

@pytest.fixture
def test_material():
    """Create a test material for testing."""
    return Material(
        material_number="TEST001",
        name="Test Material",
        description="A test material for service testing",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH,
        status=MaterialStatus.ACTIVE
    )

@pytest.fixture
def setup_test_materials(material_service_fixture):
    """Set up various test materials with different statuses"""
    # Active materials of different types
    material_service_fixture.create_material(
        MaterialCreate(
            material_number="RAW001",
            name="Raw Material",
            type=MaterialType.RAW,
            description="Active raw material"
        )
    )
    
    material_service_fixture.create_material(
        MaterialCreate(
            material_number="FIN001",
            name="Finished Product",
            type=MaterialType.FINISHED,
            description="Active finished product"
        )
    )
    
    return material_service_fixture

@pytest.fixture
async def async_test_material():
    """Async fixture creating a test material for testing."""
    return Material(
        material_number="TEST001",
        name="Test Material",
        description="A test material for service testing",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH,
        status=MaterialStatus.ACTIVE
    )

@pytest.fixture
async def async_setup_test_materials(async_material_service):
    """Async fixture setting up various test materials with different statuses"""
    # Active materials of different types
    async_material_service.create_material(
        MaterialCreate(
            material_number="RAW001",
            name="Raw Material",
            type=MaterialType.RAW,
            description="Active raw material"
        )
    )
    
    async_material_service.create_material(
        MaterialCreate(
            material_number="FIN001",
            name="Finished Product",
            type=MaterialType.FINISHED,
            description="Active finished product"
        )
    )
    
    return async_material_service
