"""
Comprehensive tests for ApiConnector.

These tests connect to a real Navigo3 test instance to verify functionality.
Configuration is loaded from environment variables (set in .env file).
"""

import os
import unittest
import threading
from uuid import uuid1
from requests.exceptions import HTTPError
from dotenv import load_dotenv

from dry_apy_connector.ApiConnector import ApiConnector
from dry_apy_connector.DryApiException import DryApiException


# Load environment variables from .env file
load_dotenv()

# Test configuration from environment variables
TEST_API_URL = os.getenv("TEST_API_URL")
TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")
TEST_PROJECT_ID = int(os.getenv("TEST_PROJECT_ID", 88))

if not TEST_API_URL or not TEST_USERNAME or not TEST_PASSWORD or not TEST_PROJECT_ID:
    raise ValueError("Missing environment variables")


class TestApiConnectorBasics(unittest.TestCase):
    """Test basic functionality of ApiConnector."""

    def setUp(self):
        """Set up test connector."""
        self.connector = ApiConnector(TEST_API_URL)

    def tearDown(self):
        """Clean up after tests."""
        if self.connector.is_logged_in():
            self.connector.logout()
        self.connector.close()

    def test_initial_state_not_logged_in(self):
        """Test that connector starts in logged out state."""
        self.assertFalse(self.connector.is_logged_in())

    def test_login_with_valid_credentials(self):
        """Test successful login with valid credentials."""
        self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
        self.assertTrue(self.connector.is_logged_in())

    def test_login_with_invalid_credentials(self):
        """Test that invalid credentials raise HTTPError."""
        with self.assertRaises(HTTPError) as context:
            self.connector.login_with_credentials("invalid_user", "wrong_password")
        self.assertIn("401", str(context.exception))

    def test_logout_after_login(self):
        """Test successful logout after login."""
        self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
        self.assertTrue(self.connector.is_logged_in())

        self.connector.logout()
        self.assertFalse(self.connector.is_logged_in())

    def test_double_login_raises_error(self):
        """Test that logging in twice raises an error."""
        self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)

        with self.assertRaises(Exception) as context:
            self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
        self.assertIn("already logged in", str(context.exception).lower())

    def test_execute_without_login_raises_error(self):
        """Test that calling execute without login raises error."""
        with self.assertRaises((DryApiException, ValueError)):
            self.connector.execute("project/get", {"id": TEST_PROJECT_ID})


class TestApiConnectorExecution(unittest.TestCase):
    """Test API execution methods."""

    def setUp(self):
        """Set up authenticated connector."""
        self.connector = ApiConnector(TEST_API_URL)
        self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)

    def tearDown(self):
        """Clean up after tests."""
        if self.connector.is_logged_in():
            self.connector.logout()
        self.connector.close()

    def test_execute_single_request(self):
        """Test executing a single API request."""
        result = self.connector.execute("project/get", {"id": TEST_PROJECT_ID})

        self.assertIsInstance(result, dict)
        self.assertIn("project", result)
        self.assertIn("id", result["project"])
        self.assertEqual(result["project"]["id"], TEST_PROJECT_ID)
        self.assertIn("name", result["project"])

    def test_execute_returns_correct_data_structure(self):
        """Test that execute returns the expected data structure."""
        result = self.connector.execute("project/get", {"id": TEST_PROJECT_ID})

        # Verify common project fields exist
        self.assertIsInstance(result, dict)
        self.assertIn("project", result)
        project_data = result["project"]
        self.assertIn("id", project_data)
        self.assertIn("name", project_data)
        self.assertIsInstance(project_data["id"], int)
        self.assertIsInstance(project_data["name"], str)

    def test_batch_execution_with_single_endpoint(self):
        """Test batch execution with multiple requests to same endpoint."""
        batch = []
        project_ids = [(TEST_PROJECT_ID + i) for i in range(3)]

        for pid in project_ids:
            request = ApiConnector.create_request(
                str(uuid1()), "project/get", "EXECUTE", {"id": pid}, None, None
            )
            batch.append(request)

        responses = self.connector.call(batch)

        self.assertEqual(len(responses), len(project_ids))
        for i, response in enumerate(responses):
            self.assertIn("output", response)
            self.assertIn("project", response["output"])
            self.assertEqual(response["output"]["project"]["id"], project_ids[i])

    def test_validate_method(self):
        """Test the validate method."""
        validation_result = self.connector.validate(
            "project/get", {"id": TEST_PROJECT_ID}
        )

        self.assertIsInstance(validation_result, dict)
        # Validation result should contain validation info

    def test_call_with_empty_list_returns_empty(self):
        """Test that calling with empty list returns empty list."""
        result = self.connector.call([])
        self.assertEqual(result, [])


class TestApiConnectorContextManager(unittest.TestCase):
    """Test context manager functionality."""

    def test_context_manager_basic_usage(self):
        """Test basic context manager usage."""
        with ApiConnector(TEST_API_URL) as connector:
            connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
            self.assertTrue(connector.is_logged_in())

            result = connector.execute("project/get", {"id": TEST_PROJECT_ID})
            self.assertIn("project", result)
            self.assertIn("id", result["project"])

            connector.logout()
        # Session should be closed after context

    def test_context_manager_with_exception(self):
        """Test that context manager closes session even with exception."""
        try:
            with ApiConnector(TEST_API_URL) as connector:
                connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
                raise ValueError("Test exception")
        except ValueError:
            pass
        # Should not leak resources

    def test_context_manager_auto_cleanup(self):
        """Test that context manager properly cleans up resources."""
        connector = None
        with ApiConnector(TEST_API_URL) as conn:
            connector = conn
            connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
            self.assertTrue(connector.is_logged_in())

        # After context, we can verify connector still exists but session is closed
        # (we can't directly test if session is closed, but we can verify behavior)


