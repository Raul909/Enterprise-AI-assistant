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
