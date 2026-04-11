"""Tests for auth module.

Covers admin authentication, session management, and cookie handling.
"""

from unittest.mock import patch, MagicMock
import pytest

from fastapi import HTTPException, Response, Request
from app.core import auth


class TestResolveAdminPassword:
    """Test resolve_admin_password function."""

    def test_returns_env_password_when_no_ssm_parameter(self):
        """Should return ADMIN_PASSWORD when no SSM parameter configured."""
        with patch.object(auth, 'ADMIN_PASSWORD_PARAMETER_NAME', None):
            with patch.object(auth, 'ADMIN_PASSWORD', 'test_password'):
                result = auth.resolve_admin_password()
                assert result == 'test_password'

    def test_returns_ssm_password_when_configured(self):
        """Should return SSM password when parameter is configured."""
        with patch.object(auth, 'ADMIN_PASSWORD_PARAMETER_NAME', '/test/param'):
            with patch('app.core.auth.get_admin_password') as mock_get:
                mock_get.return_value = 'ssm_secret_password'
                result = auth.resolve_admin_password()
                assert result == 'ssm_secret_password'
                mock_get.assert_called_once_with('/test/param')

    def test_falls_back_to_env_when_ssm_fails(self):
        """Should fall back to ADMIN_PASSWORD when SSM returns None."""
        with patch.object(auth, 'ADMIN_PASSWORD_PARAMETER_NAME', '/test/param'):
            with patch.object(auth, 'ADMIN_PASSWORD', 'fallback_password'):
                with patch('app.core.auth.get_admin_password') as mock_get:
                    mock_get.return_value = None
                    result = auth.resolve_admin_password()
                    assert result == 'fallback_password'


class TestIsSessionValid:
    """Test _is_session_valid function."""

    def test_returns_true_for_local_session(self):
        """Should return True for session in local cache."""
        auth._active_sessions.add('test_token')
        try:
            assert auth._is_session_valid('test_token') is True
        finally:
            auth._active_sessions.discard('test_token')

    def test_returns_true_for_store_session(self):
        """Should return True for session in store."""
        with patch('app.services.store.session_exists') as mock_session_exists:
            mock_session_exists.return_value = True
            assert auth._is_session_valid('test_token') is True

    def test_returns_false_for_invalid_session(self):
        """Should return False for unknown session."""
        auth._active_sessions.discard('test_token')
        with patch('app.services.store.session_exists') as mock_session_exists:
            mock_session_exists.return_value = False
            assert auth._is_session_valid('test_token') is False

    def test_caches_store_session(self):
        """Should add store session to local cache."""
        auth._active_sessions.discard('test_token')
        with patch('app.services.store.session_exists') as mock_session_exists:
            mock_session_exists.return_value = True
            auth._is_session_valid('test_token')
            assert 'test_token' in auth._active_sessions
            auth._active_sessions.discard('test_token')


