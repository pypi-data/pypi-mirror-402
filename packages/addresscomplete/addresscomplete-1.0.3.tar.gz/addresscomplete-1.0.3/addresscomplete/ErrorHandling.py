"""Error Handling for AddressComplete package."""
from abc import ABC, abstractmethod

# Response Errors

class ResponseError(ABC, Exception):
    """Base exception for response errors."""
    def __init__(self, message):
        """Initialize the ResponseError."""
        super().__init__(message)
        
    @abstractmethod
    def _raise_error(self, error_code):
        """Raise the appropriate error based on the error code."""
        raise NotImplementedError("Subclasses must implement this method")

class FindError(ResponseError):
    """Base exception for find errors."""
    def __init__(self, error_code):
        self._raise_error(error_code)
        
    def _raise_error(self, error_code):
        if error_code in GENERAL_ERROR_CODE_MAP:
            raise GENERAL_ERROR_CODE_MAP[error_code]
        elif error_code in FIND_ERROR_CODE_MAP:
            raise FIND_ERROR_CODE_MAP[error_code]
        else:
            raise UnknownError()

class RetrieveError(ResponseError):
    """Base exception for retrieve errors."""
    def __init__(self, error_code):
        self._raise_error(error_code)
        
    
    def _raise_error(self, error_code):
        if error_code in GENERAL_ERROR_CODE_MAP:
            raise GENERAL_ERROR_CODE_MAP[error_code]
        elif error_code in RETRIEVE_ERROR_CODE_MAP:
            raise RETRIEVE_ERROR_CODE_MAP[error_code]
        else:
            raise UnknownError()

class CountryInvalidError(Exception):
    """Country code is invalid."""
    def __init__(self):
        super().__init__("Country code is invalid")
        
class InvalidSearchTermError(Exception):
    """SearchTerm is invalid."""
    def __init__(self):
        super().__init__("SearchTerm is invalid")
        
class LanguagePreferenceInvalidError(Exception):
    """LanguagePreference is invalid."""
    def __init__(self):
        super().__init__("LanguagePreference is invalid")
        
class NoResponseError(Exception):
    """No response from the server."""
    def __init__(self):
        super().__init__("No response from the server")

class IDInvalidError(Exception):
    def __init__(self):
        super().__init__("ID is invalid")


class NotAvailableError(Exception):
    """Exception raised when the data requested is not available for
    your account."""
    def __init__(self):
        super().__init__("The requested record contains data that is not "
                         "available on your account.")

# API Errors

class APIError(Exception):
    """Base exception for API errors returned by the web service."""
    pass


class UnknownError(APIError):
    """Unknown error."""
    def __init__(self):
        super().__init__("Unknown error")


class UnknownKeyError(APIError):
    """Unknown key."""
    def __init__(self):
        super().__init__("Unknown key")


class AccountOutOfCreditError(APIError):
    """Account out of credit."""
    def __init__(self):
        super().__init__("Account out of credit")


class IPNotAllowedError(APIError):
    """Request not allowed from this IP."""
    def __init__(self):
        super().__init__("Request not allowed from this IP")


class URLNotAllowedError(APIError):
    """Request not allowed from this URL."""
    def __init__(self):
        super().__init__("Request not allowed from this URL")


class ServiceNotAvailableOnKeyError(APIError):
    """Web service not available on this key."""
    def __init__(self):
        super().__init__("Web service not available on this key")


class ServiceNotAvailableOnPlanError(APIError):
    """Web service not available on your plan."""
    def __init__(self):
        super().__init__("Web service not available on your plan")


class KeyDailyLimitExceededError(APIError):
    """Key daily limit exceeded."""
    def __init__(self):
        super().__init__("Key daily limit exceeded")


class AccountSuspendedError(APIError):
    """Account has been suspended."""
    def __init__(self):
        super().__init__("Your account has been suspended")


class SurgeProtectorTriggeredError(APIError):
    """Surge protector triggered."""
    def __init__(self):
        super().__init__("Surge protector triggered")


class NoValidLicenseError(APIError):
    """No valid license available."""
    def __init__(self):
        super().__init__("No valid license available")


class ManagementKeyRequiredError(APIError):
    """Management key required."""
    def __init__(self):
        super().__init__("Management key required")


class DemoLimitExceededError(APIError):
    """Demo limit exceeded."""
    def __init__(self):
        super().__init__("Demo limit exceeded")


class FreeServiceLimitExceededError(APIError):
    """Free service limit exceeded."""
    def __init__(self):
        super().__init__("Free service limit exceeded")


class WrongKeyTypeError(APIError):
    """Wrong type of key."""
    def __init__(self):
        super().__init__("Wrong type of key")


class KeyExpiredError(APIError):
    """Key expired."""
    def __init__(self):
        super().__init__("Key expired")


class UserLookupLimitExceededError(APIError):
    """Individual User exceeded Lookup Limit."""
    def __init__(self):
        super().__init__("Individual User exceeded Lookup Limit")


class InvalidParametersError(APIError):
    """Missing or invalid parameters."""
    def __init__(self):
        super().__init__("Missing or invalid parameters")


class InvalidJSONError(APIError):
    """Invalid JSON object."""
    def __init__(self):
        super().__init__("Invalid JSON object")


class EndpointNotAvailableError(APIError):
    """Endpoint not available."""
    def __init__(self):
        super().__init__("Endpoint not available")


class SandboxNotAvailableError(APIError):
    """Sandbox Mode is not available on this endpoint."""
    def __init__(self):
        super().__init__("Sandbox Mode is not available on this endpoint")


class HTTPSRequiredError(APIError):
    """HTTPS requests only."""
    def __init__(self):
        super().__init__("HTTPS requests only")


class AgreementNotSignedError(APIError):
    """Agreement Not Signed."""
    def __init__(self):
        super().__init__("Agreement Not Signed")

FIND_ERROR_CODE_MAP = {
    1001: InvalidSearchTermError,
    1002: InvalidSearchTermError,
    1003: CountryInvalidError,
    1004: LanguagePreferenceInvalidError,
    1005: NoResponseError,
}

RETRIEVE_ERROR_CODE_MAP = {
    1001: IDInvalidError,
    1002: NotAvailableError,
}

GENERAL_ERROR_CODE_MAP = {
    -1: UnknownError,
    2: UnknownKeyError,
    3: AccountOutOfCreditError,
    4: IPNotAllowedError,
    5: URLNotAllowedError,
    6: ServiceNotAvailableOnKeyError,
    7: ServiceNotAvailableOnPlanError,
    8: KeyDailyLimitExceededError,
    9: AccountSuspendedError,
    10: SurgeProtectorTriggeredError,
    11: NoValidLicenseError,
    12: ManagementKeyRequiredError,
    13: DemoLimitExceededError,
    14: FreeServiceLimitExceededError,
    15: WrongKeyTypeError,
    16: KeyExpiredError,
    17: UserLookupLimitExceededError,
    18: InvalidParametersError,
    19: InvalidJSONError,
    20: EndpointNotAvailableError,
    21: SandboxNotAvailableError,
    22: HTTPSRequiredError,
    23: AgreementNotSignedError,
}


def raise_error(error_code, context=None):
    """Raise the appropriate error based on the error code and context.
    
    Args:
        error_code: The error code to raise.
        context: Optional context string. If "find", uses FindError logic.
                 If "retrieve", uses RetrieveError logic. Defaults to "find".
    """
    if context == "retrieve":
        RetrieveError(error_code)
    else:
        # Default to FindError behavior (also when context="find" or None)
        FindError(error_code)
