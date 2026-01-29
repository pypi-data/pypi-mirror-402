"""
Security & Safety Checks for NetworkDoctor
"""
import time
from typing import Dict, Any
from collections import deque


class RateLimiter:
    """Rate limiter to prevent network flooding"""
    
    def __init__(self, max_requests: int = 10, time_window: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def acquire(self) -> bool:
        """
        Check if request is allowed.
        
        Returns:
            True if allowed
        """
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Check limit
        if len(self.requests) >= self.max_requests:
            return False
        
        # Add current request
        self.requests.append(now)
        return True
    
    async def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        if not self.acquire():
            # Calculate wait time
            if self.requests:
                oldest = self.requests[0]
                wait_time = self.time_window - (time.time() - oldest)
                if wait_time > 0:
                    import asyncio
                    await asyncio.sleep(wait_time)
                    return self.acquire()
        return True


class SecurityChecker:
    """Security and safety checks"""
    
    @staticmethod
    def is_safe_target(target: str) -> bool:
        """
        Check if target is safe to scan.
        
        Args:
            target: Target string
            
        Returns:
            True if safe
        """
        # Block private/localhost ranges
        unsafe_patterns = [
            "127.0.0.1",
            "localhost",
            "0.0.0.0",
            "::1",
        ]
        
        target_lower = target.lower()
        for pattern in unsafe_patterns:
            if pattern in target_lower:
                return False
        
        return True
    
    @staticmethod
    def validate_scan_scope(targets: list, max_targets: int = 100) -> bool:
        """
        Validate scan scope is reasonable.
        
        Args:
            targets: List of targets
            max_targets: Maximum allowed targets
            
        Returns:
            True if scope is valid
        """
        return len(targets) <= max_targets
    
    @staticmethod
    def check_permissions() -> Dict[str, bool]:
        """
        Check required permissions.
        
        Returns:
            Dictionary of permission checks
        """
        import os
        import socket
        
        checks = {
            "network_access": True,  # Assume true, will fail on actual use if not
            "file_read": os.access(".", os.R_OK),
            "file_write": os.access(".", os.W_OK),
        }
        
        # Test network access
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            test_socket.connect(("8.8.8.8", 53))
            test_socket.close()
            checks["network_access"] = True
        except Exception:
            checks["network_access"] = False
        
        return checks







