"""Tests for error handling and error code mapping."""

import unittest
import sys
import os

# Add parent directory to path to import addresscomplete module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from addresscomplete.ErrorHandling import (
    FindError,
    RetrieveError,
    FIND_ERROR_CODE_MAP,
    RETRIEVE_ERROR_CODE_MAP,
    GENERAL_ERROR_CODE_MAP,
    # Response Errors
    ResponseError,
    CountryInvalidError,
    InvalidSearchTermError,
    LanguagePreferenceInvalidError,
    NoResponseError,
    IDInvalidError,
    NotAvailableError,
    # API Errors
    APIError,
    UnknownError,
    UnknownKeyError,
    AccountOutOfCreditError,
    IPNotAllowedError,
    URLNotAllowedError,
    ServiceNotAvailableOnKeyError,
    ServiceNotAvailableOnPlanError,
    KeyDailyLimitExceededError,
    AccountSuspendedError,
    SurgeProtectorTriggeredError,
    NoValidLicenseError,
    ManagementKeyRequiredError,
    DemoLimitExceededError,
    FreeServiceLimitExceededError,
    WrongKeyTypeError,
    KeyExpiredError,
    UserLookupLimitExceededError,
    InvalidParametersError,
    InvalidJSONError,
    EndpointNotAvailableError,
    SandboxNotAvailableError,
    HTTPSRequiredError,
    AgreementNotSignedError,
    # Additional imports for new error codes
)


