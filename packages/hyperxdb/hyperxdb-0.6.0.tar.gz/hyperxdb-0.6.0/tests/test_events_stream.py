"""Tests for Events Streaming API."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pytest_httpx import HTTPXMock

from hyperx import AsyncHyperX, HyperX
from hyperx.events import Event


class TestEventsAPI:
    """Tests for synchronous EventsAPI."""

    def test_stream_basic(self, client: HyperX):
        """Test basic event streaming via SSE."""
        # Create mock response with SSE data
        sse_data = [
            'data: {"type": "entity.created", "data": {"id": "e:123", "name": "Test"}, "timestamp": "2026-01-17T00:00:00Z", "metadata": {}}',
            'data: {"type": "entity.updated", "data": {"id": "e:123", "name": "Updated"}, "timestamp": "2026-01-17T00:01:00Z", "metadata": {"source": "api"}}',
        ]

        # Mock the httpx stream context manager
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        with patch.object(client._http._client, "stream", return_value=mock_stream):
            events = list(client.events.stream())

        assert len(events) == 2
        assert events[0].type == "entity.created"
        assert events[0].data["id"] == "e:123"
        assert events[0].data["name"] == "Test"
        assert events[0].metadata == {}

        assert events[1].type == "entity.updated"
        assert events[1].data["name"] == "Updated"
        assert events[1].metadata["source"] == "api"

    def test_stream_with_event_type_filter(self, client: HyperX):
        """Test event streaming with event type filter."""
        sse_data = [
            'data: {"type": "entity.created", "data": {"id": "e:456"}, "timestamp": "2026-01-17T00:00:00Z", "metadata": {}}',
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        with patch.object(client._http._client, "stream", return_value=mock_stream) as mock:
            list(client.events.stream(["entity.*"]))

            # Verify filter was passed
            mock.assert_called_once()
            call_kwargs = mock.call_args
            assert "params" in call_kwargs.kwargs
            assert call_kwargs.kwargs["params"]["types"] == "entity.*"

    def test_stream_with_since_parameter(self, client: HyperX):
        """Test event streaming with since timestamp for replay."""
        sse_data = []

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        since_time = datetime(2026, 1, 16, 12, 0, 0, tzinfo=timezone.utc)

        with patch.object(client._http._client, "stream", return_value=mock_stream) as mock:
            list(client.events.stream(since=since_time))

            # Verify since was passed
            mock.assert_called_once()
            call_kwargs = mock.call_args
            assert "params" in call_kwargs.kwargs
            assert "since" in call_kwargs.kwargs["params"]

    def test_stream_ignores_non_data_lines(self, client: HyperX):
        """Test that stream ignores SSE comments and empty lines."""
        sse_data = [
            ": this is a comment",
            "",
            "event: message",
            'data: {"type": "entity.created", "data": {"id": "e:789"}, "timestamp": "2026-01-17T00:00:00Z", "metadata": {}}',
            "id: 12345",
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        with patch.object(client._http._client, "stream", return_value=mock_stream):
            events = list(client.events.stream())

        # Only the data line should produce an event
        assert len(events) == 1
        assert events[0].type == "entity.created"

    def test_stream_with_multiple_event_types(self, client: HyperX):
        """Test streaming with multiple event type filters."""
        sse_data = []

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        with patch.object(client._http._client, "stream", return_value=mock_stream) as mock:
            list(client.events.stream(["entity.created", "hyperedge.created"]))

            mock.assert_called_once()
            call_kwargs = mock.call_args
            assert call_kwargs.kwargs["params"]["types"] == "entity.created,hyperedge.created"

    def test_history_basic(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test retrieving historical events."""
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:8080/v1/events?limit=100",
            json=[
                {
                    "type": "entity.created",
                    "data": {"id": "e:123", "name": "Test"},
                    "timestamp": "2026-01-17T00:00:00Z",
                    "metadata": {},
                },
                {
                    "type": "hyperedge.created",
                    "data": {"id": "he:456"},
                    "timestamp": "2026-01-17T00:01:00Z",
                    "metadata": {"source": "api"},
                },
            ],
        )

        events = client.events.history()

        assert len(events) == 2
        assert events[0].type == "entity.created"
        assert events[0].data["id"] == "e:123"
        assert events[1].type == "hyperedge.created"
        assert events[1].metadata["source"] == "api"

    def test_history_with_filters(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test history with event type filter and time range."""
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:8080/v1/events?limit=50&types=entity.%2A&since=2026-01-16T00%3A00%3A00%2B00%3A00&until=2026-01-17T00%3A00%3A00%2B00%3A00",
            json=[],
        )

        since = datetime(2026, 1, 16, 0, 0, 0, tzinfo=timezone.utc)
        until = datetime(2026, 1, 17, 0, 0, 0, tzinfo=timezone.utc)

        events = client.events.history(
            event_types=["entity.*"],
            since=since,
            until=until,
            limit=50,
        )

        assert events == []

    def test_history_with_limit(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test history with custom limit."""
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:8080/v1/events?limit=10",
            json=[],
        )

        events = client.events.history(limit=10)

        assert events == []


