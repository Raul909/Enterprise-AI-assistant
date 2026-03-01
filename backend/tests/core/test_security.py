import pytest
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from core.security import decode_token, create_token
from core.config import settings

def test_decode_token_valid():
    """Test decoding a valid token."""
    data = {"sub": "123", "email": "test@example.com", "role": "user"}
    token = create_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"
    assert "exp" in payload
    assert "type" in payload

def test_decode_token_expired():
    """Test decoding an expired token."""
    # Manually create an expired token
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    to_encode = {
        "sub": "123",
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid or expired token"

def test_decode_token_invalid_signature():
    """Test decoding a token with an invalid signature."""
    data = {"sub": "123"}
    # Sign with a different key
    token = jwt.encode(
        data,
        "wrong-secret-key",
        algorithm=settings.jwt_algorithm
    )

    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid or expired token"

def test_decode_token_malformed():
    """Test decoding a malformed token."""
    token = "invalid-token-string"

    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid or expired token"

def test_decode_token_wrong_algorithm():
    """Test decoding a token signed with a different algorithm."""
    # Assuming the server expects HS256 (default in settings)

    data = {"sub": "123"}
    # Sign with a different algorithm
    token = jwt.encode(
        data,
        settings.jwt_secret_key,
        algorithm="HS384"
    )

    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid or expired token"
from datetime import datetime, timedelta, timezone
from jose import jwt
from unittest.mock import patch
from app.core.security import create_token

# Test data
SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

@pytest.fixture
def mock_settings():
    with patch("app.core.security.settings") as mock_settings:
        mock_settings.jwt_secret_key = SECRET_KEY
        mock_settings.jwt_algorithm = ALGORITHM
        mock_settings.jwt_access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        mock_settings.jwt_refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
        yield mock_settings

def test_create_access_token(mock_settings):
    data = {"sub": "user123", "email": "test@example.com"}
    token = create_token(data, token_type="access")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    assert payload["type"] == "access"

    # Check expiration
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

    expected_exp = iat + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Allow small difference due to execution time
    assert abs((exp - expected_exp).total_seconds()) < 5

def test_create_refresh_token(mock_settings):
    data = {"sub": "user123"}
    token = create_token(data, token_type="refresh")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "user123"
    assert payload["type"] == "refresh"

    # Check expiration
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

    expected_exp = iat + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    assert abs((exp - expected_exp).total_seconds()) < 5

def test_create_token_default_type(mock_settings):
    data = {"sub": "user123"}
    token = create_token(data) # default should be "access"

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "access"

def test_create_token_custom_data(mock_settings):
    data = {"sub": "user123", "custom_claim": "custom_value"}
    token = create_token(data, token_type="access")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["custom_claim"] == "custom_value"

def test_create_token_unknown_type(mock_settings):
    """Test that unknown token types default to refresh token expiration behavior."""
    data = {"sub": "user123"}
    token = create_token(data, token_type="unknown")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["type"] == "unknown"

    # Check expiration - currently defaults to refresh token expiration
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

    expected_exp = iat + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    assert abs((exp - expected_exp).total_seconds()) < 5
