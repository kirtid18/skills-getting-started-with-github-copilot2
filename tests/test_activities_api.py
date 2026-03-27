"""Integration tests for the High School Management System API endpoints."""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_has_correct_structure(self, client):
        """Test that activity objects have all required fields."""
        response = client.get("/activities")
        data = response.json()
        
        # Check Chess Club structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_initial_participants(self, client):
        """Test that activities have correct initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club and Programming Class should have existing participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Programming Class"]["participants"]) == 2
        
        # Soccer Team should have no participants initially
        assert len(data["Soccer Team"]["participants"]) == 0


class TestRootRedirect:
    """Tests for the GET / endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success_new_student(self, client):
        """Test successful signup of a new student."""
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alex@mergington.edu" in data["message"]
        assert "Soccer Team" in data["message"]
    
    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds the student to the activity."""
        # Sign up a student
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": "new_student@mergington.edu"}
        )
        
        # Verify student is now in participants
        response = client.get("/activities")
        data = response.json()
        assert "new_student@mergington.edu" in data["Tennis Club"]["participants"]
    
    def test_signup_duplicate_student_fails(self, client):
        """Test that signing up a student twice raises an error."""
        email = "michael@mergington.edu"
        
        # Attempt to sign up a student who's already registered
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()
    
    def test_signup_invalid_activity(self, client):
        """Test that signup fails when activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.parametrize("email", [
        "alice@mergington.edu",
        "bob@mergington.edu",
        "charlie@mergington.edu"
    ])
    def test_signup_multiple_students(self, client, email):
        """Test signing up multiple different students to the same activity."""
        response = client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify all students are added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Drama Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client):
        """Test successful unregistration of a registered student."""
        email = "michael@mergington.edu"
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_removes_student_from_participants(self, client):
        """Test that unregister actually removes the student from the activity."""
        email = "michael@mergington.edu"
        
        # Unregister the student
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Verify student is no longer in participants
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_unregister_not_registered_student_fails(self, client):
        """Test that unregistering a non-registered student fails."""
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": "not_registered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_invalid_activity(self, client):
        """Test that unregister fails when activity doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can sign up again after unregistering."""
        email = "test_student@mergington.edu"
        activity = "Art Club"
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up again
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify signed up again
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple endpoints."""
    
    def test_complete_signup_workflow(self, client):
        """Test a complete workflow: view activities, sign up, verify, unregister."""
        email = "workflow_test@mergington.edu"
        activity = "Debate Club"
        
        # View activities
        response = client.get("/activities")
        assert response.status_code == 200
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up for activity
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify unregistration
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        assert len(response.json()[activity]["participants"]) == initial_count
    
    def test_multiple_activities_signup(self, client):
        """Test signing up the same student to multiple activities."""
        email = "multi_activity@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Science Club"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities_to_join:
            assert email in data[activity]["participants"]
