"""
IntGate API Client implementation.
"""

import requests
import threading
import time
from typing import Optional, Dict, Any, Callable
from .exceptions import IntGateAPIError, IntGateValidationError


class IntGateClient:
    """
    Client for interacting with the IntGate license verification API.
    
    Args:
        team_id: Your team's UUID from the IntGate dashboard.
        base_url: The base URL for the IntGate API (default: https://license.intserver.com/api/v1).
    """
    
    def __init__(self, team_id: str, base_url: str = "https://license.intserver.com/api/v1"):
        """Initialize the IntGate client."""
        if not team_id:
            raise IntGateValidationError("team_id is required")
        
        self.team_id = team_id
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Automatic heartbeat properties
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_running = False
        self._heartbeat_interval = 1800  # 30 minutes default
        self._heartbeat_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._heartbeat_error_callback: Optional[Callable[[Exception], None]] = None
        self._last_heartbeat_result: Optional[Dict[str, Any]] = None
        self._heartbeat_lock = threading.Lock()
    
    def verify_license(
        self,
        license_key: str,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        challenge: Optional[str] = None,
        version: Optional[str] = None,
        hardware_identifier: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a license key with the IntGate backend.
        
        This endpoint validates a license key and returns license information,
        customer data, and product details. Typically called when software starts.
        
        Args:
            license_key: IntGate license key (format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX).
            customer_id: Customer UUID (required if strict customers enabled).
            product_id: Product UUID (required if strict products enabled).
            challenge: Client-generated random string for request signing (no spaces).
            version: Software version identifier (3-255 chars, no spaces).
            hardware_identifier: Unique hardware identifier (10-1000 chars, no spaces).
            branch: Product branch name (2-255 chars).
        
        Returns:
            Dict containing:
                - data: License, customer, and product information
                - result: Verification result with timestamp, valid flag, details, code, and challengeResponse
        
        Raises:
            IntGateValidationError: If required parameters are invalid.
            IntGateAPIError: If the API request fails.
        """
        if not license_key:
            raise IntGateValidationError("license_key is required")
        
        payload = {
            "licenseKey": license_key
        }
        
        if customer_id:
            payload["customerId"] = customer_id
        if product_id:
            payload["productId"] = product_id
        if challenge:
            payload["challenge"] = challenge
        if version:
            payload["version"] = version
        if hardware_identifier:
            payload["hardwareIdentifier"] = hardware_identifier
        if branch:
            payload["branch"] = branch
        
        url = f"{self.base_url}/client/teams/{self.team_id}/verification/verify"
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Handle null data field (occurs when no returned fields are configured in Team Settings)
            if result and result.get("data") is None:
                result["data"] = {}
            
            return result
        except requests.exceptions.HTTPError as e:
            raise IntGateAPIError(
                f"API request failed: {str(e)}",
                status_code=e.response.status_code if e.response else None,
                response_data=e.response.json() if e.response and e.response.content else None
            )
        except requests.exceptions.RequestException as e:
            raise IntGateAPIError(f"Network error: {str(e)}")
    
    def license_heartbeat(
        self,
        license_key: str,
        hardware_identifier: str,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        challenge: Optional[str] = None,
        version: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a heartbeat to determine if a device is still active.
        
        This endpoint should be called at regular intervals (e.g., every 30 minutes).
        It validates the license key similar to verify_license.
        
        Args:
            license_key: IntGate license key (format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX).
            hardware_identifier: Unique hardware identifier (10-1000 chars, no spaces).
            customer_id: Customer UUID.
            product_id: Product UUID.
            challenge: Client-generated random string for request signing (no spaces).
            version: Software version identifier (3-255 chars, no spaces).
            branch: Product branch name (2-255 chars).
        
        Returns:
            Dict containing:
                - data: License information (ipLimit, hwidLimit, expirationType)
                - result: Heartbeat result with timestamp, valid flag, details, and code
        
        Raises:
            IntGateValidationError: If required parameters are invalid.
            IntGateAPIError: If the API request fails.
        """
        if not license_key:
            raise IntGateValidationError("license_key is required")
        if not hardware_identifier:
            raise IntGateValidationError("hardware_identifier is required")
        
        payload = {
            "licenseKey": license_key,
            "hardwareIdentifier": hardware_identifier
        }
        
        if customer_id:
            payload["customerId"] = customer_id
        if product_id:
            payload["productId"] = product_id
        if challenge:
            payload["challenge"] = challenge
        if version:
            payload["version"] = version
        if branch:
            payload["branch"] = branch
        
        url = f"{self.base_url}/client/teams/{self.team_id}/verification/heartbeat"
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Handle null data field (occurs when no returned fields are configured in Team Settings)
            if result and result.get("data") is None:
                result["data"] = {}
            
            return result
        except requests.exceptions.HTTPError as e:
            raise IntGateAPIError(
                f"API request failed: {str(e)}",
                status_code=e.response.status_code if e.response else None,
                response_data=e.response.json() if e.response and e.response.content else None
            )
        except requests.exceptions.RequestException as e:
            raise IntGateAPIError(f"Network error: {str(e)}")
    
    def download_release(
        self,
        license_key: str,
        product_id: str,
        session_key: str,
        hardware_identifier: str,
        version: str,
        customer_id: Optional[str] = None,
        branch: Optional[str] = None
    ) -> bytes:
        """
        Download an encrypted release file.
        
        This endpoint is primarily for languages that support loading code remotely
        (e.g., Java classloaders). The file is encrypted using the provided session key.
        
        Args:
            license_key: IntGate license key (format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX).
            product_id: Product UUID.
            session_key: Unique session identifier encrypted using team's public key (10-1000 chars, no spaces).
            hardware_identifier: Unique hardware identifier (10-1000 chars, no spaces).
            version: Software version identifier (3-255 chars, no spaces).
            customer_id: Customer UUID (required if strict customers enabled).
            branch: Product branch name (2-255 chars).
        
        Returns:
            bytes: Encrypted file content. Must be decrypted using the same session key.
        
        Raises:
            IntGateValidationError: If required parameters are invalid.
            IntGateAPIError: If the API request fails.
        """
        if not license_key:
            raise IntGateValidationError("license_key is required")
        if not product_id:
            raise IntGateValidationError("product_id is required")
        if not session_key:
            raise IntGateValidationError("session_key is required")
        if not hardware_identifier:
            raise IntGateValidationError("hardware_identifier is required")
        if not version:
            raise IntGateValidationError("version is required")
        
        params = {
            "licenseKey": license_key,
            "productId": product_id,
            "sessionKey": session_key,
            "hardwareIdentifier": hardware_identifier,
            "version": version
        }
        
        if customer_id:
            params["customerId"] = customer_id
        if branch:
            params["branch"] = branch
        
        url = f"{self.base_url}/client/teams/{self.team_id}/verification/classloader"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.content
        except requests.exceptions.HTTPError as e:
            raise IntGateAPIError(
                f"API request failed: {str(e)}",
                status_code=e.response.status_code if e.response else None,
                response_data=e.response.text if e.response else None
            )
        except requests.exceptions.RequestException as e:
            raise IntGateAPIError(f"Network error: {str(e)}")
    
    def start_automatic_heartbeat(
        self,
        license_key: str,
        hardware_identifier: str,
        interval: int = 1800,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
        **kwargs
    ) -> None:
        """
        Start automatic heartbeat in the background.
        
        Args:
            license_key: IntGate license key.
            hardware_identifier: Unique hardware identifier.
            interval: Interval in seconds between heartbeats (default: 1800 = 30 minutes).
            callback: Optional callback function called with heartbeat result on success.
            error_callback: Optional callback function called with exception on error.
            **kwargs: Additional parameters to pass to license_heartbeat (customer_id, product_id, etc.).
        """
        if self._heartbeat_running:
            raise IntGateValidationError("Automatic heartbeat is already running")
        
        self._heartbeat_interval = interval
        self._heartbeat_callback = callback
        self._heartbeat_error_callback = error_callback
        self._heartbeat_running = True
        
        def heartbeat_worker():
            while self._heartbeat_running:
                try:
                    result = self.license_heartbeat(
                        license_key=license_key,
                        hardware_identifier=hardware_identifier,
                        **kwargs
                    )
                    
                    with self._heartbeat_lock:
                        self._last_heartbeat_result = result
                    
                    if self._heartbeat_callback:
                        self._heartbeat_callback(result)
                        
                except Exception as e:
                    if self._heartbeat_error_callback:
                        self._heartbeat_error_callback(e)
                
                # Wait for the interval, checking periodically if we should stop
                for _ in range(self._heartbeat_interval):
                    if not self._heartbeat_running:
                        break
                    time.sleep(1)
        
        self._heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        self._heartbeat_thread.start()
    
    def stop_automatic_heartbeat(self) -> None:
        """Stop the automatic heartbeat."""
        if self._heartbeat_running:
            self._heartbeat_running = False
            if self._heartbeat_thread:
                self._heartbeat_thread.join(timeout=5)
                self._heartbeat_thread = None
    
    def get_last_heartbeat_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the result of the last automatic heartbeat.
        
        Returns:
            Dict containing the last heartbeat result, or None if no heartbeat has run yet.
        """
        with self._heartbeat_lock:
            return self._last_heartbeat_result
    
    def is_heartbeat_running(self) -> bool:
        """Check if automatic heartbeat is currently running."""
        return self._heartbeat_running

