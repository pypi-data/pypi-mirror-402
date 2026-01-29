"""Tests for the PantherClient class."""

import pytest

from panther_sdk import PantherClient, PantherConfig
from panther_sdk.exceptions import ConfigurationError


class TestPantherClientInit:
    """Tests for PantherClient initialization."""

    def test_init_with_explicit_credentials(self):
        """Test client initialization with explicit credentials."""
        client = PantherClient(
            api_host="test.runpanther.net",
            api_token="test-token",
        )
        assert client.config.api_host == "https://test.runpanther.net"
        assert client.config.api_token == "test-token"
        client.close()

    def test_init_with_https_prefix(self):
        """Test client initialization with https:// prefix."""
        client = PantherClient(
            api_host="https://test.runpanther.net",
            api_token="test-token",
        )
        assert client.config.api_host == "https://test.runpanther.net"
        client.close()

    def test_init_with_trailing_slash(self):
        """Test client initialization with trailing slash."""
        client = PantherClient(
            api_host="test.runpanther.net/",
            api_token="test-token",
        )
        assert client.config.api_host == "https://test.runpanther.net"
        client.close()

    def test_init_missing_host_raises_error(self, monkeypatch):
        """Test that missing host raises ConfigurationError."""
        monkeypatch.delenv("PANTHER_API_HOST", raising=False)
        monkeypatch.delenv("PANTHER_HOST", raising=False)
        with pytest.raises(ConfigurationError, match="api_host is required"):
            PantherClient(api_token="test-token")

    def test_init_missing_token_raises_error(self, monkeypatch):
        """Test that missing token raises ConfigurationError."""
        monkeypatch.delenv("PANTHER_API_TOKEN", raising=False)
        monkeypatch.delenv("PANTHER_TOKEN", raising=False)
        with pytest.raises(ConfigurationError, match="api_token is required"):
            PantherClient(api_host="test.runpanther.net")

    def test_config_base_url(self):
        """Test that base URL is constructed correctly."""
        client = PantherClient(
            api_host="test.runpanther.net",
            api_token="test-token",
        )
        assert client.config.base_url == "https://test.runpanther.net/public"
        assert client.config.rest_url == "https://test.runpanther.net/public/v1"
        assert client.config.graphql_url == "https://test.runpanther.net/public/graphql"
        client.close()


class TestPantherClientResources:
    """Tests for PantherClient resource access."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        c = PantherClient(
            api_host="test.runpanther.net",
            api_token="test-token",
        )
        yield c
        c.close()

    def test_alerts_resource(self, client):
        """Test accessing alerts resource."""
        from panther_sdk.api.rest import AlertsResource
        assert isinstance(client.alerts, AlertsResource)

    def test_rules_resource(self, client):
        """Test accessing rules resource."""
        from panther_sdk.api.rest import RulesResource
        assert isinstance(client.rules, RulesResource)

    def test_policies_resource(self, client):
        """Test accessing policies resource."""
        from panther_sdk.api.rest import PoliciesResource
        assert isinstance(client.policies, PoliciesResource)

    def test_queries_resource(self, client):
        """Test accessing queries resource."""
        from panther_sdk.api.rest import QueriesResource
        assert isinstance(client.queries, QueriesResource)

    def test_users_resource(self, client):
        """Test accessing users resource."""
        from panther_sdk.api.rest import UsersResource
        assert isinstance(client.users, UsersResource)

    def test_roles_resource(self, client):
        """Test accessing roles resource."""
        from panther_sdk.api.rest import RolesResource
        assert isinstance(client.roles, RolesResource)

    def test_data_models_resource(self, client):
        """Test accessing data_models resource."""
        from panther_sdk.api.rest import DataModelsResource
        assert isinstance(client.data_models, DataModelsResource)

    def test_log_sources_resource(self, client):
        """Test accessing log_sources resource."""
        from panther_sdk.api.rest import LogSourcesResource
        assert isinstance(client.log_sources, LogSourcesResource)

    def test_globals_resource(self, client):
        """Test accessing globals resource."""
        from panther_sdk.api.rest import GlobalsResource
        assert isinstance(client.globals, GlobalsResource)

    def test_graphql_client(self, client):
        """Test accessing GraphQL client."""
        from panther_sdk.api.graphql import GraphQLClient
        assert isinstance(client.graphql, GraphQLClient)


class TestPantherClientContextManager:
    """Tests for PantherClient context manager."""

    def test_sync_context_manager(self):
        """Test using client as sync context manager."""
        with PantherClient(
            api_host="test.runpanther.net",
            api_token="test-token",
        ) as client:
            assert client.config.api_host == "https://test.runpanther.net"

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test using client as async context manager."""
        async with PantherClient(
            api_host="test.runpanther.net",
            api_token="test-token",
        ) as client:
            assert client.config.api_host == "https://test.runpanther.net"
