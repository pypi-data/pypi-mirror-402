import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import requests

from addresscomplete import AddressComplete
from addresscomplete.ErrorHandling import (
    AccountOutOfCreditError,
    AccountSuspendedError,
    AgreementNotSignedError,
    CountryInvalidError,
    DemoLimitExceededError,
    EndpointNotAvailableError,
    FreeServiceLimitExceededError,
    HTTPSRequiredError,
    IDInvalidError,
    InvalidJSONError,
    InvalidParametersError,
    InvalidSearchTermError,
    IPNotAllowedError,
    KeyDailyLimitExceededError,
    KeyExpiredError,
    LanguagePreferenceInvalidError,
    ManagementKeyRequiredError,
    NoResponseError,
    NoValidLicenseError,
    NotAvailableError,
    SandboxNotAvailableError,
    ServiceNotAvailableOnKeyError,
    ServiceNotAvailableOnPlanError,
    SurgeProtectorTriggeredError,
    UnknownError,
    UnknownKeyError,
    URLNotAllowedError,
    UserLookupLimitExceededError,
    WrongKeyTypeError,
)


def make_response(json_data, raise_exc=None):
    response = Mock()
    response.json.return_value = json_data
    if raise_exc is None:
        response.raise_for_status.return_value = None
    else:
        response.raise_for_status.side_effect = raise_exc
    return response


