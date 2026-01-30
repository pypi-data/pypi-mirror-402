"""Tests for the unified catalog system."""

import pytest

from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier
from yirifi_mcp.core.route_filters import MCPType


class TestEndpoint:
    """Tests for Endpoint dataclass."""

    def test_endpoint_creation(self):
        """Test basic endpoint creation."""
        endpoint = Endpoint(
            "get_user_list",
            "GET",
            "/users/",
            "List all users",
            Tier.DIRECT,
        )
        assert endpoint.name == "get_user_list"
        assert endpoint.method == "GET"
        assert endpoint.path == "/users/"
        assert endpoint.tier == Tier.DIRECT
        assert endpoint.risk_level == "low"

    def test_endpoint_with_risk_level(self):
        """Test endpoint with custom risk level."""
        endpoint = Endpoint(
            "delete_user_detail",
            "DELETE",
            "/users/{user_id}",
            "Delete user",
            Tier.GATEWAY,
            risk_level="high",
        )
        assert endpoint.risk_level == "high"

    def test_endpoint_method_normalized(self):
        """Test that HTTP method is normalized to uppercase."""
        endpoint = Endpoint("test", "get", "/test", "Test", Tier.DIRECT)
        assert endpoint.method == "GET"

    def test_invalid_method_raises(self):
        """Test that invalid HTTP method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            Endpoint("test", "INVALID", "/test", "Test", Tier.DIRECT)

    def test_invalid_risk_level_raises(self):
        """Test that invalid risk level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid risk level"):
            Endpoint("test", "GET", "/test", "Test", Tier.GATEWAY, risk_level="extreme")


class TestServiceCatalog:
    """Tests for ServiceCatalog class."""

    @pytest.fixture
    def sample_endpoints(self):
        """Sample endpoints for testing."""
        return [
            Endpoint("get_item_list", "GET", "/items/", "List items", Tier.DIRECT),
            Endpoint("get_item_detail", "GET", "/items/{id}", "Get item", Tier.DIRECT),
            Endpoint("post_item_list", "POST", "/items/", "Create item", Tier.DIRECT),
            Endpoint(
                "delete_item_detail",
                "DELETE",
                "/items/{id}",
                "Delete",
                Tier.GATEWAY,
                risk_level="high",
            ),
            Endpoint("post_admin_op", "POST", "/admin/op", "Admin", Tier.GATEWAY, risk_level="medium"),
            Endpoint("get_internal", "GET", "/internal", "Internal", Tier.EXCLUDE),
        ]

    @pytest.fixture
    def catalog(self, sample_endpoints):
        """Sample catalog for testing."""
        return ServiceCatalog(sample_endpoints)

    def test_catalog_creation(self, catalog):
        """Test catalog is created correctly."""
        assert len(catalog) == 6

    def test_get_direct_endpoints(self, catalog):
        """Test getting direct tier endpoints."""
        direct = catalog.get_direct_endpoints()
        assert len(direct) == 3
        assert all(e.tier == Tier.DIRECT for e in direct)

    def test_get_gateway_endpoints(self, catalog):
        """Test getting gateway tier endpoints."""
        gateway = catalog.get_gateway_endpoints()
        assert len(gateway) == 2
        assert all(e.tier == Tier.GATEWAY for e in gateway)

    def test_get_all_endpoints_excludes_excluded(self, catalog):
        """Test that get_all_endpoints excludes EXCLUDE tier."""
        all_endpoints = catalog.get_all_endpoints()
        assert len(all_endpoints) == 5
        assert not any(e.tier == Tier.EXCLUDE for e in all_endpoints)

    def test_get_endpoint(self, catalog):
        """Test looking up endpoint by name."""
        endpoint = catalog.get_endpoint("get_item_list")
        assert endpoint is not None
        assert endpoint.path == "/items/"

    def test_get_endpoint_not_found(self, catalog):
        """Test looking up non-existent endpoint."""
        assert catalog.get_endpoint("nonexistent") is None

    def test_duplicate_names_raises(self):
        """Test that duplicate endpoint names raise ValueError."""
        endpoints = [
            Endpoint("same_name", "GET", "/a", "A", Tier.DIRECT),
            Endpoint("same_name", "POST", "/b", "B", Tier.DIRECT),
        ]
        with pytest.raises(ValueError, match="Duplicate endpoint names"):
            ServiceCatalog(endpoints)

    def test_direct_count(self, catalog):
        """Test direct_count property."""
        assert catalog.direct_count == 3

    def test_gateway_count(self, catalog):
        """Test gateway_count property."""
        assert catalog.gateway_count == 2

    # -------------------------------------------------------------------------
    # Route map generation tests (moved from CatalogBuilder)
    # -------------------------------------------------------------------------

    def test_to_route_maps(self, catalog):
        """Test generating RouteMap list."""
        route_maps = catalog.to_route_maps()
        # 3 direct endpoints + 1 catch-all exclusion
        assert len(route_maps) == 4
        assert route_maps[-1].mcp_type == MCPType.EXCLUDE
        assert route_maps[-1].pattern == r".*"

    def test_route_map_patterns(self, catalog):
        """Test that path patterns are converted correctly."""
        route_maps = catalog.to_route_maps()
        patterns = [rm.pattern for rm in route_maps[:-1]]

        assert "^/items/$" in patterns
        assert "^/items/[^/]+$" in patterns

    def test_route_map_methods(self, catalog):
        """Test that methods are set correctly."""
        route_maps = catalog.to_route_maps()
        # Find the list route (GET /items/)
        list_rm = next(rm for rm in route_maps if rm.pattern == "^/items/$" and rm.methods == ["GET"])
        assert list_rm.mcp_type == MCPType.TOOL

    def test_path_to_pattern(self):
        """Test path to regex pattern conversion."""
        assert ServiceCatalog._path_to_pattern("/users/") == "^/users/$"
        assert ServiceCatalog._path_to_pattern("/users/{user_id}") == "^/users/[^/]+$"
        assert ServiceCatalog._path_to_pattern("/a/{b}/c/{d}") == "^/a/[^/]+/c/[^/]+$"

    # -------------------------------------------------------------------------
    # Gateway catalog generation tests (moved from CatalogBuilder)
    # -------------------------------------------------------------------------

    def test_to_gateway_catalog(self, catalog):
        """Test generating gateway catalog dict."""
        gateway_catalog = catalog.to_gateway_catalog()
        assert len(gateway_catalog) == 5  # All non-excluded endpoints

        assert "get_item_list" in gateway_catalog
        assert gateway_catalog["get_item_list"]["method"] == "GET"
        assert gateway_catalog["get_item_list"]["path"] == "/items/"
        assert gateway_catalog["get_item_list"]["desc"] == "List items"

        assert "delete_item_detail" in gateway_catalog  # Gateway endpoint included
        assert gateway_catalog["delete_item_detail"]["risk_level"] == "high"

    def test_to_api_catalog_alias(self, catalog):
        """Test that to_api_catalog is an alias for to_gateway_catalog."""
        assert catalog.to_api_catalog() == catalog.to_gateway_catalog()

    def test_get_stats(self, catalog):
        """Test catalog statistics."""
        stats = catalog.get_stats()
        assert stats["total"] == 6
        assert stats["direct"] == 3
        assert stats["gateway"] == 2
        assert stats["excluded"] == 1
        assert stats["high_risk"] == 1
        assert stats["medium_risk"] == 1
        assert stats["low_risk"] == 0
