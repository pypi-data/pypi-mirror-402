"""Tests for Jira utility functions, specifically PAT authentication (C2-1259)."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from jira import JIRA, JIRAError

from coauthor.utils.jira_utils import get_jira_connection


class TestGetJiraConnection:
    """Test suite for get_jira_connection function with PAT authentication support."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = Mock()
        return logger

    @pytest.fixture
    def jira_url(self):
        """Test Jira URL."""
        return "https://test-jira.example.com"

    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        """Clear Jira-related environment variables before each test."""
        env_vars = ["COAUTHOR_JIRA_PAT", "COAUTHOR_JIRA_USERNAME", "COAUTHOR_JIRA_PASSWORD"]
        original_values = {}

        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        yield

        # Restore original values
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_pat_authentication_success(self, mock_jira_class, mock_logger, jira_url):
        """Test successful PAT authentication when COAUTHOR_JIRA_PAT is set."""
        # Arrange
        test_pat = "test_personal_access_token_12345"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url}, token_auth=test_pat)
        mock_logger.debug.assert_any_call("Using PAT authentication for JIRA")
        mock_logger.debug.assert_any_call(f"Connected to JIRA at {jira_url}")

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_basic_auth_fallback_success(self, mock_jira_class, mock_logger, jira_url):
        """Test successful fallback to basic authentication when PAT is not set."""
        # Arrange
        test_username = "test_user"
        test_password = "test_password"
        os.environ["COAUTHOR_JIRA_USERNAME"] = test_username
        os.environ["COAUTHOR_JIRA_PASSWORD"] = test_password
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url}, basic_auth=(test_username, test_password))
        mock_logger.debug.assert_any_call("Using basic authentication for JIRA")
        mock_logger.debug.assert_any_call(f"Connected to JIRA at {jira_url}")

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_pat_priority_over_basic_auth(self, mock_jira_class, mock_logger, jira_url):
        """Test that PAT authentication is prioritized when both PAT and basic auth are available."""
        # Arrange
        test_pat = "test_pat_token"
        test_username = "test_user"
        test_password = "test_password"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        os.environ["COAUTHOR_JIRA_USERNAME"] = test_username
        os.environ["COAUTHOR_JIRA_PASSWORD"] = test_password
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        # Verify PAT was used, not basic auth
        mock_jira_class.assert_called_once_with(options={"server": jira_url}, token_auth=test_pat)
        mock_logger.debug.assert_any_call("Using PAT authentication for JIRA")
        # Verify basic auth was NOT used
        call_args = mock_jira_class.call_args
        assert "basic_auth" not in call_args.kwargs

    def test_no_credentials_configured(self, mock_logger, jira_url):
        """Test error handling when no authentication credentials are configured."""
        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once_with(
            "No JIRA authentication credentials found. "
            "Set COAUTHOR_JIRA_PAT (recommended) or "
            "COAUTHOR_JIRA_USERNAME and COAUTHOR_JIRA_PASSWORD."
        )

    def test_only_username_no_password(self, mock_logger, jira_url):
        """Test error handling when only username is set without password."""
        # Arrange
        os.environ["COAUTHOR_JIRA_USERNAME"] = "test_user"

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()

    def test_only_password_no_username(self, mock_logger, jira_url):
        """Test error handling when only password is set without username."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "test_password"

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_invalid_pat_token(self, mock_jira_class, mock_logger, jira_url):
        """Test error handling when PAT token is invalid."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PAT"] = "invalid_token"
        mock_jira_class.side_effect = JIRAError("401 Unauthorized")

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
        assert "Failed to connect to JIRA" in mock_logger.error.call_args[0][0]

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_invalid_basic_auth_credentials(self, mock_jira_class, mock_logger, jira_url):
        """Test error handling when basic auth credentials are invalid."""
        # Arrange
        os.environ["COAUTHOR_JIRA_USERNAME"] = "invalid_user"
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "invalid_password"
        mock_jira_class.side_effect = JIRAError("401 Unauthorized")

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
        assert "Failed to connect to JIRA" in mock_logger.error.call_args[0][0]

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_ssl_verification_disabled_with_pat(self, mock_jira_class, mock_logger, jira_url):
        """Test SSL verification can be disabled with PAT authentication."""
        # Arrange
        test_pat = "test_pat_token"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger, disable_ssl_verification=True)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url, "verify": False}, token_auth=test_pat)
        mock_logger.warning.assert_called_once()
        assert "SSL verification is disabled" in mock_logger.warning.call_args[0][0]

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_ssl_verification_disabled_with_basic_auth(self, mock_jira_class, mock_logger, jira_url):
        """Test SSL verification can be disabled with basic authentication."""
        # Arrange
        test_username = "test_user"
        test_password = "test_password"
        os.environ["COAUTHOR_JIRA_USERNAME"] = test_username
        os.environ["COAUTHOR_JIRA_PASSWORD"] = test_password
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger, disable_ssl_verification=True)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(
            options={"server": jira_url, "verify": False}, basic_auth=(test_username, test_password)
        )
        mock_logger.warning.assert_called_once()
        assert "SSL verification is disabled" in mock_logger.warning.call_args[0][0]

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_empty_pat_string_falls_back_to_basic_auth(self, mock_jira_class, mock_logger, jira_url):
        """Test that empty PAT string falls back to basic authentication."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PAT"] = ""  # Empty string
        os.environ["COAUTHOR_JIRA_USERNAME"] = "test_user"
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "test_password"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        # Verify basic auth was used
        mock_jira_class.assert_called_once_with(options={"server": jira_url}, basic_auth=("test_user", "test_password"))
        mock_logger.debug.assert_any_call("Using basic authentication for JIRA")

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_connection_timeout_error(self, mock_jira_class, mock_logger, jira_url):
        """Test error handling when connection times out."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_class.side_effect = JIRAError("Connection timeout")

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()
        assert "Failed to connect to JIRA" in mock_logger.error.call_args[0][0]
        assert "Connection timeout" in str(mock_logger.error.call_args[0][0])

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_network_error(self, mock_jira_class, mock_logger, jira_url):
        """Test error handling for network errors."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_class.side_effect = JIRAError("Name or service not known")

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        mock_logger.error.assert_called_once()

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_phx_jira_scenario(self, mock_jira_class, mock_logger):
        """Test PHX domain Jira scenario with PAT authentication."""
        # Arrange
        phx_jira_url = "https://phx-jira.example.com"
        test_pat = "phx_pat_token_12345"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(phx_jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": phx_jira_url}, token_auth=test_pat)
        mock_logger.debug.assert_any_call("Using PAT authentication for JIRA")

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_bearer_token_format_implicit(self, mock_jira_class, mock_logger, jira_url):
        """Test that Bearer token format is handled implicitly by JIRA library."""
        # Arrange
        test_pat = "test_bearer_token"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        # Verify token_auth parameter is used (JIRA library handles Bearer header internally)
        call_kwargs = mock_jira_class.call_args.kwargs
        assert call_kwargs.get("token_auth") == test_pat
        assert "basic_auth" not in call_kwargs

    def test_backward_compatibility_no_pat_env_var(self, mock_logger, jira_url):
        """Test backward compatibility when COAUTHOR_JIRA_PAT doesn't exist."""
        # Arrange
        os.environ["COAUTHOR_JIRA_USERNAME"] = "legacy_user"
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "legacy_password"

        with patch("coauthor.utils.jira_utils.JIRA") as mock_jira_class:
            mock_jira_instance = Mock(spec=JIRA)
            mock_jira_class.return_value = mock_jira_instance

            # Act
            result = get_jira_connection(jira_url, mock_logger)

            # Assert
            assert result == mock_jira_instance
            mock_jira_class.assert_called_once_with(
                options={"server": jira_url}, basic_auth=("legacy_user", "legacy_password")
            )
            mock_logger.debug.assert_any_call("Using basic authentication for JIRA")


