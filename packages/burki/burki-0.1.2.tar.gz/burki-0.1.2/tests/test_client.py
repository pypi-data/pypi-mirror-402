"""Tests for the BurkiClient."""

import pytest
from unittest.mock import Mock, patch

from burki import BurkiClient
from burki.exceptions import AuthenticationError, NotFoundError, ValidationError


class TestBurkiClient:
    """Tests for the BurkiClient class."""

    def test_client_initialization(self):
        """Test client initialization with API key."""
        client = BurkiClient(api_key="test-api-key")
        assert client is not None

    def test_client_initialization_no_api_key(self):
        """Test client initialization fails without API key."""
        with pytest.raises(ValueError):
            BurkiClient(api_key="")

    def test_client_has_resources(self):
        """Test client has all resource properties."""
        client = BurkiClient(api_key="test-api-key")
        
        assert client.assistants is not None
        assert client.calls is not None
        assert client.phone_numbers is not None
        assert client.documents is not None
        assert client.tools is not None
        assert client.sms is not None
        assert client.campaigns is not None
        assert client.realtime is not None

    def test_client_context_manager(self):
        """Test client works as context manager."""
        with BurkiClient(api_key="test-api-key") as client:
            assert client is not None


class TestAssistantsResource:
    """Tests for the AssistantsResource class."""

    @pytest.fixture
    def client(self):
        return BurkiClient(api_key="test-api-key")

    @patch("burki.http_client.HTTPClient.get")
    def test_list_assistants(self, mock_get, client):
        """Test listing assistants."""
        mock_get.return_value = [
            {"id": 1, "name": "Test Assistant", "organization_id": 1, "is_active": True}
        ]
        
        assistants = client.assistants.list()
        
        assert len(assistants) == 1
        assert assistants[0].id == 1
        assert assistants[0].name == "Test Assistant"

    @patch("burki.http_client.HTTPClient.get")
    def test_get_assistant(self, mock_get, client):
        """Test getting a specific assistant."""
        mock_get.return_value = {
            "id": 1,
            "name": "Test Assistant",
            "organization_id": 1,
            "is_active": True,
        }
        
        assistant = client.assistants.get(assistant_id=1)
        
        assert assistant.id == 1
        assert assistant.name == "Test Assistant"

    @patch("burki.http_client.HTTPClient.post")
    def test_create_assistant(self, mock_post, client):
        """Test creating an assistant."""
        mock_post.return_value = {
            "id": 1,
            "name": "New Assistant",
            "organization_id": 1,
            "is_active": True,
        }
        
        assistant = client.assistants.create(name="New Assistant")
        
        assert assistant.id == 1
        assert assistant.name == "New Assistant"

    @patch("burki.http_client.HTTPClient.delete")
    def test_delete_assistant(self, mock_delete, client):
        """Test deleting an assistant."""
        mock_delete.return_value = None
        
        result = client.assistants.delete(assistant_id=1)
        
        assert result is True


class TestCallsResource:
    """Tests for the CallsResource class."""

    @pytest.fixture
    def client(self):
        return BurkiClient(api_key="test-api-key")

    @patch("burki.http_client.HTTPClient.get")
    def test_list_calls(self, mock_get, client):
        """Test listing calls."""
        mock_get.return_value = {
            "items": [
                {
                    "id": 1,
                    "call_sid": "CA123",
                    "assistant_id": 1,
                    "status": "completed",
                }
            ]
        }
        
        calls = client.calls.list()
        
        assert len(calls) == 1
        assert calls[0].id == 1
        assert calls[0].call_sid == "CA123"

    @patch("burki.http_client.HTTPClient.get")
    def test_get_transcripts(self, mock_get, client):
        """Test getting call transcripts."""
        mock_get.return_value = [
            {
                "id": 1,
                "call_id": 1,
                "speaker": "user",
                "content": "Hello",
                "is_final": True,
            }
        ]
        
        transcripts = client.calls.get_transcripts(call_id=1)
        
        assert len(transcripts) == 1
        assert transcripts[0].speaker == "user"
        assert transcripts[0].content == "Hello"


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def client(self):
        return BurkiClient(api_key="test-api-key")

    @patch("burki.http_client.HTTPClient.get")
    def test_authentication_error(self, mock_get, client):
        """Test authentication error handling."""
        from burki.exceptions import AuthenticationError
        
        mock_get.side_effect = AuthenticationError("Invalid API key")
        
        with pytest.raises(AuthenticationError):
            client.assistants.list()

    @patch("burki.http_client.HTTPClient.get")
    def test_not_found_error(self, mock_get, client):
        """Test not found error handling."""
        from burki.exceptions import NotFoundError
        
        mock_get.side_effect = NotFoundError("Assistant not found")
        
        with pytest.raises(NotFoundError):
            client.assistants.get(assistant_id=999)
