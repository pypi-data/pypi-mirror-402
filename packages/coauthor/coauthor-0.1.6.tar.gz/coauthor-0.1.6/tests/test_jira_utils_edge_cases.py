"""Additional edge case tests for Jira PAT authentication (C2-1259)."""

import os
import pytest
from unittest.mock import Mock, patch
from jira import JIRA, JIRAError

from coauthor.utils.jira_utils import get_jira_connection


class TestJiraAuthenticationEdgeCases:
    """Test edge cases and security considerations for Jira authentication."""

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

    def test_pat_token_not_logged(self, mock_logger, jira_url):
        """Test that PAT token value is never logged in debug messages."""
        # Arrange
        test_pat = "super_secret_pat_token_12345"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat

        with patch("coauthor.utils.jira_utils.JIRA") as mock_jira_class:
            mock_jira_instance = Mock(spec=JIRA)
            mock_jira_class.return_value = mock_jira_instance

            # Act
            get_jira_connection(jira_url, mock_logger)

            # Assert - check all logger calls don't contain the token
            all_log_calls = (
                mock_logger.debug.call_args_list
                + mock_logger.info.call_args_list
                + mock_logger.warning.call_args_list
                + mock_logger.error.call_args_list
            )

            for call in all_log_calls:
                if call:
                    call_str = str(call)
                    assert test_pat not in call_str, "PAT token should never be logged"

    def test_password_not_logged(self, mock_logger, jira_url):
        """Test that password is never logged in debug messages."""
        # Arrange
        test_username = "test_user"
        test_password = "super_secret_password"
        os.environ["COAUTHOR_JIRA_USERNAME"] = test_username
        os.environ["COAUTHOR_JIRA_PASSWORD"] = test_password

        with patch("coauthor.utils.jira_utils.JIRA") as mock_jira_class:
            mock_jira_instance = Mock(spec=JIRA)
            mock_jira_class.return_value = mock_jira_instance

            # Act
            get_jira_connection(jira_url, mock_logger)

            # Assert - check all logger calls don't contain the password
            all_log_calls = (
                mock_logger.debug.call_args_list
                + mock_logger.info.call_args_list
                + mock_logger.warning.call_args_list
                + mock_logger.error.call_args_list
            )

            for call in all_log_calls:
                if call:
                    call_str = str(call)
                    assert test_password not in call_str, "Password should never be logged"

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_whitespace_in_pat_token(self, mock_jira_class, mock_logger, jira_url):
        """Test PAT token with whitespace is handled correctly."""
        # Arrange
        test_pat_with_whitespace = "  token_with_spaces  "
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat_with_whitespace
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        # Verify the token was passed as-is (not stripped)
        call_kwargs = mock_jira_class.call_args.kwargs
        assert call_kwargs.get("token_auth") == test_pat_with_whitespace

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_special_characters_in_credentials(self, mock_jira_class, mock_logger, jira_url):
        """Test credentials with special characters are handled correctly."""
        # Arrange
        test_username = "user@example.com"
        test_password = "p@ssw0rd!#$%"
        os.environ["COAUTHOR_JIRA_USERNAME"] = test_username
        os.environ["COAUTHOR_JIRA_PASSWORD"] = test_password
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url}, basic_auth=(test_username, test_password))

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_very_long_pat_token(self, mock_jira_class, mock_logger, jira_url):
        """Test handling of very long PAT tokens."""
        # Arrange
        test_pat = "a" * 1000  # Very long token
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        call_kwargs = mock_jira_class.call_args.kwargs
        assert call_kwargs.get("token_auth") == test_pat

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_unicode_in_credentials(self, mock_jira_class, mock_logger, jira_url):
        """Test credentials with unicode characters."""
        # Arrange
        test_username = "用户名"
        test_password = "密码"
        os.environ["COAUTHOR_JIRA_USERNAME"] = test_username
        os.environ["COAUTHOR_JIRA_PASSWORD"] = test_password
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url}, basic_auth=(test_username, test_password))

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_error_message_does_not_expose_credentials(self, mock_jira_class, mock_logger, jira_url):
        """Test that error messages don't expose credentials."""
        # Arrange
        test_pat = "secret_token"
        os.environ["COAUTHOR_JIRA_PAT"] = test_pat
        mock_jira_class.side_effect = JIRAError("401 Unauthorized")

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        error_call = mock_logger.error.call_args[0][0]
        assert test_pat not in error_call, "Error message should not contain PAT token"

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_connection_with_custom_port(self, mock_jira_class, mock_logger):
        """Test connection to Jira with custom port."""
        # Arrange
        jira_url_with_port = "https://jira.example.com:8443"
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url_with_port, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url_with_port}, token_auth="test_token")

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_connection_with_path_in_url(self, mock_jira_class, mock_logger):
        """Test connection to Jira with path in URL."""
        # Arrange
        jira_url_with_path = "https://example.com/jira"
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url_with_path, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": jira_url_with_path}, token_auth="test_token")

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_http_url_instead_of_https(self, mock_jira_class, mock_logger):
        """Test connection with HTTP URL (not recommended but should work)."""
        # Arrange
        http_jira_url = "http://jira.example.com"
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(http_jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(options={"server": http_jira_url}, token_auth="test_token")

    def test_mixed_empty_credentials(self, mock_logger, jira_url):
        """Test various combinations of empty credential values."""
        test_cases = [
            {"COAUTHOR_JIRA_PAT": "", "COAUTHOR_JIRA_USERNAME": "", "COAUTHOR_JIRA_PASSWORD": ""},
            {"COAUTHOR_JIRA_PAT": "", "COAUTHOR_JIRA_USERNAME": "user", "COAUTHOR_JIRA_PASSWORD": ""},
            {"COAUTHOR_JIRA_PAT": "", "COAUTHOR_JIRA_USERNAME": "", "COAUTHOR_JIRA_PASSWORD": "pass"},
        ]

        for env_vars in test_cases:
            # Clear previous env vars
            for key in ["COAUTHOR_JIRA_PAT", "COAUTHOR_JIRA_USERNAME", "COAUTHOR_JIRA_PASSWORD"]:
                if key in os.environ:
                    del os.environ[key]

            # Set test env vars
            for key, value in env_vars.items():
                os.environ[key] = value

            # Act
            result = get_jira_connection(jira_url, mock_logger)

            # Assert
            assert result is None, f"Should fail with env_vars: {env_vars}"
            mock_logger.error.assert_called()
            mock_logger.reset_mock()

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_jira_error_with_detailed_message(self, mock_jira_class, mock_logger, jira_url):
        """Test that detailed JIRA error messages are properly logged."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        detailed_error_msg = "401 Unauthorized: Invalid token - Token has expired"
        mock_jira_class.side_effect = JIRAError(detailed_error_msg)

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result is None
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to connect to JIRA" in error_call
        assert detailed_error_msg in str(error_call)

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_ssl_verification_default_is_enabled(self, mock_jira_class, mock_logger, jira_url):
        """Test that SSL verification is enabled by default."""
        # Arrange
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        call_kwargs = mock_jira_class.call_args.kwargs
        options = call_kwargs.get("options", {})
        # Verify that verify is not set to False (meaning SSL is enabled)
        assert options.get("verify", True) is not False
        # Verify no SSL warning was logged
        mock_logger.warning.assert_not_called()

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_authentication_method_logging_accuracy(self, mock_jira_class, mock_logger, jira_url):
        """Test that the correct authentication method is logged."""
        # Test PAT authentication logging
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        get_jira_connection(jira_url, mock_logger)

        # Verify PAT authentication was logged
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Using PAT authentication" in call for call in debug_calls)
        assert not any("Using basic authentication" in call for call in debug_calls)

        # Reset
        mock_logger.reset_mock()
        del os.environ["COAUTHOR_JIRA_PAT"]

        # Test basic authentication logging
        os.environ["COAUTHOR_JIRA_USERNAME"] = "user"
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "pass"

        get_jira_connection(jira_url, mock_logger)

        # Verify basic authentication was logged
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Using basic authentication" in call for call in debug_calls)
        assert not any("Using PAT authentication" in call for call in debug_calls)


class TestBackwardCompatibility:
    """Test backward compatibility scenarios."""

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
    def test_legacy_configuration_still_works(self, mock_jira_class, mock_logger):
        """Test that legacy username/password configuration works without changes."""
        # Arrange
        jira_url = "https://legacy-jira.example.com"
        os.environ["COAUTHOR_JIRA_USERNAME"] = "legacy_user"
        os.environ["COAUTHOR_JIRA_PASSWORD"] = "legacy_password"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act
        result = get_jira_connection(jira_url, mock_logger)

        # Assert
        assert result == mock_jira_instance
        mock_jira_class.assert_called_once_with(
            options={"server": jira_url}, basic_auth=("legacy_user", "legacy_password")
        )

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_function_signature_unchanged(self, mock_jira_class, mock_logger):
        """Test that function signature remains backward compatible."""
        # Arrange
        jira_url = "https://test.example.com"
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance

        # Act - call with positional and keyword arguments
        result1 = get_jira_connection(jira_url, mock_logger)
        result2 = get_jira_connection(jira_url, mock_logger, False)
        result3 = get_jira_connection(jira_url, mock_logger, disable_ssl_verification=True)

        # Assert
        assert result1 == mock_jira_instance
        assert result2 == mock_jira_instance
        assert result3 == mock_jira_instance
        assert mock_jira_class.call_count == 3

    @patch("coauthor.utils.jira_utils.JIRA")
    def test_return_value_type_unchanged(self, mock_jira_class, mock_logger):
        """Test that return value type remains consistent (JIRA instance or None)."""
        jira_url = "https://test.example.com"

        # Test success case
        os.environ["COAUTHOR_JIRA_PAT"] = "test_token"
        mock_jira_instance = Mock(spec=JIRA)
        mock_jira_class.return_value = mock_jira_instance
        result = get_jira_connection(jira_url, mock_logger)
        assert isinstance(result, Mock) and result == mock_jira_instance

        # Test failure case
        mock_jira_class.side_effect = JIRAError("Error")
        result = get_jira_connection(jira_url, mock_logger)
        assert result is None
