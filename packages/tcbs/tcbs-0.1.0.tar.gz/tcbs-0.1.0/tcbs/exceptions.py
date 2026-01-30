"""Custom exceptions for TCBS SDK"""


class TCBSAuthError(Exception):
    """Raised when authentication fails"""
    pass


class TCBSAPIError(Exception):
    """Raised when API returns non-200 status or business logic error"""
    pass