class TestAsyncEventsAPI:
    """Tests for async EventsAPI."""

    @pytest.fixture
    def async_client(self):
        """Create an async client for testing."""
        client = AsyncHyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080")
        yield client

    @pytest.mark.asyncio
    async def test_async_stream_basic(self, async_client: AsyncHyperX):
        """Test async event streaming."""
        sse_data = [
            'data: {"type": "entity.created", "data": {"id": "e:123"}, "timestamp": "2026-01-17T00:00:00Z", "metadata": {}}',
            'data: {"type": "entity.updated", "data": {"id": "e:123"}, "timestamp": "2026-01-17T00:01:00Z", "metadata": {}}',
        ]

        # Create an async iterator from the data
        async def async_iter_lines():
            for line in sse_data:
                yield line

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = async_iter_lines

        # Create a proper async context manager mock
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_response

            async def __aexit__(self, *args):
                return False

        mock_stream = MockAsyncContextManager()

        with patch.object(async_client._http._client, "stream", return_value=mock_stream):
            events = []
            async for event in async_client.events.stream():
                events.append(event)

        assert len(events) == 2
        assert events[0].type == "entity.created"
        assert events[1].type == "entity.updated"

    @pytest.mark.asyncio
    async def test_async_stream_with_filter(self, async_client: AsyncHyperX):
        """Test async streaming with event type filter."""
        sse_data = []

        async def async_iter_lines():
            for line in sse_data:
                yield line

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = async_iter_lines

        # Create a proper async context manager mock
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_response

            async def __aexit__(self, *args):
                return False

        mock_stream = MockAsyncContextManager()

        with patch.object(async_client._http._client, "stream", return_value=mock_stream) as mock:
            events = []
            async for event in async_client.events.stream(["entity.*", "hyperedge.*"]):
                events.append(event)

            mock.assert_called_once()
            call_kwargs = mock.call_args
            assert call_kwargs.kwargs["params"]["types"] == "entity.*,hyperedge.*"

    @pytest.mark.asyncio
    async def test_async_history(self, async_client: AsyncHyperX, httpx_mock: HTTPXMock):
        """Test async history retrieval."""
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:8080/v1/events?limit=100",
            json=[
                {
                    "type": "entity.created",
                    "data": {"id": "e:abc"},
                    "timestamp": "2026-01-17T00:00:00Z",
                    "metadata": {},
                },
            ],
        )

        events = await async_client.events.history()

        assert len(events) == 1
        assert events[0].type == "entity.created"
        assert events[0].data["id"] == "e:abc"


class TestEventParsing:
    """Tests for event parsing from SSE data."""

    def test_event_timestamp_parsing(self, client: HyperX):
        """Test that timestamps are correctly parsed."""
        sse_data = [
            'data: {"type": "entity.created", "data": {}, "timestamp": "2026-01-17T12:30:45Z", "metadata": {}}',
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        with patch.object(client._http._client, "stream", return_value=mock_stream):
            events = list(client.events.stream())

        assert len(events) == 1
        assert events[0].timestamp.hour == 12
        assert events[0].timestamp.minute == 30
        assert events[0].timestamp.second == 45

    def test_event_missing_metadata_defaults_to_empty(self, client: HyperX):
        """Test that missing metadata defaults to empty dict."""
        sse_data = [
            'data: {"type": "entity.created", "data": {"id": "e:test"}, "timestamp": "2026-01-17T00:00:00Z"}',
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=iter(sse_data))

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        with patch.object(client._http._client, "stream", return_value=mock_stream):
            events = list(client.events.stream())

        assert len(events) == 1
        assert events[0].metadata == {}
