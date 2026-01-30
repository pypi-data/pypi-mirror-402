"""
Custom exceptions for PyKAP
"""


class KAPError(Exception):
    """Base exception for KAP API errors"""
    pass


class KAPAuthenticationError(KAPError):
    """Authentication related errors"""
    pass


class KAPAPIError(KAPError):
    """API request errors"""
    
    def __init__(self, message: str, status_code: int = None, 
                 error_code: str = None, error_message: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        
    def __str__(self):
        parts = [super().__str__()]
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")
        if self.error_message:
            parts.append(f"Error Message: {self.error_message}")
        if self.status_code:
            parts.append(f"Status Code: {self.status_code}")
        return " | ".join(parts)


class KAPValidationError(KAPError):
    """Input validation errors"""
    pass
