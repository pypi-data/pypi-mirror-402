"""Tests for paths API - the hero feature."""

from pytest_httpx import HTTPXMock

from hyperx import HyperX


def test_find_paths(client: HyperX, httpx_mock: HTTPXMock):
    """Test finding paths between entities."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/paths",
        json={
            "paths": [
                {
                    "hyperedges": ["h:edge1", "h:edge2"],
                    "bridges": [["e:bridge1"]],
                    "cost": 0.5,
                },
                {
                    "hyperedges": ["h:edge3", "h:edge4", "h:edge5"],
                    "bridges": [["e:bridge2"], ["e:bridge3"]],
                    "cost": 0.8,
                },
            ]
        },
    )

    paths = client.paths.find(
        from_entity="e:useState",
        to_entity="e:redux",
        max_hops=4,
    )

    assert len(paths) == 2
    assert paths[0].cost == 0.5
    assert len(paths[0].hyperedges) == 2
    assert len(paths[1].hyperedges) == 3


def test_find_paths_with_constraints(client: HyperX, httpx_mock: HTTPXMock):
    """Test path finding with custom constraints."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/paths",
        json={
            "paths": [
                {
                    "hyperedges": ["h:edge1"],
                    "bridges": [],
                    "cost": 0.2,
                },
            ]
        },
    )

    paths = client.paths.find(
        from_entity="e:source",
        to_entity="e:target",
        max_hops=2,
        intersection_size=2,
        k_paths=5,
    )

    assert len(paths) == 1
    assert paths[0].cost == 0.2


def test_find_paths_empty_result(client: HyperX, httpx_mock: HTTPXMock):
    """Test path finding when no paths exist."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/paths",
        json={"paths": []},
    )

    paths = client.paths.find(
        from_entity="e:isolated1",
        to_entity="e:isolated2",
    )

    assert len(paths) == 0


def test_path_result_structure(client: HyperX, httpx_mock: HTTPXMock):
    """Test that PathResult has correct structure."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/paths",
        json={
            "paths": [
                {
                    "hyperedges": ["h:e1", "h:e2", "h:e3"],
                    "bridges": [["e:b1", "e:b2"], ["e:b3"]],
                    "cost": 1.5,
                },
            ]
        },
    )

    paths = client.paths.find(from_entity="e:a", to_entity="e:b")

    path = paths[0]
    assert path.hyperedges == ["h:e1", "h:e2", "h:e3"]
    assert path.bridges == [["e:b1", "e:b2"], ["e:b3"]]
    assert path.cost == 1.5
