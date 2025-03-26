import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

# Import all needed components from the service_imports module
from tests_dest.test_helpers.service_imports import (
    Material,
    MaterialCreate,
    MaterialStatus,
    MaterialType,
    UnitOfMeasure,
    Requisition,
    RequisitionCreate,
    RequisitionItem,
    Order,
    DocumentStatus,
    get_material_service,
    get_p2p_service,
    NotFoundError,
    ValidationError,
    ConflictError
)

class TestMaterialP2PIntegration:
    """
    Tests for the integration between Material and P2P services.
    """
    
    def setup_method(self):
        """Set up test resources before each test"""
        self.material_service = get_material_service()
        self.p2p_service = get_p2p_service()
        
        # Create test materials for use in tests
        self.material1 = self.material_service.create_material(
            MaterialCreate(
                name="Test Material 1",
                description="Test Material Status",
                type=MaterialType.RAW,
                base_unit=UnitOfMeasure.EACH,
                status=MaterialStatus.ACTIVE
            )
        )
        
        self.material2 = self.material_service.create_material(
            MaterialCreate(
                name="Test Material 2",
                description="Test Material Status",
                type=MaterialType.RAW,
                base_unit=UnitOfMeasure.EACH,
                status=MaterialStatus.ACTIVE
            )
        )
        
        # Create a material with specific ID "MAT001" for tests that reference it directly
        self.mat001 = self.material_service.create_material(
            MaterialCreate(
                material_number="MAT001",
                name="Material MAT001",
                description="Test material with fixed ID",
                type=MaterialType.RAW,
                base_unit=UnitOfMeasure.EACH,
                status=MaterialStatus.ACTIVE
            )
        )
        
    def test_create_requisition_with_materials(self):
        """Test creating a requisition that references materials"""
        
        # Create a requisition with a valid material reference
        requisition = self.p2p_service.create_requisition(
            RequisitionCreate(
                document_number="REQTEST001",
                description="Test Material Requisition",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number=self.material1.material_number,
                        description="Test Material Item 1",
                        quantity=10,
                        price=100.0,
                        unit="EA"
                    )
                ]
            )
        )
        
        # Verify the requisition was created successfully
        assert requisition.document_number == "REQTEST001"
        assert len(requisition.items) == 1
        assert requisition.items[0].material_number == self.material1.material_number
        
        # Verify we can retrieve it
        retrieved = self.p2p_service.get_requisition("REQTEST001")
        assert retrieved.document_number == "REQTEST001"
        
    def test_create_requisition_with_invalid_material(self):
        """Test creating a requisition with an invalid material reference"""
        
        # Attempt to create a requisition with an invalid material reference
        with pytest.raises(ValidationError):
            self.p2p_service.create_requisition(
                RequisitionCreate(
                    document_number="REQINVALID",
                    description="Invalid Material Requisition",
                    requester="Test User",
                    items=[
                        RequisitionItem(
                            item_number=1,
                            material_number="NONEXISTENT",
                            description="Invalid Material Item",
                            quantity=10,
                            price=100.0,
                            unit="EA"
                        )
                    ]
                )
            )
            
    def test_create_requisition_with_inactive_material(self):
        """Test creating a requisition with an inactive material"""
        
        # Change material status to DEPRECATED (which should be rejected by validate_material_active)
        self.material_service.update_material(
            self.mat001.material_number,
            MaterialStatus.DEPRECATED
        )
        
        # Attempt to create a requisition with the deprecated material
        with pytest.raises(ValidationError):
            self.p2p_service.create_requisition(
                RequisitionCreate(
                    document_number="REQINACTIVE",
                    description="Inactive Material Requisition",
                    requester="Test User",
                    items=[
                        RequisitionItem(
                            item_number=1,
                            material_number="MAT001",
                            description="Inactive Material Item",
                            quantity=10,
                            price=100.0,
                            unit="EA"
                        )
                    ]
                )
            )
            
    def test_end_to_end_procurement_flow(self):
        """Test the end-to-end procurement flow from requisition to order"""
        
        # Create a requisition with materials
        requisition = self.p2p_service.create_requisition(
            RequisitionCreate(
                document_number="REQSTATUS",
                description="Test Material Status",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number="MAT001",
                        description="Test Material Status Item",
                        quantity=10,
                        price=50.0,
                        unit="EA"
                    )
                ]
            )
        )
        
        # Submit the requisition
        submitted = self.p2p_service.submit_requisition(requisition.document_number)
        assert submitted.status == DocumentStatus.SUBMITTED
        
        # Approve the requisition
        approved = self.p2p_service.approve_requisition(requisition.document_number)
        assert approved.status == DocumentStatus.APPROVED
        
        # Create an order from the requisition
        order = self.p2p_service.create_order_from_requisition(
            requisition.document_number,
            vendor="Test Vendor"
        )
        
        # Verify order details
        assert order.requisition_reference == requisition.document_number
        assert len(order.items) == 1
        assert order.items[0].material_number == "MAT001"
        
        # Verify requisition status updated
        updated_req = self.p2p_service.get_requisition(requisition.document_number)
        assert updated_req.status == DocumentStatus.ORDERED
        
    def test_material_status_affects_procurement(self):
        """Test that material status changes affect procurement processes"""
        
        # Create a requisition with a valid material
        requisition = self.p2p_service.create_requisition(
            RequisitionCreate(
                document_number="REQSTATUS",
                description="Test Material Status",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number="MAT001",
                        description="Test Material Status Item",
                        quantity=10,
                        price=75.0,
                        unit="EA"
                    )
                ]
            )
        )
        
        # Submit and approve the requisition
        self.p2p_service.submit_requisition(requisition.document_number)
        self.p2p_service.approve_requisition(requisition.document_number)
        
        # Change material status to deprecated
        self.material_service.update_material(
            "MAT001",
            MaterialStatus.DEPRECATED
        )
        
        # Attempt to create an order - should still succeed because requisition was already approved
        order = self.p2p_service.create_order_from_requisition(
            requisition.document_number,
            vendor="Test Vendor"
        )
        
        assert order.requisition_reference == requisition.document_number 