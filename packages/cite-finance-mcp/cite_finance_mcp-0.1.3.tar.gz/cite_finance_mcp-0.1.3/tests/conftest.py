"""
Pytest configuration for Cite-Finance API tests
"""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Add fixtures for test database setup/teardown here when needed
# Example:
#
# @pytest.fixture
# async def test_db():
#     """Setup test database"""
#     # Create test database
#     # Run migrations
#     yield db_connection
#     # Cleanup
