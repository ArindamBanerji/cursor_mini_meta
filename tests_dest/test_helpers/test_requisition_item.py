"""
Test script to diagnose RequisitionItem validation issues
"""
import logging
import sys
from pathlib import Path
from pydantic import ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    logger.info(f"Added {project_root} to Python path")

def test_requisition_item():
    """Test RequisitionItem creation with proper fields to fix validation errors in tests."""
    from tests_dest.test_helpers.service_imports import RequisitionItem
    
    logger.info("Testing RequisitionItem class fields")
    
    # Test minimal required fields
    try:
        item = RequisitionItem(
            item_number=1,
            material_number="TEST-001", 
            description="Test Item",
            quantity=10, 
            price=100.0,
            unit="EA"
        )
        logger.info(f"✓ Created RequisitionItem with required fields: {item}")
    except ValidationError as e:
        logger.error(f"✗ Error creating RequisitionItem with required fields: {e}")
        for error in e.errors():
            logger.error(f"  - {error}")
    
    # Test with missing fields - should fail
    logger.info("Testing RequisitionItem creation with missing fields (expected to fail)")
    try:
        item = RequisitionItem(
            item_number=1,
            material_number="TEST-001",
            quantity=10,
            unit="EA"
        )
        logger.error(f"✗ Created RequisitionItem without required fields (should have failed): {item}")
    except ValidationError as e:
        logger.info(f"✓ Correctly failed to create RequisitionItem without required fields")
        for error in e.errors():
            logger.info(f"  - {error}")

def test_material_status_update():
    """Test updating material status using enum value directly."""
    from tests_dest.test_helpers.service_imports import get_material_service, MaterialCreate, MaterialStatus, MaterialType, UnitOfMeasure
    
    logger.info("Testing material service update with direct MaterialStatus enum")
    
    # Create material service
    material_service = get_material_service()
    
    # Create a test material
    material = material_service.create_material(
        MaterialCreate(
            name="Status Test Material",
            description="Material for testing status updates",
            type=MaterialType.RAW,
            base_unit=UnitOfMeasure.EACH,
            status=MaterialStatus.ACTIVE
        )
    )
    logger.info(f"✓ Created test material: {material.material_number}")
    
    # Get current status
    logger.info(f"Current status: {material.status}")
    
    try:
        # Try updating with status enum directly - this is what integration test is doing
        material_id = material.material_number
        
        # Create a MaterialUpdate with just status change
        from models.material import MaterialUpdate
        update_data = MaterialUpdate(status=MaterialStatus.INACTIVE)
        
        # Update material
        updated = material_service.update_material(material_id, update_data)
        logger.info(f"✓ Updated material status with MaterialUpdate: {updated.status}")
        
        # Try update directly with MaterialStatus enum
        from models.material import MaterialStatus
        updated = material_service.update_material(material_id, MaterialStatus.ACTIVE)
        logger.info(f"✓ Updated material status with direct enum: {updated.status}")
        
    except Exception as e:
        logger.error(f"✗ Error updating material status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("===== RUNNING REQUISITION ITEM AND MATERIAL STATUS DIAGNOSTICS =====")
    test_requisition_item()
    test_material_status_update()
    logger.info("===== DIAGNOSTICS COMPLETE =====") 