class TestRaiseErrorFunction(unittest.TestCase):
    """Test FindError and RetrieveError with all error codes."""

    def test_raise_error_with_find_error_code_1001(self):
        """Test that error code 1001 raises InvalidSearchTermError."""
        with self.assertRaises(InvalidSearchTermError):
            FindError(1001)

    def test_raise_error_with_find_error_code_1002(self):
        """Test that error code 1002 raises InvalidSearchTermError."""
        with self.assertRaises(InvalidSearchTermError):
            FindError(1002)

    def test_raise_error_with_find_error_code_1003(self):
        """Test that error code 1003 raises CountryInvalidError."""
        with self.assertRaises(CountryInvalidError):
            FindError(1003)

    def test_raise_error_with_find_error_code_1004(self):
        """Test that error code 1004 raises LanguagePreferenceInvalidError."""
        with self.assertRaises(LanguagePreferenceInvalidError):
            FindError(1004)

    def test_raise_error_with_find_error_code_1005(self):
        """Test that error code 1005 raises NoResponseError."""
        with self.assertRaises(NoResponseError):
            FindError(1005)

    def test_raise_error_with_retrieve_error_code_1001(self):
        """Test that error code 1001 raises IDInvalidError for retrieve."""
        with self.assertRaises(IDInvalidError):
            RetrieveError(1001)

    def test_raise_error_with_retrieve_error_code_1002(self):
        """Test that error code 1002 raises NotAvailableError for retrieve."""
        with self.assertRaises(NotAvailableError):
            RetrieveError(1002)

    def test_raise_error_with_general_error_code_negative_one(self):
        """Test that error code -1 raises UnknownError."""
        with self.assertRaises(UnknownError):
            FindError(-1)

    def test_raise_error_with_general_error_code_2(self):
        """Test that error code 2 raises UnknownKeyError."""
        with self.assertRaises(UnknownKeyError):
            FindError(2)

    def test_raise_error_with_general_error_code_3(self):
        """Test that error code 3 raises AccountOutOfCreditError."""
        with self.assertRaises(AccountOutOfCreditError):
            FindError(3)

    def test_raise_error_with_general_error_code_4(self):
        """Test that error code 4 raises IPNotAllowedError."""
        with self.assertRaises(IPNotAllowedError):
            FindError(4)

    def test_raise_error_with_general_error_code_5(self):
        """Test that error code 5 raises URLNotAllowedError."""
        with self.assertRaises(URLNotAllowedError):
            FindError(5)

    def test_raise_error_with_general_error_code_6(self):
        """Test that error code 6 raises ServiceNotAvailableOnKeyError."""
        with self.assertRaises(ServiceNotAvailableOnKeyError):
            FindError(6)

    def test_raise_error_with_general_error_code_7(self):
        """Test that error code 7 raises ServiceNotAvailableOnPlanError."""
        with self.assertRaises(ServiceNotAvailableOnPlanError):
            FindError(7)

    def test_raise_error_with_general_error_code_8(self):
        """Test that error code 8 raises KeyDailyLimitExceededError."""
        with self.assertRaises(KeyDailyLimitExceededError):
            FindError(8)

    def test_raise_error_with_general_error_code_9(self):
        """Test that error code 9 raises AccountSuspendedError."""
        with self.assertRaises(AccountSuspendedError):
            FindError(9)

    def test_raise_error_with_general_error_code_10(self):
        """Test that error code 10 raises SurgeProtectorTriggeredError."""
        with self.assertRaises(SurgeProtectorTriggeredError):
            FindError(10)

    def test_raise_error_with_general_error_code_11(self):
        """Test that error code 11 raises NoValidLicenseError."""
        with self.assertRaises(NoValidLicenseError):
            FindError(11)

    def test_raise_error_with_general_error_code_12(self):
        """Test that error code 12 raises ManagementKeyRequiredError."""
        with self.assertRaises(ManagementKeyRequiredError):
            FindError(12)

    def test_raise_error_with_general_error_code_13(self):
        """Test that error code 13 raises DemoLimitExceededError."""
        with self.assertRaises(DemoLimitExceededError):
            FindError(13)

    def test_raise_error_with_general_error_code_14(self):
        """Test that error code 14 raises FreeServiceLimitExceededError."""
        with self.assertRaises(FreeServiceLimitExceededError):
            FindError(14)

    def test_raise_error_with_general_error_code_15(self):
        """Test that error code 15 raises WrongKeyTypeError."""
        with self.assertRaises(WrongKeyTypeError):
            FindError(15)

    def test_raise_error_with_general_error_code_16(self):
        """Test that error code 16 raises KeyExpiredError."""
        with self.assertRaises(KeyExpiredError):
            FindError(16)

    def test_raise_error_with_general_error_code_17(self):
        """Test that error code 17 raises UserLookupLimitExceededError."""
        with self.assertRaises(UserLookupLimitExceededError):
            FindError(17)

    def test_raise_error_with_general_error_code_18(self):
        """Test that error code 18 raises InvalidParametersError."""
        with self.assertRaises(InvalidParametersError):
            FindError(18)

    def test_raise_error_with_general_error_code_19(self):
        """Test that error code 19 raises InvalidJSONError."""
        with self.assertRaises(InvalidJSONError):
            FindError(19)

    def test_raise_error_with_general_error_code_20(self):
        """Test that error code 20 raises EndpointNotAvailableError."""
        with self.assertRaises(EndpointNotAvailableError):
            FindError(20)

    def test_raise_error_with_general_error_code_21(self):
        """Test that error code 21 raises SandboxNotAvailableError."""
        with self.assertRaises(SandboxNotAvailableError):
            FindError(21)

    def test_raise_error_with_general_error_code_22(self):
        """Test that error code 22 raises HTTPSRequiredError."""
        with self.assertRaises(HTTPSRequiredError):
            FindError(22)

    def test_raise_error_with_general_error_code_23(self):
        """Test that error code 23 raises AgreementNotSignedError."""
        with self.assertRaises(AgreementNotSignedError):
            FindError(23)

    def test_raise_error_with_unknown_error_code(self):
        """Test that unknown error codes raise UnknownError."""
        with self.assertRaises(UnknownError):
            FindError(9999)

    def test_raise_error_with_unknown_error_code_zero(self):
        """Test that error code 0 raises UnknownError."""
        with self.assertRaises(UnknownError):
            FindError(0)

    def test_raise_error_with_unknown_error_code_one(self):
        """Test that error code 1 raises UnknownError."""
        with self.assertRaises(UnknownError):
            FindError(1)


