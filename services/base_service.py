"""
Base service class that provides common functionality for all services.
"""

from typing import Any, Dict, Optional, TypeVar, Generic
from datetime import datetime
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class BaseService(Generic[T]):
    """Base service class that provides common functionality.
    
    This class provides:
    1. State management
    2. Error handling
    3. Logging
    4. Common CRUD operations
    """
    
    def __init__(self, state_manager: Optional[Any] = None):
        """Initialize the base service.
        
        Args:
            state_manager: Optional state manager for persistence
        """
        self.state_manager = state_manager
        self._state: Dict[str, Any] = {}
        self._last_updated: Optional[datetime] = None
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state.
        
        Returns:
            Current state dictionary
        """
        return self._state.copy()
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the current state.
        
        Args:
            state: New state dictionary
        """
        self._state = state.copy()
        self._last_updated = datetime.now()
        logger.debug(f"Updated state in {self.__class__.__name__}")
    
    def get_last_updated(self) -> Optional[datetime]:
        """Get the last update timestamp.
        
        Returns:
            Last update timestamp or None if never updated
        """
        return self._last_updated
    
    def validate_state(self) -> bool:
        """Validate the current state.
        
        Returns:
            True if state is valid, False otherwise
        """
        try:
            # Basic validation - ensure state is a dict
            if not isinstance(self._state, dict):
                logger.error(f"Invalid state type in {self.__class__.__name__}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating state in {self.__class__.__name__}: {e}")
            return False
    
    def save_state(self) -> bool:
        """Save state to state manager if available.
        
        Returns:
            True if save successful, False otherwise
        """
        if not self.state_manager:
            logger.warning(f"No state manager available for {self.__class__.__name__}")
            return False
            
        try:
            self.state_manager.save_state(self._state)
            logger.info(f"Saved state for {self.__class__.__name__}")
            return True
        except Exception as e:
            logger.error(f"Error saving state in {self.__class__.__name__}: {e}")
            return False
    
    def load_state(self) -> bool:
        """Load state from state manager if available.
        
        Returns:
            True if load successful, False otherwise
        """
        if not self.state_manager:
            logger.warning(f"No state manager available for {self.__class__.__name__}")
            return False
            
        try:
            state = self.state_manager.load_state()
            if state:
                self.set_state(state)
                logger.info(f"Loaded state for {self.__class__.__name__}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading state in {self.__class__.__name__}: {e}")
            return False
    
    def clear_state(self) -> None:
        """Clear the current state."""
        self._state = {}
        self._last_updated = None
        logger.info(f"Cleared state in {self.__class__.__name__}")
    
    def get_item(self, key: str, default: Any = None) -> Any:
        """Get an item from state.
        
        Args:
            key: Item key
            default: Default value if key not found
            
        Returns:
            Item value or default
        """
        return self._state.get(key, default)
    
    def set_item(self, key: str, value: Any) -> None:
        """Set an item in state.
        
        Args:
            key: Item key
            value: Item value
        """
        self._state[key] = value
        self._last_updated = datetime.now()
        logger.debug(f"Updated item {key} in {self.__class__.__name__}")
    
    def delete_item(self, key: str) -> bool:
        """Delete an item from state.
        
        Args:
            key: Item key
            
        Returns:
            True if item was deleted, False if not found
        """
        if key in self._state:
            del self._state[key]
            self._last_updated = datetime.now()
            logger.debug(f"Deleted item {key} from {self.__class__.__name__}")
            return True
        return False 