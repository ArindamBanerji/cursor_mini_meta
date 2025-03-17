from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from models.material import Material, MaterialCreate, MaterialUpdate, MaterialType, MaterialStatus
from services.material_service import MaterialService
from services.state_manager import StateManager

router = APIRouter()

# Global state manager instance
state_manager = StateManager()

async def get_material_service() -> MaterialService:
    """Dependency to get material service instance"""
    service = MaterialService(state_manager)
    await service.initialize()
    return service

@router.get("/", response_model=List[Material])
async def list_materials(
    type: Optional[MaterialType] = None,
    status: Optional[MaterialStatus] = None,
    search_term: Optional[str] = None,
    service: MaterialService = Depends(get_material_service)
):
    """List materials with optional filtering"""
    return await service.list_materials(type=type, status=status, search_term=search_term)

@router.post("/", response_model=Material)
async def create_material(
    material: MaterialCreate,
    service: MaterialService = Depends(get_material_service)
):
    """Create a new material"""
    return await service.create_material(material)

@router.get("/{material_id}", response_model=Material)
async def get_material(
    material_id: str,
    service: MaterialService = Depends(get_material_service)
):
    """Get a material by ID"""
    return await service.get_material(material_id)

@router.put("/{material_id}", response_model=Material)
async def update_material(
    material_id: str,
    update_data: MaterialUpdate,
    service: MaterialService = Depends(get_material_service)
):
    """Update a material"""
    return await service.update_material(material_id, update_data)

@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    service: MaterialService = Depends(get_material_service)
):
    """Delete a material"""
    return await service.delete_material(material_id)

@router.post("/{material_id}/deprecate", response_model=Material)
async def deprecate_material(
    material_id: str,
    service: MaterialService = Depends(get_material_service)
):
    """Deprecate a material"""
    return await service.deprecate_material(material_id) 