class TestExceptionClasses(unittest.TestCase):
    """Test exception class inheritance and messages."""

    def test_api_error_inheritance(self):
        """Test that APIError subclasses inherit from APIError."""
        self.assertTrue(issubclass(UnknownError, APIError))
        self.assertTrue(issubclass(UnknownKeyError, APIError))
        self.assertTrue(issubclass(AccountOutOfCreditError, APIError))
        self.assertTrue(issubclass(IPNotAllowedError, APIError))
        self.assertTrue(issubclass(URLNotAllowedError, APIError))
        self.assertTrue(issubclass(ServiceNotAvailableOnKeyError, APIError))
        self.assertTrue(issubclass(ServiceNotAvailableOnPlanError, APIError))
        self.assertTrue(issubclass(KeyDailyLimitExceededError, APIError))
        self.assertTrue(issubclass(AccountSuspendedError, APIError))
        self.assertTrue(issubclass(SurgeProtectorTriggeredError, APIError))
        self.assertTrue(issubclass(NoValidLicenseError, APIError))
        self.assertTrue(issubclass(ManagementKeyRequiredError, APIError))
        self.assertTrue(issubclass(DemoLimitExceededError, APIError))
        self.assertTrue(issubclass(FreeServiceLimitExceededError, APIError))
        self.assertTrue(issubclass(WrongKeyTypeError, APIError))
        self.assertTrue(issubclass(KeyExpiredError, APIError))
        self.assertTrue(issubclass(UserLookupLimitExceededError, APIError))
        self.assertTrue(issubclass(InvalidParametersError, APIError))
        self.assertTrue(issubclass(InvalidJSONError, APIError))
        self.assertTrue(issubclass(EndpointNotAvailableError, APIError))
        self.assertTrue(issubclass(SandboxNotAvailableError, APIError))
        self.assertTrue(issubclass(HTTPSRequiredError, APIError))
        self.assertTrue(issubclass(AgreementNotSignedError, APIError))

    def test_response_error_not_api_error(self):
        """Test that ResponseError subclasses do not inherit from APIError."""
        self.assertFalse(issubclass(CountryInvalidError, APIError))
        self.assertFalse(issubclass(InvalidSearchTermError, APIError))
        self.assertFalse(issubclass(LanguagePreferenceInvalidError, APIError))
        self.assertFalse(issubclass(NoResponseError, APIError))
        self.assertFalse(issubclass(IDInvalidError, APIError))
        self.assertFalse(issubclass(NotAvailableError, APIError))

    def test_api_error_not_response_error(self):
        """Test that APIError subclasses do not inherit from ResponseError."""
        self.assertFalse(issubclass(UnknownError, ResponseError))
        self.assertFalse(issubclass(UnknownKeyError, ResponseError))
        self.assertFalse(issubclass(AccountOutOfCreditError, ResponseError))

    def test_country_invalid_error_message(self):
        """Test CountryInvalidError message."""
        error = CountryInvalidError()
        self.assertEqual(str(error), "Country code is invalid")

    def test_invalid_search_term_error_message(self):
        """Test InvalidSearchTermError message."""
        error = InvalidSearchTermError()
        self.assertEqual(str(error), "SearchTerm is invalid")

    def test_language_preference_invalid_error_message(self):
        """Test LanguagePreferenceInvalidError message."""
        error = LanguagePreferenceInvalidError()
        self.assertEqual(str(error), "LanguagePreference is invalid")

    def test_no_response_error_message(self):
        """Test NoResponseError message."""
        error = NoResponseError()
        self.assertEqual(str(error), "No response from the server")

    def test_id_invalid_error_message(self):
        """Test IDInvalidError message."""
        error = IDInvalidError()
        self.assertEqual(str(error), "ID is invalid")

    def test_not_available_error_message(self):
        """Test NotAvailableError message with custom message."""
        error = NotAvailableError()
        self.assertEqual(str(error), "The requested record contains data that is not available on your account.")

    def test_unknown_error_message(self):
        """Test UnknownError message."""
        error = UnknownError()
        self.assertEqual(str(error), "Unknown error")

    def test_unknown_key_error_message(self):
        """Test UnknownKeyError message."""
        error = UnknownKeyError()
        self.assertEqual(str(error), "Unknown key")

    def test_account_out_of_credit_error_message(self):
        """Test AccountOutOfCreditError message."""
        error = AccountOutOfCreditError()
        self.assertEqual(str(error), "Account out of credit")

    def test_ip_not_allowed_error_message(self):
        """Test IPNotAllowedError message."""
        error = IPNotAllowedError()
        self.assertEqual(str(error), "Request not allowed from this IP")

    def test_url_not_allowed_error_message(self):
        """Test URLNotAllowedError message."""
        error = URLNotAllowedError()
        self.assertEqual(str(error), "Request not allowed from this URL")

    def test_service_not_available_on_key_error_message(self):
        """Test ServiceNotAvailableOnKeyError message."""
        error = ServiceNotAvailableOnKeyError()
        self.assertEqual(str(error), "Web service not available on this key")

    def test_service_not_available_on_plan_error_message(self):
        """Test ServiceNotAvailableOnPlanError message."""
        error = ServiceNotAvailableOnPlanError()
        self.assertEqual(str(error), "Web service not available on your plan")

    def test_key_daily_limit_exceeded_error_message(self):
        """Test KeyDailyLimitExceededError message."""
        error = KeyDailyLimitExceededError()
        self.assertEqual(str(error), "Key daily limit exceeded")

    def test_account_suspended_error_message(self):
        """Test AccountSuspendedError message."""
        error = AccountSuspendedError()
        self.assertEqual(str(error), "Your account has been suspended")

    def test_surge_protector_triggered_error_message(self):
        """Test SurgeProtectorTriggeredError message."""
        error = SurgeProtectorTriggeredError()
        self.assertEqual(str(error), "Surge protector triggered")

    def test_no_valid_license_error_message(self):
        """Test NoValidLicenseError message."""
        error = NoValidLicenseError()
        self.assertEqual(str(error), "No valid license available")

    def test_management_key_required_error_message(self):
        """Test ManagementKeyRequiredError message."""
        error = ManagementKeyRequiredError()
        self.assertEqual(str(error), "Management key required")

    def test_demo_limit_exceeded_error_message(self):
        """Test DemoLimitExceededError message."""
        error = DemoLimitExceededError()
        self.assertEqual(str(error), "Demo limit exceeded")

    def test_free_service_limit_exceeded_error_message(self):
        """Test FreeServiceLimitExceededError message."""
        error = FreeServiceLimitExceededError()
        self.assertEqual(str(error), "Free service limit exceeded")

    def test_wrong_key_type_error_message(self):
        """Test WrongKeyTypeError message."""
        error = WrongKeyTypeError()
        self.assertEqual(str(error), "Wrong type of key")

    def test_key_expired_error_message(self):
        """Test KeyExpiredError message."""
        error = KeyExpiredError()
        self.assertEqual(str(error), "Key expired")

    def test_user_lookup_limit_exceeded_error_message(self):
        """Test UserLookupLimitExceededError message."""
        error = UserLookupLimitExceededError()
        self.assertEqual(str(error), "Individual User exceeded Lookup Limit")

    def test_invalid_parameters_error_message(self):
        """Test InvalidParametersError message."""
        error = InvalidParametersError()
        self.assertEqual(str(error), "Missing or invalid parameters")

    def test_invalid_json_error_message(self):
        """Test InvalidJSONError message."""
        error = InvalidJSONError()
        self.assertEqual(str(error), "Invalid JSON object")

    def test_endpoint_not_available_error_message(self):
        """Test EndpointNotAvailableError message."""
        error = EndpointNotAvailableError()
        self.assertEqual(str(error), "Endpoint not available")

    def test_sandbox_not_available_error_message(self):
        """Test SandboxNotAvailableError message."""
        error = SandboxNotAvailableError()
        self.assertEqual(str(error), "Sandbox Mode is not available on this endpoint")

    def test_https_required_error_message(self):
        """Test HTTPSRequiredError message."""
        error = HTTPSRequiredError()
        self.assertEqual(str(error), "HTTPS requests only")

    def test_agreement_not_signed_error_message(self):
        """Test AgreementNotSignedError message."""
        error = AgreementNotSignedError()
        self.assertEqual(str(error), "Agreement Not Signed")

    def test_exception_instantiation(self):
        """Test that all exceptions can be instantiated."""
        exceptions = [
            CountryInvalidError,
            InvalidSearchTermError,
            LanguagePreferenceInvalidError,
            NoResponseError,
            IDInvalidError,
            NotAvailableError,
            UnknownError,
            UnknownKeyError,
            AccountOutOfCreditError,
            IPNotAllowedError,
            URLNotAllowedError,
            ServiceNotAvailableOnKeyError,
            ServiceNotAvailableOnPlanError,
            KeyDailyLimitExceededError,
            AccountSuspendedError,
            SurgeProtectorTriggeredError,
            NoValidLicenseError,
            ManagementKeyRequiredError,
            DemoLimitExceededError,
            FreeServiceLimitExceededError,
            WrongKeyTypeError,
            KeyExpiredError,
            UserLookupLimitExceededError,
            InvalidParametersError,
            InvalidJSONError,
            EndpointNotAvailableError,
            SandboxNotAvailableError,
            HTTPSRequiredError,
            AgreementNotSignedError,
        ]
        
        for exc_class in exceptions:
            self.assertIsInstance(exc_class(), Exception)


class TestErrorCodeMaps(unittest.TestCase):
    """Test error code map completeness."""

    def test_find_error_code_map_completeness(self):
        """Test that FIND_ERROR_CODE_MAP contains all expected codes."""
        expected_codes = [1001, 1002, 1003, 1004, 1005]
        for code in expected_codes:
            self.assertIn(code, FIND_ERROR_CODE_MAP)

    def test_retrieve_error_code_map_completeness(self):
        """Test that RETRIEVE_ERROR_CODE_MAP contains all expected codes."""
        expected_codes = [1001, 1002]
        for code in expected_codes:
            self.assertIn(code, RETRIEVE_ERROR_CODE_MAP)

    def test_general_error_code_map_contains_expected_codes(self):
        """Test that GENERAL_ERROR_CODE_MAP contains expected codes."""
        expected_codes = [-1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        for code in expected_codes:
            self.assertIn(code, GENERAL_ERROR_CODE_MAP)


if __name__ == '__main__':
    unittest.main()