class TestJiraConnectionIntegration:
    """Integration tests for Jira connection functionality."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = Mock()
        return logger

    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        """Clear Jira-related environment variables before each test."""
        env_vars = ["COAUTHOR_JIRA_PAT", "COAUTHOR_JIRA_USERNAME", "COAUTHOR_JIRA_PASSWORD"]
        original_values = {}

        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        yield

        # Restore original values
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_multiple_connection_attempts(self, mock_jira_class, mock_logger):
        """Test multiple connection attempts with different credentials."""
        jira_url = "https://test.example.com"

        # First attempt with PAT
        os.environ["COAUTHOR_JIRA_PAT"] = "pat_token_1"
        mock_jira_instance_1 = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance_1

        result1 = get_jira_connection(jira_url, mock_logger)
        assert result1 == mock_jira_instance_1

        # Second attempt with basic auth (PAT removed)
        del os.environ["COAUTHOR_JIRA_PAT"]
        os.environ["COAUTHOR_JIRA_USERNAME"] = "user1"
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "pass1"
        mock_jira_instance_2 = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance_2

        result2 = get_jira_connection(jira_url, mock_logger)
        assert result2 == mock_jira_instance_2

        # Verify both methods were called
        assert mock_jira_class.call_count == 2

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_connection_error_recovery(self, mock_jira_class, mock_logger):
        """Test that connection can recover after an error."""
        jira_url = "https://test.example.com"
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"

        # First attempt fails
        mock_jira_class.side_effect = JIRAError("Temporary error")
        result1 = get_jira_connection(jira_url, mock_logger)
        assert result1 is None

        # Second attempt succeeds
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.side_effect = None
        mock_jira_class.return_value = mock_jira_instance
        result2 = get_jira_connection(jira_url, mock_logger)
        assert result2 == mock_jira_instance
