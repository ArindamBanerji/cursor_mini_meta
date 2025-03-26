"""
Integration tests for service interactions and dependencies.
This package contains tests that verify how different services
work together and handle errors across service boundaries.
"""

from .test_material_p2p_integration import TestMaterialP2PIntegration
from .test_monitor_service_integration import TestMonitorServiceIntegration
from .test_service_registry import TestServiceRegistry
from .test_error_propagation import TestErrorPropagation

__all__ = [
    'TestMaterialP2PIntegration',
    'TestMonitorServiceIntegration',
    'TestServiceRegistry',
    'TestErrorPropagation'
] 