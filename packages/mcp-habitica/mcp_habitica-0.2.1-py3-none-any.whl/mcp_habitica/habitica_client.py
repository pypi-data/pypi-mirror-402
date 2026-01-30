"""Habitica API client for task and tag operations."""

import httpx
from typing import Any, Dict, List, Optional


class HabiticaClient:
    """Client for interacting with the Habitica API.

    Provides methods for task and tag management operations.
    API Documentation: https://habitica.com/apidoc/
    """

    BASE_URL = "https://habitica.com/api/v3"

    def __init__(self, user_id: str, api_token: str):
        """Initialize the Habitica client.

        Args:
            user_id: Your Habitica user ID (found in Settings > Site Data)
            api_token: Your Habitica API token (found in Settings > Site Data)
        """
        self.user_id = user_id
        self.api_token = api_token
        self.client = httpx.AsyncClient(timeout=30.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get required authentication headers for API requests."""
        return {
            "x-api-user": self.user_id,
            "x-api-key": self.api_token,
            "Content-Type": "application/json",
        }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    # Task Operations

    async def get_tasks(self, task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks for the user.

        Args:
            task_type: Optional filter by type (habits, dailys, todos, rewards)

        Returns:
            List of task objects
        """
        url = f"{self.BASE_URL}/tasks/user"
        params = {"type": task_type} if task_type else {}

        response = await self.client.get(
            url,
            headers=self._get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get a specific task by ID.

        Args:
            task_id: The task ID

        Returns:
            Task object
        """
        url = f"{self.BASE_URL}/tasks/{task_id}"

        response = await self.client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()["data"]

    async def create_task(
        self,
        text: str,
        task_type: str = "todo",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new task.

        Args:
            text: Task title/description
            task_type: Type of task (habit, daily, todo, reward)
            notes: Additional notes
            tags: List of tag IDs to apply
            priority: Task priority (0.1=trivial, 1=easy, 1.5=medium, 2=hard)
            **kwargs: Additional task properties

        Returns:
            Created task object
        """
        url = f"{self.BASE_URL}/tasks/user"

        data = {
            "text": text,
            "type": task_type,
            "priority": priority,
            **kwargs
        }

        if notes:
            data["notes"] = notes
        if tags:
            data["tags"] = tags

        response = await self.client.post(
            url,
            headers=self._get_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()["data"]

    async def update_task(
        self,
        task_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update an existing task.

        Args:
            task_id: The task ID
            **updates: Fields to update (text, notes, priority, etc.)

        Returns:
            Updated task object
        """
        url = f"{self.BASE_URL}/tasks/{task_id}"

        response = await self.client.put(
            url,
            headers=self._get_headers(),
            json=updates
        )
        response.raise_for_status()
        return response.json()["data"]

    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task.

        Args:
            task_id: The task ID

        Returns:
            Deletion response
        """
        url = f"{self.BASE_URL}/tasks/{task_id}"

        response = await self.client.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()["data"]

    async def score_task(self, task_id: str, direction: str) -> Dict[str, Any]:
        """Score a task (mark complete or fail).

        Args:
            task_id: The task ID
            direction: 'up' for complete/success, 'down' for fail

        Returns:
            Updated task and user stats
        """
        url = f"{self.BASE_URL}/tasks/{task_id}/score/{direction}"

        response = await self.client.post(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()["data"]

    # Tag Operations

    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags for the user.

        Returns:
            List of tag objects
        """
        url = f"{self.BASE_URL}/tags"

        response = await self.client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()["data"]

    async def get_tag(self, tag_id: str) -> Dict[str, Any]:
        """Get a specific tag by ID.

        Args:
            tag_id: The tag ID

        Returns:
            Tag object
        """
        url = f"{self.BASE_URL}/tags/{tag_id}"

        response = await self.client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()["data"]

    async def create_tag(self, name: str) -> Dict[str, Any]:
        """Create a new tag.

        Args:
            name: Tag name

        Returns:
            Created tag object
        """
        url = f"{self.BASE_URL}/tags"

        response = await self.client.post(
            url,
            headers=self._get_headers(),
            json={"name": name}
        )
        response.raise_for_status()
        return response.json()["data"]

    async def update_tag(self, tag_id: str, name: str) -> Dict[str, Any]:
        """Update an existing tag.

        Args:
            tag_id: The tag ID
            name: New tag name

        Returns:
            Updated tag object
        """
        url = f"{self.BASE_URL}/tags/{tag_id}"

        response = await self.client.put(
            url,
            headers=self._get_headers(),
            json={"name": name}
        )
        response.raise_for_status()
        return response.json()["data"]

    async def delete_tag(self, tag_id: str) -> Dict[str, Any]:
        """Delete a tag.

        Args:
            tag_id: The tag ID

        Returns:
            Deletion response
        """
        url = f"{self.BASE_URL}/tags/{tag_id}"

        response = await self.client.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()["data"]
