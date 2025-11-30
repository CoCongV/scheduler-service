import pytest
import time
from scheduler_service.models import RequestTask
from scheduler_service.constants import TaskStatus
from tests import const


@pytest.mark.asyncio
class TestStatsAPI:
    """Test dashboard stats API"""

    async def test_get_dashboard_stats(self, client, headers, user):
        """Test getting dashboard statistics"""
        # Create tasks with different statuses
        # 1. Pending task
        await RequestTask.create(
            name="pending_task",
            start_time=int(time.time()) + 3600,
            user_id=user.id,
            request_url="http://example.com",
            status=TaskStatus.PENDING
        )

        # 2. Completed task
        await RequestTask.create(
            name="completed_task",
            start_time=int(time.time()),
            user_id=user.id,
            request_url="http://example.com",
            status=TaskStatus.COMPLETED
        )

        # 3. Failed task
        await RequestTask.create(
            name="failed_task",
            start_time=int(time.time()),
            user_id=user.id,
            request_url="http://example.com",
            status=TaskStatus.FAILED
        )

        resp = await client.get(f"{const.STATS_URL}/dashboard", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_tasks"] == 3
        assert data["status_counts"][TaskStatus.PENDING] == 1
        assert data["status_counts"][TaskStatus.COMPLETED] == 1
        assert data["status_counts"][TaskStatus.FAILED] == 1
        # Ensure other statuses are not present if count is 0
        assert TaskStatus.RUNNING not in data["status_counts"]

    async def test_get_dashboard_stats_empty(self, client, headers, user):
        """Test getting dashboard statistics with no tasks"""
        resp = await client.get(f"{const.STATS_URL}/dashboard", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_tasks"] == 0
        assert data["status_counts"] == {}

    async def test_unauthorized_access(self, client):
        """Test unauthorized access"""
        resp = await client.get(f"{const.STATS_URL}/dashboard")
        assert resp.status_code == 401
