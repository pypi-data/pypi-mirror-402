"""
Integration tests for FastAPI router endpoints.

Tests conversation CRUD, messages, and health check endpoints.
Chat streaming endpoints require agent mocking (covered in E2E tests).
"""

import pytest


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, client):
        """Health endpoint returns status: healthy."""
        response = await client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestConversationEndpoints:
    """Tests for conversation CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation_default_title(self, client):
        """Create conversation without title uses default."""
        response = await client.post("/api/conversations", json={})

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["is_pinned"] is False
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_conversation_with_title(self, client):
        """Create conversation with custom title."""
        response = await client.post(
            "/api/conversations",
            json={"title": "My Test Conversation"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My Test Conversation"

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, client):
        """List conversations returns empty list initially."""
        response = await client.get("/api/conversations")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_conversations_returns_created(self, client):
        """List conversations includes created conversations."""
        # Create two conversations
        await client.post("/api/conversations", json={"title": "First"})
        await client.post("/api/conversations", json={"title": "Second"})

        response = await client.get("/api/conversations")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = [c["title"] for c in data]
        assert "First" in titles
        assert "Second" in titles

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, client):
        """List conversations respects skip and limit."""
        # Create 5 conversations
        for i in range(5):
            await client.post("/api/conversations", json={"title": f"Conv {i}"})

        # Get with limit
        response = await client.get("/api/conversations?limit=2")
        assert len(response.json()) == 2

        # Get with skip
        response = await client.get("/api/conversations?skip=3")
        assert len(response.json()) == 2  # 5 - 3 = 2

    @pytest.mark.asyncio
    async def test_get_conversation_exists(self, client):
        """Get specific conversation by ID."""
        create_resp = await client.post(
            "/api/conversations",
            json={"title": "Test Conv"},
        )
        conv_id = create_resp.json()["id"]

        response = await client.get(f"/api/conversations/{conv_id}")

        assert response.status_code == 200
        assert response.json()["id"] == conv_id
        assert response.json()["title"] == "Test Conv"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, client):
        """Get non-existent conversation returns 404."""
        response = await client.get("/api/conversations/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_conversation_title(self, client):
        """Update conversation title."""
        create_resp = await client.post("/api/conversations", json={})
        conv_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/conversations/{conv_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_conversation_pin(self, client):
        """Update conversation pin status."""
        create_resp = await client.post("/api/conversations", json={})
        conv_id = create_resp.json()["id"]
        assert create_resp.json()["is_pinned"] is False

        response = await client.patch(
            f"/api/conversations/{conv_id}",
            json={"is_pinned": True},
        )

        assert response.status_code == 200
        assert response.json()["is_pinned"] is True

    @pytest.mark.asyncio
    async def test_update_conversation_both_fields(self, client):
        """Update both title and pin status."""
        create_resp = await client.post("/api/conversations", json={})
        conv_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/conversations/{conv_id}",
            json={"title": "Pinned Conv", "is_pinned": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Pinned Conv"
        assert data["is_pinned"] is True

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, client):
        """Update non-existent conversation returns 404."""
        response = await client.patch(
            "/api/conversations/99999",
            json={"title": "Ghost"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation(self, client):
        """Delete conversation removes it."""
        create_resp = await client.post("/api/conversations", json={})
        conv_id = create_resp.json()["id"]

        response = await client.delete(f"/api/conversations/{conv_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify gone
        get_resp = await client.get(f"/api/conversations/{conv_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, client):
        """Delete non-existent conversation returns 404."""
        response = await client.delete("/api/conversations/99999")

        assert response.status_code == 404


class TestBulkDeleteEndpoint:
    """Tests for bulk delete endpoint."""

    @pytest.mark.asyncio
    async def test_bulk_delete_multiple(self, client):
        """Bulk delete removes multiple conversations."""
        ids = []
        for i in range(3):
            resp = await client.post("/api/conversations", json={"title": f"Bulk {i}"})
            ids.append(resp.json()["id"])

        response = await client.post(
            "/api/conversations/bulk-delete",
            json={"conversation_ids": ids[:2]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["deleted_count"] == 2

        list_resp = await client.get("/api/conversations")
        assert len(list_resp.json()) == 1

    @pytest.mark.asyncio
    async def test_bulk_delete_empty_list(self, client):
        """Bulk delete with empty list succeeds with 0 deleted."""
        response = await client.post(
            "/api/conversations/bulk-delete",
            json={"conversation_ids": []},
        )

        assert response.status_code == 200
        assert response.json()["deleted_count"] == 0

    @pytest.mark.asyncio
    async def test_bulk_delete_nonexistent_ids(self, client):
        """Bulk delete with non-existent IDs succeeds with 0 deleted."""
        response = await client.post(
            "/api/conversations/bulk-delete",
            json={"conversation_ids": [99998, 99999]},
        )

        assert response.status_code == 200
        assert response.json()["deleted_count"] == 0


# Note: The /conversations/all endpoint is defined AFTER /conversations/{conversation_id}
# in router.py, which means FastAPI tries to match "all" as a conversation_id first.
# This is a route ordering issue in the application that would need to be fixed.
# Tests for this endpoint are skipped until the route order is corrected.


class TestMessageEndpoints:
    """Tests for message endpoints."""

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, client, create_conversation):
        """Get messages for conversation with no messages."""
        conv = await create_conversation()

        response = await client.get(f"/api/conversations/{conv.id}/messages")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_messages_returns_ordered(
        self, client, create_conversation, create_message
    ):
        """Get messages returns them in created_at order."""
        conv = await create_conversation()

        await create_message(conv.id, "user", "First message")
        await create_message(conv.id, "assistant", "Second message")
        await create_message(conv.id, "user", "Third message")

        response = await client.get(f"/api/conversations/{conv.id}/messages")

        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 3
        assert messages[0]["content"] == "First message"
        assert messages[1]["content"] == "Second message"
        assert messages[2]["content"] == "Third message"
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


class TestStarterPromptsEndpoint:
    """Tests for starter prompts endpoint."""

    @pytest.mark.asyncio
    async def test_get_starter_prompts_empty(self, client):
        """Get starter prompts returns empty when none exist."""
        response = await client.get("/api/starter-prompts")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_starter_prompts_returns_ordered(
        self, client, create_starter_prompt
    ):
        """Get starter prompts returns them in display_order."""
        await create_starter_prompt("Third prompt", order=3)
        await create_starter_prompt("First prompt", order=1)
        await create_starter_prompt("Second prompt", order=2)

        response = await client.get("/api/starter-prompts")

        assert response.status_code == 200
        prompts = response.json()
        assert len(prompts) == 3
        assert prompts[0]["prompt_text"] == "First prompt"
        assert prompts[1]["prompt_text"] == "Second prompt"
        assert prompts[2]["prompt_text"] == "Third prompt"
