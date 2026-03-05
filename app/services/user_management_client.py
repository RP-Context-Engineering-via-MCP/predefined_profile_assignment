"""User Management Service HTTP Client.

Provides interface to interact with the external User Management Service
for profile-related user data.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserManagementClient:
    """HTTP client for User Management Service.
    
    Handles all communication with the external user management service
    for profile-assignment-related user data.
    """

    def __init__(self):
        """Initialize client with base URL from config."""
        self.base_url = settings.USER_MANAGEMENT_SERVICE_URL
        self.timeout = 10.0

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data from User Management Service.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with profile data or None if user not found:
            {
                "user_id": "...",
                "profile_mode": "COLD_START",
                "predefined_profile_id": "P3",
                "dynamic_profile_id": null,
                "dynamic_profile_confidence": 0.0,
                "dynamic_profile_ready": false,
                "fallback_profile_id": null,
                "fallback_reason": null,
                "fallback_activated_at": null
            }
        """
        url = f"{self.base_url}/api/users/{user_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    logger.warning(f"User {user_id} not found in User Management Service")
                    return None
                
                response.raise_for_status()
                user_data = response.json()
                
                logger.debug(f"Retrieved user profile for {user_id}: mode={user_data.get('profile_mode')}")
                return user_data
                
        except httpx.TimeoutException:
            logger.error(f"Timeout getting user {user_id} from User Management Service")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user {user_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id} from User Management Service: {e}")
            return None

    async def update_user_profile(
        self, 
        user_id: str, 
        predefined_profile_id: Optional[str] = None,
        profile_mode: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Update user profile fields in User Management Service.
        
        Args:
            user_id: User identifier
            predefined_profile_id: Profile to assign
            profile_mode: Profile mode to set
            **kwargs: Additional fields to update
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/users/{user_id}"
        
        # Build update payload
        payload = {}
        if predefined_profile_id is not None:
            payload["predefined_profile_id"] = predefined_profile_id
        if profile_mode is not None:
            payload["profile_mode"] = profile_mode
        payload.update(kwargs)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(url, json=payload)
                response.raise_for_status()
                
                logger.info(f"Updated user {user_id} profile: {payload}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating user {user_id}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False

    async def activate_fallback(
        self,
        user_id: str,
        fallback_profile_id: str,
        fallback_reason: str
    ) -> bool:
        """Activate fallback profile for user.
        
        Args:
            user_id: User identifier
            fallback_profile_id: Profile to use as fallback
            fallback_reason: Reason for fallback
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/users/{user_id}/fallback/activate"
        
        payload = {
            "fallback_profile_id": fallback_profile_id,
            "fallback_reason": fallback_reason
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                logger.info(f"Activated fallback for user {user_id}: {fallback_profile_id}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error activating fallback for user {user_id}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to activate fallback for user {user_id}: {e}")
            return False

    async def deactivate_fallback(self, user_id: str) -> bool:
        """Deactivate fallback profile for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/users/{user_id}/fallback/deactivate"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url)
                response.raise_for_status()
                
                logger.info(f"Deactivated fallback for user {user_id}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error deactivating fallback for user {user_id}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate fallback for user {user_id}: {e}")
            return False

    def get_user_profile_sync(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous version of get_user_profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with profile data or None if user not found
        """
        url = f"{self.base_url}/api/users/{user_id}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                
                if response.status_code == 404:
                    logger.warning(f"User {user_id} not found in User Management Service")
                    return None
                
                response.raise_for_status()
                user_data = response.json()
                
                logger.debug(f"Retrieved user profile for {user_id}: mode={user_data.get('profile_mode')}")
                return user_data
                
        except httpx.TimeoutException:
            logger.error(f"Timeout getting user {user_id} from User Management Service")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user {user_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id} from User Management Service: {e}")
            return None

    def update_user_profile_sync(
        self, 
        user_id: str, 
        predefined_profile_id: Optional[str] = None,
        profile_mode: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Synchronous version of update_user_profile.
        
        Args:
            user_id: User identifier
            predefined_profile_id: Profile to assign
            profile_mode: Profile mode to set
            **kwargs: Additional fields to update
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/users/{user_id}"
        
        # Build update payload
        payload = {}
        if predefined_profile_id is not None:
            payload["predefined_profile_id"] = predefined_profile_id
        if profile_mode is not None:
            payload["profile_mode"] = profile_mode
        payload.update(kwargs)
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.put(url, json=payload)
                response.raise_for_status()
                
                logger.info(f"Updated user {user_id} profile: {payload}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating user {user_id}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False
