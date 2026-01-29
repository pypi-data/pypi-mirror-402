class TaxError(Exception):
    """Base Error"""

class AuthError(TaxError):
    """Auth Error"""
    
class ApiResponseError(Exception):
    """Api response error"""