class TestGetCurrentAdmin:
    """Test get_current_admin function."""

    def test_raises_401_when_no_cookie(self):
        """Should raise 401 when no session cookie."""
        mock_request = MagicMock()
        mock_request.cookies = {}

        with patch.object(auth, '_is_session_valid', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                auth.get_current_admin(mock_request)

            assert exc_info.value.status_code == 401
            assert "administrateur" in exc_info.value.detail.lower()

    def test_raises_401_when_invalid_session(self):
        """Should raise 401 when session is invalid."""
        mock_request = MagicMock()
        mock_request.cookies = {auth.ADMIN_SESSION_COOKIE: 'invalid_token'}

        with patch.object(auth, '_is_session_valid', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                auth.get_current_admin(mock_request)

            assert exc_info.value.status_code == 401

    def test_returns_username_when_authenticated(self):
        """Should return ADMIN_USERNAME when authenticated."""
        mock_request = MagicMock()
        mock_request.cookies = {auth.ADMIN_SESSION_COOKIE: 'valid_token'}

        with patch.object(auth, '_is_session_valid', return_value=True):
            result = auth.get_current_admin(mock_request)
            assert result == auth.ADMIN_USERNAME


class TestLoginAdmin:
    """Test login_admin function."""

    def test_raises_401_for_wrong_password(self):
        """Should raise 401 for wrong password."""
        mock_response = MagicMock()

        with patch('app.core.auth.resolve_admin_password', return_value='correct_password'):
            with pytest.raises(HTTPException) as exc_info:
                auth.login_admin(mock_response, 'admin', 'wrong_password')

            assert exc_info.value.status_code == 401

    def test_raises_401_for_wrong_username(self):
        """Should raise 401 for wrong username."""
        mock_response = MagicMock()

        with patch('app.core.auth.resolve_admin_password', return_value='password'):
            with pytest.raises(HTTPException) as exc_info:
                auth.login_admin(mock_response, 'wrong_user', 'password')

            assert exc_info.value.status_code == 401

    def test_sets_cookie_on_successful_login(self):
        """Should set session cookie and create session."""
        mock_response = MagicMock()
        mock_response.set_cookie = MagicMock()

        with patch('app.core.auth.resolve_admin_password', return_value='password'):
            with patch('app.services.store.save_session') as mock_save:
                auth.login_admin(mock_response, 'admin', 'password')

                # Verify cookie was set
                assert mock_response.set_cookie.called
                cookie_call = mock_response.set_cookie.call_args
                assert cookie_call[1]['key'] == auth.ADMIN_SESSION_COOKIE
                assert cookie_call[1]['httponly'] is True

                # Verify session was saved
                assert mock_save.called

    def test_cookie_security_settings(self):
        """Should set cookie with security settings."""
        mock_response = MagicMock()

        with patch('app.core.auth.resolve_admin_password', return_value='password'):
            with patch('app.core.auth._COOKIE_SAMESITE', 'strict'):
                with patch('app.core.auth._USE_SECURE_COOKIE', True):
                    auth.login_admin(mock_response, 'admin', 'password')

                    cookie_call = mock_response.set_cookie.call_args
                    assert cookie_call[1]['samesite'] == 'strict'
                    assert cookie_call[1]['secure'] is True


class TestLogoutAdmin:
    """Test logout_admin function."""

    def test_deletes_cookie(self):
        """Should delete session cookie."""
        mock_response = MagicMock()
        mock_response.delete_cookie = MagicMock()

        auth.logout_admin(mock_response)

        mock_response.delete_cookie.assert_called_once_with(
            key=auth.ADMIN_SESSION_COOKIE
        )


class TestInvalidateSession:
    """Test invalidate_session function."""

    def test_removes_from_local_cache(self):
        """Should remove session from local cache."""
        auth._active_sessions.add('test_token')
        try:
            with patch('app.services.store.delete_session') as mock_delete:
                auth.invalidate_session('test_token')
                assert 'test_token' not in auth._active_sessions
        finally:
            auth._active_sessions.discard('test_token')

    def test_deletes_from_store(self):
        """Should delete session from store."""
        with patch('app.services.store.delete_session') as mock_delete:
            auth.invalidate_session('test_token')
            mock_delete.assert_called_once_with('test_token')


class TestIsAdminAuthenticated:
    """Test is_admin_authenticated function."""

    def test_returns_false_when_no_cookie(self):
        """Should return False when no cookie."""
        mock_request = MagicMock()
        mock_request.cookies = {}

        result = auth.is_admin_authenticated(mock_request)
        assert result is False

    def test_returns_false_when_invalid_session(self):
        """Should return False when session is invalid."""
        mock_request = MagicMock()
        mock_request.cookies = {auth.ADMIN_SESSION_COOKIE: 'invalid_token'}

        with patch.object(auth, '_is_session_valid', return_value=False):
            result = auth.is_admin_authenticated(mock_request)
            assert result is False

    def test_returns_true_when_authenticated(self):
        """Should return True when authenticated."""
        mock_request = MagicMock()
        mock_request.cookies = {auth.ADMIN_SESSION_COOKIE: 'valid_token'}

        with patch.object(auth, '_is_session_valid', return_value=True):
            result = auth.is_admin_authenticated(mock_request)
            assert result is True