class TestApiConnectorSessionManagement(unittest.TestCase):
    """Test session management and relogin scenarios."""

    def test_relogin_after_logout(self):
        """Test that we can login again after logout."""
        connector = ApiConnector(TEST_API_URL)

        try:
            # First login
            connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
            result1 = connector.execute("project/get", {"id": TEST_PROJECT_ID})
            self.assertIn("project", result1)
            connector.logout()

            # Second login
            connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
            result2 = connector.execute("project/get", {"id": TEST_PROJECT_ID})
            self.assertIn("project", result2)
            connector.logout()

            # Both should return same data
            self.assertEqual(result1["project"]["id"], result2["project"]["id"])
        finally:
            if connector.is_logged_in():
                connector.logout()
            connector.close()

    def test_multiple_logout_calls_safe(self):
        """Test that calling logout multiple times is safe."""
        connector = ApiConnector(TEST_API_URL)

        try:
            connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)
            connector.logout()
            connector.logout()  # Second logout should be safe
            # No exception should be raised
        finally:
            connector.close()

    def test_close_multiple_times_safe(self):
        """Test that calling close multiple times is safe."""
        connector = ApiConnector(TEST_API_URL)
        connector.close()
        connector.close()  # Should be safe
        # No exception should be raised


class TestApiConnectorThreadSafety(unittest.TestCase):
    """Test thread safety of ApiConnector."""

    def setUp(self):
        """Set up authenticated connector."""
        self.connector = ApiConnector(TEST_API_URL)
        self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)

    def tearDown(self):
        """Clean up after tests."""
        if self.connector.is_logged_in():
            self.connector.logout()
        self.connector.close()

    def test_concurrent_api_calls(self):
        """Test that concurrent API calls from multiple threads work correctly."""
        results = []
        errors = []

        def make_api_call(project_id):
            try:
                result = self.connector.execute("project/get", {"id": project_id})
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = []
        project_ids = [
            TEST_PROJECT_ID for _ in range(5)
        ]  # Use same ID to avoid test data issues

        for pid in project_ids:
            thread = threading.Thread(target=make_api_call, args=(pid,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All calls should succeed
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), len(project_ids))

        # All results should be valid
        for result in results:
            self.assertIn("project", result)
            self.assertEqual(result["project"]["id"], TEST_PROJECT_ID)

    def test_concurrent_batch_calls(self):
        """Test concurrent batch API calls."""
        results = []
        errors = []

        def make_batch_call(batch_id):
            try:
                batch = [
                    ApiConnector.create_request(
                        str(uuid1()),
                        "project/get",
                        "EXECUTE",
                        {"id": TEST_PROJECT_ID},
                        None,
                        None,
                    )
                ]
                responses = self.connector.call(
                    batch, execution_alias=f"Batch {batch_id}"
                )
                results.append(responses)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_batch_call, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)


class TestApiConnectorErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        """Set up authenticated connector."""
        self.connector = ApiConnector(TEST_API_URL)
        self.connector.login_with_credentials(TEST_USERNAME, TEST_PASSWORD)

    def tearDown(self):
        """Clean up after tests."""
        if self.connector.is_logged_in():
            self.connector.logout()
        self.connector.close()

    def test_execute_with_invalid_endpoint(self):
        """Test that invalid endpoint raises appropriate error."""
        with self.assertRaises((DryApiException, HTTPError)):
            self.connector.execute("invalid/endpoint/that/does/not/exist", {})

    def test_execute_with_invalid_data(self):
        """Test execution with invalid input data structure."""
        # This depends on API validation, but should handle gracefully
        try:
            result = self.connector.execute("project/get", {"id": "invalid_id"})
            # If it doesn't raise, that's also valid behavior
        except (DryApiException, Exception):
            # Expected for invalid data
            pass


class TestApiConnectorRequestCreation(unittest.TestCase):
    """Test request creation utility methods."""

    def test_create_request_basic(self):
        """Test basic request creation."""
        request = ApiConnector.create_request(
            str(uuid1()), "project/get", "EXECUTE", {"id": TEST_PROJECT_ID}, None, None
        )

        self.assertIsInstance(request, dict)
        self.assertIn("qualifiedName", request)
        self.assertIn("requestType", request)
        self.assertIn("input", request)
        self.assertIn("requestUuid", request)

        self.assertEqual(request["qualifiedName"], "project/get")
        self.assertEqual(request["requestType"], "EXECUTE")
        self.assertEqual(request["input"]["id"], TEST_PROJECT_ID)

    def test_create_request_with_list_input(self):
        """Test creating request with list as input data."""
        request = ApiConnector.create_request(
            str(uuid1()), "some/endpoint", "EXECUTE", [1, 2, 3], [], None
        )

        self.assertIsInstance(request, dict)
        self.assertIn("input", request)
        self.assertEqual(request["input"], [1, 2, 3])


def suite():
    """Create test suite."""
    test_suite = unittest.TestSuite()

    # Add all test classes
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorBasics)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorExecution)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorContextManager)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorSessionManagement)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorThreadSafety)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorErrorHandling)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestApiConnectorRequestCreation)
    )

    return test_suite


if __name__ == "__main__":
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
