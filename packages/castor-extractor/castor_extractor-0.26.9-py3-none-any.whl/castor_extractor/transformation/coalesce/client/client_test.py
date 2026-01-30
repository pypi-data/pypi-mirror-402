from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

import pytest
from requests.exceptions import ReadTimeout

from .client import COALESCE_MIN_PAGE_SIZE, COALESCE_PAGE_SIZE, CoalesceClient
from .credentials import CoalesceCredentials
from .endpoint import CoalesceEndpointFactory


@dataclass
class _StubResponse:
    payload: dict[str, Any]

    def json(self) -> dict[str, Any]:
        return self.payload


def _make_client() -> CoalesceClient:
    # Minimal real client instance; we'll patch _call so no network happens.
    creds = CoalesceCredentials(
        host="https://example.invalid", token="fake-token"
    )
    return CoalesceClient(credentials=creds)


def _node(i: int) -> dict[str, Any]:
    return {"id": f"{i:03d}", "name": f"n{i}"}


def test_fetch_env_nodes_paginates_until_next_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Ensures _fetch_env_nodes() keeps fetching pages using the 'next' cursor and
    stops when next is None.
    """
    client = _make_client()
    env_id = 17
    expected_endpoint = CoalesceEndpointFactory.nodes(environment_id=env_id)

    # Simulate 3 pages: 200 + 200 + 305 = 705
    pages: dict[str | None, _StubResponse] = {
        None: _StubResponse(
            {
                "data": [_node(i) for i in range(200)],
                "limit": 200,
                "next": "c1",
                "total": 200,
            }
        ),
        "c1": _StubResponse(
            {
                "data": [_node(i) for i in range(200, 400)],
                "limit": 200,
                "next": "c2",
                "total": 200,
            }
        ),
        "c2": _StubResponse(
            {
                "data": [_node(i) for i in range(400, 705)],
                "limit": 200,
                "next": None,
                "total": 305,
            }
        ),
    }

    def _call_stub(
        *, method: str, endpoint: str, params: dict, retry_on_timeout: bool
    ) -> _StubResponse:
        assert method == "GET"
        assert endpoint == expected_endpoint
        cursor = params.get("startingFrom")
        return pages[cursor]

    call_mock = Mock(side_effect=_call_stub)
    monkeypatch.setattr(client, "_call", call_mock)

    nodes = client._fetch_env_nodes(env_id)

    assert len(nodes) == 705
    assert all(n["environment_id"] == env_id for n in nodes)
    assert call_mock.call_count == 3


def test_fetch_env_nodes_reduces_page_size_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    If a timeout happens, smart pagination should reduce page_size and retry the SAME cursor.
    """
    client = _make_client()
    env_id = 17

    calls: list[dict[str, Any]] = []

    def _call_stub(
        *,
        method: str,
        endpoint: str,
        params: dict,
        retry_on_timeout: bool,
    ) -> _StubResponse:
        calls.append(params)

        # First attempt fails at default page size.
        if len(calls) == 1:
            assert params.get("limit") == COALESCE_PAGE_SIZE
            raise ReadTimeout("boom")

        # Second attempt should be a retry with a reduced page size (still first page cursor).
        limit = params.get("limit")
        assert isinstance(limit, int)
        assert limit < COALESCE_PAGE_SIZE
        assert (
            params.get("startingFrom") is None or "startingFrom" not in params
        )

        # Return a single page and finish.
        return _StubResponse(
            {
                "data": [_node(0)],
                "limit": params["limit"],
                "next": None,
                "total": 1,
            }
        )

    call_mock = Mock(side_effect=_call_stub)
    monkeypatch.setattr(client, "_call", call_mock)

    # Avoid sleeping in tests
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    nodes = client._fetch_env_nodes(env_id)

    assert len(nodes) == 1
    assert call_mock.call_count == 2


def test_fetch_env_nodes_raises_when_page_size_is_1_and_still_timeouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Coalesce cursor pagination can't skip assets. When page_size is reduced to 1 and it still fails,
    we must raise.
    """
    client = _make_client()
    env_id = 17

    def _call_stub(
        *,
        method: str,
        endpoint: str,
        params: dict,
        retry_on_timeout: bool,
    ) -> _StubResponse:
        raise ReadTimeout("still failing")

    call_mock = Mock(side_effect=_call_stub)
    monkeypatch.setattr(client, "_call", call_mock)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    # Force starting page_size to MIN so it raises immediately on first error at page_size=1.
    monkeypatch.setattr(
        "castor_extractor.transformation.coalesce.client.client.COALESCE_PAGE_SIZE",
        COALESCE_MIN_PAGE_SIZE,
    )

    with pytest.raises(ReadTimeout):
        client._fetch_env_nodes(env_id)
