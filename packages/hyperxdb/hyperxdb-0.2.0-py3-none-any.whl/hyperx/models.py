"""Data models for HyperX SDK."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """A node in the hypergraph."""

    id: str
    name: str
    entity_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class HyperedgeMember(BaseModel):
    """A member of a hyperedge."""

    entity_id: str
    role: str


class Hyperedge(BaseModel):
    """An n-ary relationship connecting multiple entities."""

    id: str
    description: str
    members: list[HyperedgeMember]
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime


class SearchResult(BaseModel):
    """Results from a search query."""

    entities: list[Entity]
    hyperedges: list[Hyperedge]


class PathResult(BaseModel):
    """A path between two entities."""

    hyperedges: list[str]
    bridges: list[list[str]]
    cost: float


class PathsResponse(BaseModel):
    """Response from paths.find()."""

    paths: list[PathResult]
