import pytest
from scheduler_service.models import ApiKey
from tests import const


@pytest.mark.asyncio
class TestApiKey:
    """Test API Key functionality"""

    async def test_create_api_key(self, client, headers, user):
        """Test creating an API key"""
        resp = await client.post(
            f"/api/v1/apikeys",
            headers=headers,
            json={"name": "Test Key"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "key" in data
        assert data["name"] == "Test Key"
        assert data["prefix"] == data["key"][:8]

        # Verify in DB
        key_obj = await ApiKey.get(id=data["id"])
        assert key_obj.name == "Test Key"
        assert key_obj.verify_key(data["key"])

    async def test_list_api_keys(self, client, headers, user):
        """Test listing API keys"""
        # Create a key first
        await client.post(
            f"/api/v1/apikeys",
            headers=headers,
            json={"name": "List Test Key"}
        )

        resp = await client.get(f"/api/v1/apikeys", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "List Test Key"
        assert "key" not in data[0]  # Raw key should not be listed

    async def test_revoke_api_key(self, client, headers, user):
        """Test revoking an API key"""
        # Create a key
        create_resp = await client.post(
            f"/api/v1/apikeys",
            headers=headers,
            json={"name": "Revoke Test Key"}
        )
        key_id = create_resp.json()["id"]

        # Revoke it
        resp = await client.delete(f"/api/v1/apikeys/{key_id}", headers=headers)
        assert resp.status_code == 200

        # Verify it's inactive
        key_obj = await ApiKey.get(id=key_id)
        assert not key_obj.is_active

        # Verify list doesn't show it (endpoint filters is_active=True)
        list_resp = await client.get(f"/api/v1/apikeys", headers=headers)
        active_ids = [k["id"] for k in list_resp.json()]
        assert key_id not in active_ids

    async def test_auth_with_api_key(self, client, headers, user):
        """Test authentication using API Key"""
        # Generate a key
        create_resp = await client.post(
            f"/api/v1/apikeys",
            headers=headers,
            json={"name": "Auth Test Key"}
        )
        api_key = create_resp.json()["key"]

        # Use key to access a protected endpoint (e.g. get current user info)
        # Note: We use X-API-KEY header instead of Authorization
        resp = await client.get(
            const.USER_ME_URL,
            headers={"X-API-KEY": api_key}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user.id
        assert data["name"] == user.name

    async def test_auth_with_invalid_api_key(self, client):
        """Test authentication with invalid API Key"""
        resp = await client.get(
            const.USER_ME_URL,
            headers={"X-API-KEY": "invalid_key_12345678"}
        )
        assert resp.status_code == 401

    async def test_auth_with_revoked_api_key(self, client, headers):
        """Test authentication with revoked API Key"""
        # Generate a key
        create_resp = await client.post(
            f"/api/v1/apikeys",
            headers=headers,
            json={"name": "Revoked Auth Key"}
        )
        api_key = create_resp.json()["key"]
        key_id = create_resp.json()["id"]

        # Revoke it
        await client.delete(f"/api/v1/apikeys/{key_id}", headers=headers)

        # Try to use it
        resp = await client.get(
            const.USER_ME_URL,
            headers={"X-API-KEY": api_key}
        )
        assert resp.status_code == 401