class TestAddressCompleteFind(unittest.TestCase):
    def setUp(self):
        self.client = AddressComplete("test-key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_happy_path_returns_json(self, mock_get):
        payload = {"Error": None, "Items": []}
        mock_get.return_value = make_response(payload)

        result = self.client.find(
            "123 Main St",
            country="CAN",
            max_suggestions=5,
            language_preference="en",
        )

        self.assertEqual(result, payload)
        called_url = mock_get.call_args[0][0]
        self.assertIn("SearchTerm=123+Main+St", called_url)

        query = parse_qs(urlparse(called_url).query)
        self.assertEqual(query["Key"][0], "test-key")
        self.assertEqual(query["SearchTerm"][0], "123 Main St")
        self.assertEqual(query["Country"][0], "CAN")
        self.assertEqual(query["MaxSuggestions"][0], "5")
        self.assertEqual(query["LanguagePreference"][0], "en")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_raises_for_status(self, mock_get):
        mock_get.return_value = make_response(
            {"Error": None},
            raise_exc=requests.HTTPError("boom"),
        )

        with self.assertRaises(requests.HTTPError):
            self.client.find("test")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_mapping_find(self, mock_get):
        mock_get.return_value = make_response({"Error": 1001})

        with self.assertRaises(InvalidSearchTermError):
            self.client.find("bad")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_mapping_general(self, mock_get):
        mock_get.return_value = make_response({"Error": 2})

        with self.assertRaises(UnknownKeyError):
            self.client.find("test")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_unknown_error_code(self, mock_get):
        mock_get.return_value = make_response({"Error": 9999})

        with self.assertRaises(UnknownError):
            self.client.find("test")


class TestAddressCompleteRetrieve(unittest.TestCase):
    def setUp(self):
        self.client = AddressComplete("test-key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_happy_path_returns_json(self, mock_get):
        payload = {"Error": None, "Address": {"Line1": "123 Main St"}}
        mock_get.return_value = make_response(payload)

        result = self.client.retrieve("ABC 123")

        self.assertEqual(result, payload)
        called_url = mock_get.call_args[0][0]
        self.assertIn("Id=ABC%20123", called_url)

        query = parse_qs(urlparse(called_url).query)
        self.assertEqual(query["Key"][0], "test-key")
        self.assertEqual(query["Id"][0], "ABC 123")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_raises_for_status(self, mock_get):
        mock_get.return_value = make_response(
            {"Error": None},
            raise_exc=requests.HTTPError("boom"),
        )

        with self.assertRaises(requests.HTTPError):
            self.client.retrieve("ABC")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_mapping_retrieve(self, mock_get):
        mock_get.return_value = make_response({"Error": 1001})

        with self.assertRaises(IDInvalidError):
            self.client.retrieve("bad-id")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_mapping_general(self, mock_get):
        mock_get.return_value = make_response({"Error": 2})

        with self.assertRaises(UnknownKeyError):
            self.client.retrieve("ABC")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_unknown_error_code(self, mock_get):
        mock_get.return_value = make_response({"Error": 9999})

        with self.assertRaises(UnknownError):
            self.client.retrieve("ABC")


class TestFindErrorMappings(unittest.TestCase):
    """Test all FindError specific error code mappings."""
    
    def setUp(self):
        self.client = AddressComplete("test-key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_1001_invalid_search_term(self, mock_get):
        """Test error code 1001 maps to InvalidSearchTermError."""
        mock_get.return_value = make_response({"Error": 1001})
        with self.assertRaises(InvalidSearchTermError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "SearchTerm is invalid")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_1002_invalid_search_term(self, mock_get):
        """Test error code 1002 maps to InvalidSearchTermError."""
        mock_get.return_value = make_response({"Error": 1002})
        with self.assertRaises(InvalidSearchTermError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "SearchTerm is invalid")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_1003_country_invalid(self, mock_get):
        """Test error code 1003 maps to CountryInvalidError."""
        mock_get.return_value = make_response({"Error": 1003})
        with self.assertRaises(CountryInvalidError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Country code is invalid")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_1004_language_preference_invalid(self, mock_get):
        """Test error code 1004 maps to LanguagePreferenceInvalidError."""
        mock_get.return_value = make_response({"Error": 1004})
        with self.assertRaises(LanguagePreferenceInvalidError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "LanguagePreference is invalid")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_1005_no_response(self, mock_get):
        """Test error code 1005 maps to NoResponseError."""
        mock_get.return_value = make_response({"Error": 1005})
        with self.assertRaises(NoResponseError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "No response from the server")


class TestRetrieveErrorMappings(unittest.TestCase):
    """Test all RetrieveError specific error code mappings."""
    
    def setUp(self):
        self.client = AddressComplete("test-key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_1001_id_invalid(self, mock_get):
        """Test error code 1001 maps to IDInvalidError."""
        mock_get.return_value = make_response({"Error": 1001})
        with self.assertRaises(IDInvalidError) as context:
            self.client.retrieve("bad-id")
        self.assertEqual(str(context.exception), "ID is invalid")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_1002_not_available(self, mock_get):
        """Test error code 1002 maps to NotAvailableError."""
        mock_get.return_value = make_response({"Error": 1002})
        with self.assertRaises(NotAvailableError) as context:
            self.client.retrieve("id")
        self.assertEqual(
            str(context.exception),
            "The requested record contains data that is not available on your account."
        )


class TestGeneralErrorMappingsFind(unittest.TestCase):
    """Test all general error code mappings for find operations."""
    
    def setUp(self):
        self.client = AddressComplete("test-key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_minus_1_unknown_error(self, mock_get):
        """Test error code -1 maps to UnknownError."""
        mock_get.return_value = make_response({"Error": -1})
        with self.assertRaises(UnknownError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Unknown error")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_2_unknown_key(self, mock_get):
        """Test error code 2 maps to UnknownKeyError."""
        mock_get.return_value = make_response({"Error": 2})
        with self.assertRaises(UnknownKeyError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Unknown key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_3_account_out_of_credit(self, mock_get):
        """Test error code 3 maps to AccountOutOfCreditError."""
        mock_get.return_value = make_response({"Error": 3})
        with self.assertRaises(AccountOutOfCreditError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Account out of credit")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_4_ip_not_allowed(self, mock_get):
        """Test error code 4 maps to IPNotAllowedError."""
        mock_get.return_value = make_response({"Error": 4})
        with self.assertRaises(IPNotAllowedError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Request not allowed from this IP")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_5_url_not_allowed(self, mock_get):
        """Test error code 5 maps to URLNotAllowedError."""
        mock_get.return_value = make_response({"Error": 5})
        with self.assertRaises(URLNotAllowedError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Request not allowed from this URL")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_6_service_not_available_on_key(self, mock_get):
        """Test error code 6 maps to ServiceNotAvailableOnKeyError."""
        mock_get.return_value = make_response({"Error": 6})
        with self.assertRaises(ServiceNotAvailableOnKeyError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Web service not available on this key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_7_service_not_available_on_plan(self, mock_get):
        """Test error code 7 maps to ServiceNotAvailableOnPlanError."""
        mock_get.return_value = make_response({"Error": 7})
        with self.assertRaises(ServiceNotAvailableOnPlanError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Web service not available on your plan")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_8_key_daily_limit_exceeded(self, mock_get):
        """Test error code 8 maps to KeyDailyLimitExceededError."""
        mock_get.return_value = make_response({"Error": 8})
        with self.assertRaises(KeyDailyLimitExceededError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Key daily limit exceeded")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_9_account_suspended(self, mock_get):
        """Test error code 9 maps to AccountSuspendedError."""
        mock_get.return_value = make_response({"Error": 9})
        with self.assertRaises(AccountSuspendedError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Your account has been suspended")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_10_surge_protector_triggered(self, mock_get):
        """Test error code 10 maps to SurgeProtectorTriggeredError."""
        mock_get.return_value = make_response({"Error": 10})
        with self.assertRaises(SurgeProtectorTriggeredError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Surge protector triggered")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_11_no_valid_license(self, mock_get):
        """Test error code 11 maps to NoValidLicenseError."""
        mock_get.return_value = make_response({"Error": 11})
        with self.assertRaises(NoValidLicenseError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "No valid license available")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_12_management_key_required(self, mock_get):
        """Test error code 12 maps to ManagementKeyRequiredError."""
        mock_get.return_value = make_response({"Error": 12})
        with self.assertRaises(ManagementKeyRequiredError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Management key required")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_13_demo_limit_exceeded(self, mock_get):
        """Test error code 13 maps to DemoLimitExceededError."""
        mock_get.return_value = make_response({"Error": 13})
        with self.assertRaises(DemoLimitExceededError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Demo limit exceeded")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_14_free_service_limit_exceeded(self, mock_get):
        """Test error code 14 maps to FreeServiceLimitExceededError."""
        mock_get.return_value = make_response({"Error": 14})
        with self.assertRaises(FreeServiceLimitExceededError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Free service limit exceeded")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_15_wrong_key_type(self, mock_get):
        """Test error code 15 maps to WrongKeyTypeError."""
        mock_get.return_value = make_response({"Error": 15})
        with self.assertRaises(WrongKeyTypeError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Wrong type of key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_16_key_expired(self, mock_get):
        """Test error code 16 maps to KeyExpiredError."""
        mock_get.return_value = make_response({"Error": 16})
        with self.assertRaises(KeyExpiredError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Key expired")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_17_user_lookup_limit_exceeded(self, mock_get):
        """Test error code 17 maps to UserLookupLimitExceededError."""
        mock_get.return_value = make_response({"Error": 17})
        with self.assertRaises(UserLookupLimitExceededError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Individual User exceeded Lookup Limit")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_18_invalid_parameters(self, mock_get):
        """Test error code 18 maps to InvalidParametersError."""
        mock_get.return_value = make_response({"Error": 18})
        with self.assertRaises(InvalidParametersError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Missing or invalid parameters")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_19_invalid_json(self, mock_get):
        """Test error code 19 maps to InvalidJSONError."""
        mock_get.return_value = make_response({"Error": 19})
        with self.assertRaises(InvalidJSONError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Invalid JSON object")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_20_endpoint_not_available(self, mock_get):
        """Test error code 20 maps to EndpointNotAvailableError."""
        mock_get.return_value = make_response({"Error": 20})
        with self.assertRaises(EndpointNotAvailableError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Endpoint not available")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_21_sandbox_not_available(self, mock_get):
        """Test error code 21 maps to SandboxNotAvailableError."""
        mock_get.return_value = make_response({"Error": 21})
        with self.assertRaises(SandboxNotAvailableError) as context:
            self.client.find("test")
        self.assertEqual(
            str(context.exception),
            "Sandbox Mode is not available on this endpoint"
        )

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_22_https_required(self, mock_get):
        """Test error code 22 maps to HTTPSRequiredError."""
        mock_get.return_value = make_response({"Error": 22})
        with self.assertRaises(HTTPSRequiredError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "HTTPS requests only")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_find_error_23_agreement_not_signed(self, mock_get):
        """Test error code 23 maps to AgreementNotSignedError."""
        mock_get.return_value = make_response({"Error": 23})
        with self.assertRaises(AgreementNotSignedError) as context:
            self.client.find("test")
        self.assertEqual(str(context.exception), "Agreement Not Signed")


class TestGeneralErrorMappingsRetrieve(unittest.TestCase):
    """Test all general error code mappings for retrieve operations."""
    
    def setUp(self):
        self.client = AddressComplete("test-key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_minus_1_unknown_error(self, mock_get):
        """Test error code -1 maps to UnknownError."""
        mock_get.return_value = make_response({"Error": -1})
        with self.assertRaises(UnknownError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Unknown error")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_2_unknown_key(self, mock_get):
        """Test error code 2 maps to UnknownKeyError."""
        mock_get.return_value = make_response({"Error": 2})
        with self.assertRaises(UnknownKeyError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Unknown key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_3_account_out_of_credit(self, mock_get):
        """Test error code 3 maps to AccountOutOfCreditError."""
        mock_get.return_value = make_response({"Error": 3})
        with self.assertRaises(AccountOutOfCreditError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Account out of credit")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_4_ip_not_allowed(self, mock_get):
        """Test error code 4 maps to IPNotAllowedError."""
        mock_get.return_value = make_response({"Error": 4})
        with self.assertRaises(IPNotAllowedError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Request not allowed from this IP")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_5_url_not_allowed(self, mock_get):
        """Test error code 5 maps to URLNotAllowedError."""
        mock_get.return_value = make_response({"Error": 5})
        with self.assertRaises(URLNotAllowedError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Request not allowed from this URL")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_6_service_not_available_on_key(self, mock_get):
        """Test error code 6 maps to ServiceNotAvailableOnKeyError."""
        mock_get.return_value = make_response({"Error": 6})
        with self.assertRaises(ServiceNotAvailableOnKeyError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Web service not available on this key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_7_service_not_available_on_plan(self, mock_get):
        """Test error code 7 maps to ServiceNotAvailableOnPlanError."""
        mock_get.return_value = make_response({"Error": 7})
        with self.assertRaises(ServiceNotAvailableOnPlanError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Web service not available on your plan")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_8_key_daily_limit_exceeded(self, mock_get):
        """Test error code 8 maps to KeyDailyLimitExceededError."""
        mock_get.return_value = make_response({"Error": 8})
        with self.assertRaises(KeyDailyLimitExceededError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Key daily limit exceeded")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_9_account_suspended(self, mock_get):
        """Test error code 9 maps to AccountSuspendedError."""
        mock_get.return_value = make_response({"Error": 9})
        with self.assertRaises(AccountSuspendedError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Your account has been suspended")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_10_surge_protector_triggered(self, mock_get):
        """Test error code 10 maps to SurgeProtectorTriggeredError."""
        mock_get.return_value = make_response({"Error": 10})
        with self.assertRaises(SurgeProtectorTriggeredError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Surge protector triggered")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_11_no_valid_license(self, mock_get):
        """Test error code 11 maps to NoValidLicenseError."""
        mock_get.return_value = make_response({"Error": 11})
        with self.assertRaises(NoValidLicenseError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "No valid license available")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_12_management_key_required(self, mock_get):
        """Test error code 12 maps to ManagementKeyRequiredError."""
        mock_get.return_value = make_response({"Error": 12})
        with self.assertRaises(ManagementKeyRequiredError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Management key required")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_13_demo_limit_exceeded(self, mock_get):
        """Test error code 13 maps to DemoLimitExceededError."""
        mock_get.return_value = make_response({"Error": 13})
        with self.assertRaises(DemoLimitExceededError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Demo limit exceeded")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_14_free_service_limit_exceeded(self, mock_get):
        """Test error code 14 maps to FreeServiceLimitExceededError."""
        mock_get.return_value = make_response({"Error": 14})
        with self.assertRaises(FreeServiceLimitExceededError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Free service limit exceeded")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_15_wrong_key_type(self, mock_get):
        """Test error code 15 maps to WrongKeyTypeError."""
        mock_get.return_value = make_response({"Error": 15})
        with self.assertRaises(WrongKeyTypeError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Wrong type of key")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_16_key_expired(self, mock_get):
        """Test error code 16 maps to KeyExpiredError."""
        mock_get.return_value = make_response({"Error": 16})
        with self.assertRaises(KeyExpiredError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Key expired")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_17_user_lookup_limit_exceeded(self, mock_get):
        """Test error code 17 maps to UserLookupLimitExceededError."""
        mock_get.return_value = make_response({"Error": 17})
        with self.assertRaises(UserLookupLimitExceededError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Individual User exceeded Lookup Limit")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_18_invalid_parameters(self, mock_get):
        """Test error code 18 maps to InvalidParametersError."""
        mock_get.return_value = make_response({"Error": 18})
        with self.assertRaises(InvalidParametersError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Missing or invalid parameters")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_19_invalid_json(self, mock_get):
        """Test error code 19 maps to InvalidJSONError."""
        mock_get.return_value = make_response({"Error": 19})
        with self.assertRaises(InvalidJSONError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Invalid JSON object")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_20_endpoint_not_available(self, mock_get):
        """Test error code 20 maps to EndpointNotAvailableError."""
        mock_get.return_value = make_response({"Error": 20})
        with self.assertRaises(EndpointNotAvailableError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Endpoint not available")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_21_sandbox_not_available(self, mock_get):
        """Test error code 21 maps to SandboxNotAvailableError."""
        mock_get.return_value = make_response({"Error": 21})
        with self.assertRaises(SandboxNotAvailableError) as context:
            self.client.retrieve("id")
        self.assertEqual(
            str(context.exception),
            "Sandbox Mode is not available on this endpoint"
        )

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_22_https_required(self, mock_get):
        """Test error code 22 maps to HTTPSRequiredError."""
        mock_get.return_value = make_response({"Error": 22})
        with self.assertRaises(HTTPSRequiredError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "HTTPS requests only")

    @patch("addresscomplete.AddressComplete.requests.get")
    def test_retrieve_error_23_agreement_not_signed(self, mock_get):
        """Test error code 23 maps to AgreementNotSignedError."""
        mock_get.return_value = make_response({"Error": 23})
        with self.assertRaises(AgreementNotSignedError) as context:
            self.client.retrieve("id")
        self.assertEqual(str(context.exception), "Agreement Not Signed")


class TestErrorInheritance(unittest.TestCase):
    """Test that errors inherit from correct base classes."""
    
    def test_api_error_inheritance(self):
        """Test that APIError exceptions inherit from Exception."""
        self.assertTrue(issubclass(UnknownError, Exception))
        self.assertTrue(issubclass(UnknownKeyError, Exception))
        self.assertTrue(issubclass(AccountOutOfCreditError, Exception))
        
    def test_response_error_inheritance(self):
        """Test that ResponseError exceptions inherit from Exception."""
        from addresscomplete.ErrorHandling import ResponseError
        self.assertTrue(issubclass(ResponseError, Exception))
        
    def test_error_message_content(self):
        """Test that error messages are correctly set."""
        # Test direct instantiation
        error = InvalidSearchTermError()
        self.assertEqual(str(error), "SearchTerm is invalid")
        
        error = CountryInvalidError()
        self.assertEqual(str(error), "Country code is invalid")
        
        error = LanguagePreferenceInvalidError()
        self.assertEqual(str(error), "LanguagePreference is invalid")
        
        error = NoResponseError()
        self.assertEqual(str(error), "No response from the server")
        
        error = IDInvalidError()
        self.assertEqual(str(error), "ID is invalid")
        
        error = UnknownError()
        self.assertEqual(str(error), "Unknown error")
        
        error = UnknownKeyError()
        self.assertEqual(str(error), "Unknown key")


if __name__ == "__main__":
    unittest.main()
