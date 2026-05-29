"""
Tests for the Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) pattern throughout.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activity participants to a known state before each test."""
    original = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_all_activities(self, client):
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_activity_has_required_fields(self, client):
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity in data.values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        # Arrange
        activity_name = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 404

    def test_duplicate_signup_returns_409(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # already a participant

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 409

    def test_signup_normalises_email(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "  NewStudent@MERGINGTON.EDU  "

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in activities[activity_name]["participants"]

    def test_signup_full_activity_returns_400(self, client):
        # Arrange – fill every spot in a small activity
        activity_name = "Chess Club"
        max_p = activities[activity_name]["max_participants"]
        for i in range(max_p):
            activities[activity_name]["participants"] = [f"filler{i}@mergington.edu" for i in range(max_p)]

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email=latecoming@mergington.edu")

        # Assert
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # existing participant

        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]

    def test_unregister_unknown_activity_returns_404(self, client):
        # Arrange
        activity_name = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 404

    def test_unregister_non_participant_returns_404(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 404

    def test_unregister_then_signup_again(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act – unregister then sign back up
        client.delete(f"/activities/{activity_name}/signup?email={email}")
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
