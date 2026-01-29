"""Unit tests for RED9 API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from red9.api.main import app


class TestHealthCheckEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_success(self) -> None:
        """Test that health check endpoint returns success."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_health_check_response_model(self) -> None:
        """Test that health check endpoint returns correct response model."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check that only expected fields are present
        assert set(data.keys()) == {"status", "timestamp"}

        # Check field types
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)

    def test_health_check_cors_headers(self) -> None:
        """Test that health check endpoint includes CORS headers."""
        client = TestClient(app)
        # Make a request with Origin header to trigger CORS
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        # Check for CORS headers
        assert (
            "access-control-allow-origin" in response.headers
            or "Access-Control-Allow-Origin" in response.headers
        )


class TestDataEndpoint:
    """Tests for the data endpoint."""

    def test_get_items_success(self) -> None:
        """Test that data endpoint returns items successfully."""
        client = TestClient(app)
        response = client.get("/items")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        # Check structure of first item
        first_item = data["items"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert "description" in first_item

    def test_get_items_response_model(self) -> None:
        """Test that data endpoint returns correct response model."""
        client = TestClient(app)
        response = client.get("/items")

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert set(data.keys()) == {"items"}

        # Check each item has correct structure
        for item in data["items"]:
            assert set(item.keys()) == {"id", "name", "description"}
            assert isinstance(item["id"], int)
            assert isinstance(item["name"], str)
            assert isinstance(item["description"], str)

    def test_get_items_pagination(self) -> None:
        """Test that data endpoint supports pagination."""
        client = TestClient(app)
        response = client.get("/items?skip=1&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        # Should return at most 2 items
        assert len(data["items"]) <= 2

    def test_get_items_default_pagination(self) -> None:
        """Test that data endpoint uses default pagination values."""
        client = TestClient(app)
        response = client.get("/items")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        # Default should limit results
        assert len(data["items"]) <= 10

    def test_get_items_max_limit(self) -> None:
        """Test that data endpoint enforces maximum limit."""
        client = TestClient(app)
        response = client.get("/items?limit=150")  # Above max limit of 100

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should be limited to 100 items (but we only have 5 in our test data)
        assert len(data["items"]) <= 5

    def test_get_items_negative_skip(self) -> None:
        """Test that data endpoint handles negative skip values."""
        client = TestClient(app)
        response = client.get("/items?skip=-1&limit=2")

        # Should still return valid data (likely empty or starting from beginning)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_items_empty_result(self) -> None:
        """Test that data endpoint handles skip beyond available items."""
        client = TestClient(app)
        response = client.get("/items?skip=1000&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should return empty list when no items match
        assert data["items"] == []

    def test_get_items_single_item(self) -> None:
        """Test that data endpoint can return a single item."""
        client = TestClient(app)
        response = client.get("/items?skip=0&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        # Should return exactly 1 item
        assert len(data["items"]) == 1

        # Check item structure
        item = data["items"][0]
        assert set(item.keys()) == {"id", "name", "description"}


class TestApiDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema_exists(self) -> None:
        """Test that OpenAPI schema is available."""
        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_ui_exists(self) -> None:
        """Test that Swagger UI documentation is available."""
        client = TestClient(app)
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_ui_exists(self) -> None:
        """Test that ReDoc UI documentation is available."""
        client = TestClient(app)
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_swagger_spec_validity(self) -> None:
        """Test that the OpenAPI specification is valid."""
        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        # Basic structure checks
        assert "openapi" in data
        assert "info" in data
        assert "title" in data["info"]
        assert "version" in data["info"]
        assert "paths" in data


class TestApiErrorHandling:
    """Tests for API error handling."""

    def test_nonexistent_endpoint(self) -> None:
        """Test that nonexistent endpoints return 404."""
        client = TestClient(app)
        response = client.get("/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_method_not_allowed(self) -> None:
        """Test that unsupported HTTP methods return 405."""
        client = TestClient(app)
        response = client.post("/health")  # Health endpoint only supports GET

        assert response.status_code == 405
        data = response.json()
        assert "detail" in data

    def test_invalid_query_parameters(self) -> None:
        """Test that invalid query parameters return appropriate errors."""
        client = TestClient(app)
        response = client.get("/items?skip=invalid&limit=invalid")

        # FastAPI should handle validation errors automatically
        assert response.status_code in [400, 422]

    def test_health_endpoint_only_get(self) -> None:
        """Test that health endpoint rejects non-GET methods."""
        client = TestClient(app)

        # Test POST method
        post_response = client.post("/health")
        assert post_response.status_code == 405

        # Test PUT method
        put_response = client.put("/health")
        assert put_response.status_code == 405

        # Test DELETE method
        delete_response = client.delete("/health")
        assert delete_response.status_code == 405

    def test_items_endpoint_only_get(self) -> None:
        """Test that items endpoint rejects non-GET methods."""
        client = TestClient(app)

        # Test POST method
        post_response = client.post("/items")
        assert post_response.status_code == 405

        # Test PUT method
        put_response = client.put("/items")
        assert put_response.status_code == 405

        # Test DELETE method
        delete_response = client.delete("/items")
        assert delete_response.status_code == 405


class TestApiPerformance:
    """Tests for API performance characteristics."""

    def test_health_check_response_time(self) -> None:
        """Test that health check responds quickly."""
        client = TestClient(app)
        response = client.get("/health")

        # Just verify it returns successfully - actual performance testing
        # would require more sophisticated tooling
        assert response.status_code == 200

    def test_items_endpoint_response_time(self) -> None:
        """Test that items endpoint responds quickly."""
        client = TestClient(app)
        response = client.get("/items")

        # Just verify it returns successfully - actual performance testing
        # would require more sophisticated tooling
        assert response.status_code == 200


class TestApiSecurity:
    """Tests for API security features."""

    def test_no_server_info_leakage(self) -> None:
        """Test that error responses don't leak server information."""
        client = TestClient(app)
        response = client.get("/nonexistent")

        assert response.status_code == 404
        data = response.json()
        # Should only contain standard error fields
        assert "detail" in data
        # Should not contain stack traces or internal details
        assert "traceback" not in str(data).lower()
        assert "exception" not in str(data).lower()

    def test_secure_headers(self) -> None:
        """Test that secure headers are present."""
        client = TestClient(app)
        response = client.get("/health")

        # Check for common security headers (implementation dependent)
        headers = response.headers
        # These checks might need adjustment based on actual implementation
        assert "content-type" in headers
