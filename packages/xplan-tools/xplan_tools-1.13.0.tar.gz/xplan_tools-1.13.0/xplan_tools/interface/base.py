from typing import Protocol

from xplan_tools.model.base import BaseCollection, BaseFeature


class BaseRepository(Protocol):
    """Abstract base class for specific repositories, which re-implement supported methods for a given data source."""

    def __init__(self, datasource: str, version: str | None = None):
        """Initialize the Repository.

        Args:
            datasource: Generally a file path or URL. May also accept file-like objects.
        """
        self.datasource = datasource

    def get(self, obj_id: str) -> BaseFeature:
        """Get a specific BaseFeature by id."""
        raise NotImplementedError("get not implemented")

    def get_all(self) -> BaseCollection:
        """Get all BaseFeatures."""
        raise NotImplementedError("get_all not implemented")

    def get_plan_by_id(self, plan_id: str) -> BaseCollection:
        """Get a plan object with its related features."""
        raise NotImplementedError("get_plan_by_id not implemented")

    def delete_plan_by_id(self, plan_id: str) -> None:
        """Delete a plan object with its related features."""
        raise NotImplementedError("delete_plan_by_id not implemented")

    def save(self, obj: BaseFeature) -> None:
        """Store a BaseFeature."""
        raise NotImplementedError("save not implemented")

    def save_all(self, features: BaseCollection) -> None:
        """Store a BaseFeature."""
        raise NotImplementedError("save_all not implemented")

    def update(self, obj_id: str, new_obj: BaseFeature) -> BaseFeature:
        """Update a BaseFeature."""
        raise NotImplementedError("update not implemented")

    def patch(self, obj_id: str, partial_obj: dict) -> BaseFeature:
        """Partially update a BaseFeature."""
        raise NotImplementedError("patch not implemented")

    def delete(self, obj_id: str) -> BaseFeature:
        """Delete a BaseFeature."""
        raise NotImplementedError("delete not implemented")
