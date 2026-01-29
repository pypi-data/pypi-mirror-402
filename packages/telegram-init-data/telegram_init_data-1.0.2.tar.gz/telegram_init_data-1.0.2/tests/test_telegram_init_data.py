"""
Tests for telegram_init_data library.

Contains comprehensive tests for all functions and edge cases.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

from telegram_init_data import (
    hash_token,
    sign_data,
    validate,
    is_valid,
    parse,
    sign,
    validate3rd,
    is_valid3rd,
    TelegramInitDataError,
    AuthDateInvalidError,
    SignatureInvalidError,
    SignatureMissingError,
    ExpiredError,
    User,
    Chat,
    ChatType,
    InitData,
)


class TestHashToken:
    """Tests for hash_token function."""
    
    def test_hash_token_string(self):
        """Test hashing string token."""
        token = "test_token"
        result = hash_token(token)
        assert isinstance(result, bytes)
        assert len(result) == 32  # SHA256 produces 32 bytes
    
    def test_hash_token_bytes(self):
        """Test hashing bytes token."""
        token = b"test_token"
        result = hash_token(token)
        assert isinstance(result, bytes)
        assert len(result) == 32
    
    def test_hash_token_consistency(self):
        """Test that same token produces same hash."""
        token = "test_token"
        result1 = hash_token(token)
        result2 = hash_token(token)
        assert result1 == result2


class TestSignData:
    """Tests for sign_data function."""
    
    def test_sign_data_string(self):
        """Test signing string data."""
        data = "test_data"
        token = "test_token"
        result = sign_data(data, token)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex is 64 chars
    
    def test_sign_data_bytes(self):
        """Test signing bytes data."""
        data = b"test_data"
        token = "test_token"
        result = sign_data(data, token)
        assert isinstance(result, str)
        assert len(result) == 64
    
    def test_sign_data_consistency(self):
        """Test that same data produces same signature."""
        data = "test_data"
        token = "test_token"
        result1 = sign_data(data, token)
        result2 = sign_data(data, token)
        assert result1 == result2


class TestValidate:
    """Tests for validate function."""
    
    def setup_method(self):
        """Setup test data."""
        self.token = "test_token"
        self.current_time = int(time.time())
        
        # Create valid init data
        self.valid_data = {
            "query_id": "test_query",
            "auth_date": str(self.current_time),
        }
        
        # Create check string and signature
        pairs = [f"{key}={value}" for key, value in sorted(self.valid_data.items())]
        check_string = "\n".join(pairs)
        signature = sign_data(check_string, self.token)
        
        self.valid_init_data = f"auth_date={self.current_time}&query_id=test_query&hash={signature}"
    
    def test_validate_valid_data(self):
        """Test validation with valid data."""
        # Should not raise exception
        validate(self.valid_init_data, self.token)
    
    def test_validate_missing_hash(self):
        """Test validation with missing hash."""
        data = f"auth_date={self.current_time}&query_id=test_query"
        with pytest.raises(SignatureMissingError):
            validate(data, self.token)
    
    def test_validate_invalid_auth_date(self):
        """Test validation with invalid auth_date."""
        data = "auth_date=invalid&query_id=test_query&hash=abc123"
        with pytest.raises(AuthDateInvalidError):
            validate(data, self.token)
    
    def test_validate_missing_auth_date(self):
        """Test validation with missing auth_date."""
        data = "query_id=test_query&hash=abc123"
        with pytest.raises(AuthDateInvalidError):
            validate(data, self.token)
    
    def test_validate_expired_data(self):
        """Test validation with expired data."""
        old_time = self.current_time - 86401  # More than 24 hours ago
        data = f"auth_date={old_time}&query_id=test_query&hash=abc123"
        with pytest.raises(ExpiredError):
            validate(data, self.token)
    
    def test_validate_invalid_signature(self):
        """Test validation with invalid signature."""
        data = f"auth_date={self.current_time}&query_id=test_query&hash=invalid_signature"
        with pytest.raises(SignatureInvalidError):
            validate(data, self.token)
    
    def test_validate_custom_expires_in(self):
        """Test validation with custom expiration time."""
        old_time = self.current_time - 3600  # 1 hour ago
        data = f"auth_date={old_time}&query_id=test_query&hash=abc123"
        
        # Should raise with 30 min expiration
        with pytest.raises(ExpiredError):
            validate(data, self.token, {"expires_in": 1800})
    
    def test_validate_no_expiration(self):
        """Test validation with no expiration check."""
        old_time = self.current_time - 86401  # More than 24 hours ago
        
        # Create valid signature for old data
        test_data = {"auth_date": str(old_time), "query_id": "test_query"}
        pairs = [f"{key}={value}" for key, value in sorted(test_data.items())]
        check_string = "\n".join(pairs)
        signature = sign_data(check_string, self.token)
        
        data = f"auth_date={old_time}&query_id=test_query&hash={signature}"
        
        # Should not raise with expires_in=0
        validate(data, self.token, {"expires_in": 0})


class TestIsValid:
    """Tests for is_valid function."""
    
    def test_is_valid_true(self):
        """Test is_valid with valid data."""
        current_time = int(time.time())
        test_data = {"auth_date": str(current_time), "query_id": "test_query"}
        pairs = [f"{key}={value}" for key, value in sorted(test_data.items())]
        check_string = "\n".join(pairs)
        signature = sign_data(check_string, "test_token")
        
        data = f"auth_date={current_time}&query_id=test_query&hash={signature}"
        
        assert is_valid(data, "test_token") is True
    
    def test_is_valid_false(self):
        """Test is_valid with invalid data."""
        data = "auth_date=invalid&query_id=test_query&hash=abc123"
        assert is_valid(data, "test_token") is False
    
    def test_is_valid_exception_handling(self):
        """Test that is_valid handles all exceptions properly."""
        # Missing hash
        assert is_valid("auth_date=123&query_id=test", "token") is False
        
        # Invalid auth_date
        assert is_valid("auth_date=invalid&hash=abc", "token") is False
        
        # Expired data
        old_time = int(time.time()) - 86401
        assert is_valid(f"auth_date={old_time}&hash=abc", "token") is False


class TestParse:
    """Tests for parse function."""
    
    def test_parse_simple_string(self):
        """Test parsing simple init data string."""
        data = "query_id=test&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["query_id"] == "test"
        assert result["auth_date"] == 1234567890
        assert result["hash"] == "abc123"
    
    def test_parse_with_user(self):
        """Test parsing init data with user object."""
        user_json = '{"id":123,"first_name":"John","last_name":"Doe"}'
        data = f"user={user_json}&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["user"]["id"] == 123
        assert result["user"]["first_name"] == "John"
        assert result["user"]["last_name"] == "Doe"
        assert result["auth_date"] == 1234567890
    
    def test_parse_with_chat(self):
        """Test parsing init data with chat object."""
        chat_json = '{"id":456,"type":"group","title":"Test Group"}'
        data = f"chat={chat_json}&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["chat"]["id"] == 456
        assert result["chat"]["type"] == ChatType.GROUP
        assert result["chat"]["title"] == "Test Group"
    
    def test_parse_with_chat_type_sender(self):
        """Test parsing init data with chat_type=sender."""
        data = "chat_type=sender&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["chat_type"] == ChatType.SENDER
        assert result["auth_date"] == 1234567890
    
    def test_parse_with_chat_sender_type(self):
        """Test parsing init data with chat object having sender type."""
        chat_json = '{"id":789,"type":"sender"}'
        data = f"chat={chat_json}&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["chat"]["id"] == 789
        assert result["chat"]["type"] == ChatType.SENDER
    
    def test_parse_dict_input(self):
        """Test parsing dict input."""
        data = {"query_id": "test", "auth_date": 1234567890}
        result = parse(data)
        
        assert result["query_id"] == "test"
        assert result["auth_date"] == 1234567890
    
    def test_parse_url_encoded_user(self):
        """Test parsing URL-encoded user data."""
        # URL-encoded JSON: {"id":123,"first_name":"John"}
        data = "user=%7B%22id%22%3A123%2C%22first_name%22%3A%22John%22%7D&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["user"]["id"] == 123
        assert result["user"]["first_name"] == "John"
    
    def test_parse_invalid_json(self):
        """Test parsing with invalid JSON in user field."""
        data = "user=invalid_json&auth_date=1234567890&hash=abc123"
        result = parse(data)
        
        assert result["user"] is None
        assert result["auth_date"] == 1234567890


class TestSign:
    """Tests for sign function."""
    
    def test_sign_simple_data(self):
        """Test signing simple data."""
        data = {"query_id": "test", "user": {"id": 123, "first_name": "John"}}
        auth_date = datetime.now()
        token = "test_token"
        
        result = sign(data, token, auth_date)
        
        assert isinstance(result, str)
        assert "hash=" in result
        assert "auth_date=" in result
        assert "query_id=test" in result
    
    def test_sign_and_validate_cycle(self):
        """Test that signed data can be validated."""
        data = {"query_id": "test", "user": {"id": 123, "first_name": "John"}}
        auth_date = datetime.now()
        token = "test_token"
        
        signed_data = sign(data, token, auth_date)
        
        # Should validate successfully
        validate(signed_data, token)
        assert is_valid(signed_data, token) is True
    
    def test_sign_removes_existing_hash(self):
        """Test that existing hash is removed when signing."""
        data = {"query_id": "test", "hash": "old_hash"}
        auth_date = datetime.now()
        token = "test_token"
        
        signed_data = sign(data, token, auth_date)
        
        # Should have new hash, not old one
        assert "hash=old_hash" not in signed_data
        assert "hash=" in signed_data


class TestValidate3rd:
    """Tests for validate3rd function."""
    
    def test_validate3rd_valid_data(self):
        """Test 3rd party validation with valid data."""
        current_time = int(time.time())
        data = f"auth_date={current_time}&query_id=test&signature=valid_signature"
        
        def mock_verify(verification_string, public_key, signature):
            return signature == "valid_signature"
        
        # Should not raise exception
        validate3rd(data, 123456, mock_verify)
    
    def test_validate3rd_missing_signature(self):
        """Test 3rd party validation with missing signature."""
        current_time = int(time.time())
        data = f"auth_date={current_time}&query_id=test"
        
        def mock_verify(verification_string, public_key, signature):
            return True
        
        with pytest.raises(SignatureMissingError) as exc_info:
            validate3rd(data, 123456, mock_verify)
        
        assert exc_info.value.third_party is True
    
    def test_validate3rd_invalid_signature(self):
        """Test 3rd party validation with invalid signature."""
        current_time = int(time.time())
        data = f"auth_date={current_time}&query_id=test&signature=invalid_signature"
        
        def mock_verify(verification_string, public_key, signature):
            return False
        
        with pytest.raises(SignatureInvalidError):
            validate3rd(data, 123456, mock_verify)
    
    def test_validate3rd_test_mode(self):
        """Test 3rd party validation in test mode."""
        current_time = int(time.time())
        data = f"auth_date={current_time}&query_id=test&signature=test_signature"
        
        def mock_verify(verification_string, public_key, signature):
            # Check that test public key is used
            assert public_key == "40055058a4ee38156a06562e52eece92a771bcd8346a8c4615cb7376eddf72ec"
            return True
        
        validate3rd(data, 123456, mock_verify, {"test": True})


class TestIsValid3rd:
    """Tests for is_valid3rd function."""
    
    def test_is_valid3rd_true(self):
        """Test is_valid3rd with valid data."""
        current_time = int(time.time())
        data = f"auth_date={current_time}&query_id=test&signature=valid_signature"
        
        def mock_verify(verification_string, public_key, signature):
            return True
        
        assert is_valid3rd(data, 123456, mock_verify) is True
    
    def test_is_valid3rd_false(self):
        """Test is_valid3rd with invalid data."""
        current_time = int(time.time())
        data = f"auth_date={current_time}&query_id=test&signature=invalid_signature"
        
        def mock_verify(verification_string, public_key, signature):
            return False
        
        assert is_valid3rd(data, 123456, mock_verify) is False
    
    def test_is_valid3rd_exception_handling(self):
        """Test that is_valid3rd handles all exceptions properly."""
        def mock_verify(verification_string, public_key, signature):
            return True
        
        # Missing signature
        assert is_valid3rd("auth_date=123&query_id=test", 123456, mock_verify) is False
        
        # Invalid auth_date
        assert is_valid3rd("auth_date=invalid&signature=abc", 123456, mock_verify) is False


class TestExceptions:
    """Tests for exception classes."""
    
    def test_auth_date_invalid_error(self):
        """Test AuthDateInvalidError."""
        error = AuthDateInvalidError("invalid_value")
        assert error.value == "invalid_value"
        assert "auth_date" in str(error)
        assert "invalid_value" in str(error)
    
    def test_signature_missing_error(self):
        """Test SignatureMissingError."""
        # Regular mode
        error = SignatureMissingError(False)
        assert error.third_party is False
        assert "hash" in str(error)
        
        # Third party mode
        error = SignatureMissingError(True)
        assert error.third_party is True
        assert "signature" in str(error)
    
    def test_expired_error(self):
        """Test ExpiredError."""
        issued_at = datetime.now() - timedelta(hours=2)
        expires_at = datetime.now() - timedelta(hours=1)
        now = datetime.now()
        
        error = ExpiredError(issued_at, expires_at, now)
        assert error.issued_at == issued_at
        assert error.expires_at == expires_at
        assert error.now == now
        assert "expired" in str(error).lower()


if __name__ == "__main__":
    pytest.main([__file__]) 