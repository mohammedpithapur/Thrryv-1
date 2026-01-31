"""
Thrryv API Backend Tests
Tests for: Authentication, Claims, Annotations, Voting, User Profile, Media Upload
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "testpassword123"
TEST_USERNAME = f"testuser_{uuid.uuid4().hex[:8]}"

# Shared state for tests
class TestState:
    token = None
    user_id = None
    claim_id = None
    annotation_id = None


class TestHealthAndBasics:
    """Basic API health checks"""
    
    def test_api_claims_endpoint_accessible(self):
        """Test that claims endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/claims")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ Claims endpoint accessible, returned {len(response.json())} claims")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_register_new_user(self):
        """Test user registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["username"] == TEST_USERNAME
        assert "reputation_score" in data["user"]
        
        # Store for later tests
        TestState.token = data["token"]
        TestState.user_id = data["user"]["id"]
        print(f"✓ User registered: {TEST_USERNAME}")
    
    def test_register_duplicate_email_fails(self):
        """Test that duplicate email registration fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": "another_user",
            "email": TEST_EMAIL,  # Same email
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✓ Duplicate email registration correctly rejected")
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        
        TestState.token = data["token"]
        print("✓ Login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == TEST_EMAIL
        assert "contribution_stats" in data
        print("✓ Current user info retrieved")


class TestClaims:
    """Claims CRUD tests"""
    
    def test_create_claim(self):
        """Test creating a new claim"""
        claim_text = f"TEST_CLAIM: The Earth is round - {uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/claims",
            json={
                "text": claim_text,
                "confidence_level": 85,
                "media_ids": []
            },
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200, f"Create claim failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert "id" in data
        assert data["text"] == claim_text
        assert "domain" in data  # AI-classified domain
        assert "truth_label" in data  # AI fact-check result
        assert "credibility_score" in data
        assert data["author"]["username"] == TEST_USERNAME
        
        TestState.claim_id = data["id"]
        print(f"✓ Claim created with ID: {TestState.claim_id}")
        print(f"  Domain: {data['domain']}, Truth Label: {data['truth_label']}")
    
    def test_get_claims_list(self):
        """Test getting list of claims"""
        response = requests.get(f"{BASE_URL}/api/claims")
        
        assert response.status_code == 200
        claims = response.json()
        
        assert isinstance(claims, list)
        
        # Find our test claim
        test_claim = next((c for c in claims if c["id"] == TestState.claim_id), None)
        assert test_claim is not None, "Created claim not found in list"
        
        # Validate claim structure
        assert "text" in test_claim
        assert "domain" in test_claim
        assert "truth_label" in test_claim
        assert "credibility_score" in test_claim
        assert "annotation_count" in test_claim
        assert "author" in test_claim
        
        print(f"✓ Claims list retrieved, found {len(claims)} claims")
    
    def test_get_single_claim(self):
        """Test getting a single claim by ID"""
        response = requests.get(f"{BASE_URL}/api/claims/{TestState.claim_id}")
        
        assert response.status_code == 200
        claim = response.json()
        
        assert claim["id"] == TestState.claim_id
        assert "text" in claim
        assert "domain" in claim
        assert "truth_label" in claim
        assert "credibility_score" in claim
        assert "author" in claim
        
        print(f"✓ Single claim retrieved: {claim['text'][:50]}...")
    
    def test_get_nonexistent_claim(self):
        """Test getting a claim that doesn't exist"""
        response = requests.get(f"{BASE_URL}/api/claims/nonexistent-id-12345")
        
        assert response.status_code == 404
        print("✓ Nonexistent claim correctly returns 404")
    
    def test_create_claim_without_auth_fails(self):
        """Test that creating claim without auth fails"""
        response = requests.post(
            f"{BASE_URL}/api/claims",
            json={
                "text": "Unauthorized claim",
                "confidence_level": 50
            }
        )
        
        assert response.status_code in [401, 403]
        print("✓ Unauthorized claim creation correctly rejected")


class TestAnnotations:
    """Annotation tests"""
    
    def test_create_support_annotation(self):
        """Test creating a support annotation"""
        response = requests.post(
            f"{BASE_URL}/api/claims/{TestState.claim_id}/annotations",
            json={
                "text": "TEST_ANNOTATION: This is supported by scientific evidence",
                "annotation_type": "support",
                "media_ids": []
            },
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200, f"Create annotation failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["annotation_type"] == "support"
        assert data["claim_id"] == TestState.claim_id
        assert data["helpful_votes"] == 0
        assert data["not_helpful_votes"] == 0
        
        TestState.annotation_id = data["id"]
        print(f"✓ Support annotation created: {TestState.annotation_id}")
    
    def test_create_contradict_annotation(self):
        """Test creating a contradict annotation"""
        response = requests.post(
            f"{BASE_URL}/api/claims/{TestState.claim_id}/annotations",
            json={
                "text": "TEST_ANNOTATION: This contradicts the claim",
                "annotation_type": "contradict",
                "media_ids": []
            },
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["annotation_type"] == "contradict"
        print("✓ Contradict annotation created")
    
    def test_create_context_annotation(self):
        """Test creating a context annotation"""
        response = requests.post(
            f"{BASE_URL}/api/claims/{TestState.claim_id}/annotations",
            json={
                "text": "TEST_ANNOTATION: Additional context for this claim",
                "annotation_type": "context",
                "media_ids": []
            },
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["annotation_type"] == "context"
        print("✓ Context annotation created")
    
    def test_get_annotations_for_claim(self):
        """Test getting annotations for a claim"""
        response = requests.get(f"{BASE_URL}/api/claims/{TestState.claim_id}/annotations")
        
        assert response.status_code == 200
        annotations = response.json()
        
        assert isinstance(annotations, list)
        assert len(annotations) >= 3  # We created 3 annotations
        
        # Validate annotation structure
        for ann in annotations:
            assert "id" in ann
            assert "text" in ann
            assert "annotation_type" in ann
            assert "author" in ann
            assert "helpful_votes" in ann
            assert "not_helpful_votes" in ann
        
        print(f"✓ Retrieved {len(annotations)} annotations for claim")
    
    def test_create_annotation_without_auth_fails(self):
        """Test that creating annotation without auth fails"""
        response = requests.post(
            f"{BASE_URL}/api/claims/{TestState.claim_id}/annotations",
            json={
                "text": "Unauthorized annotation",
                "annotation_type": "support"
            }
        )
        
        assert response.status_code in [401, 403]
        print("✓ Unauthorized annotation creation correctly rejected")


class TestVoting:
    """Voting on annotations tests"""
    
    def test_vote_helpful(self):
        """Test voting an annotation as helpful"""
        # Need a second user to vote (can't vote on own annotation in some systems)
        # For now, test the endpoint works
        response = requests.post(
            f"{BASE_URL}/api/annotations/{TestState.annotation_id}/vote",
            params={"helpful": True},
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        # Either success or "already voted" is acceptable
        assert response.status_code in [200, 400]
        print(f"✓ Vote endpoint responded with status {response.status_code}")
    
    def test_vote_without_auth_fails(self):
        """Test that voting without auth fails"""
        response = requests.post(
            f"{BASE_URL}/api/annotations/{TestState.annotation_id}/vote",
            params={"helpful": True}
        )
        
        assert response.status_code in [401, 403]
        print("✓ Unauthorized voting correctly rejected")


class TestUserProfile:
    """User profile tests"""
    
    def test_get_user_profile(self):
        """Test getting user profile"""
        response = requests.get(f"{BASE_URL}/api/users/{TestState.user_id}")
        
        assert response.status_code == 200
        user = response.json()
        
        assert user["id"] == TestState.user_id
        assert user["username"] == TEST_USERNAME
        assert "reputation_score" in user
        assert "contribution_stats" in user
        assert "recent_claims" in user
        assert "recent_annotations" in user
        
        # Verify contribution stats updated
        assert user["contribution_stats"]["claims_posted"] >= 1
        assert user["contribution_stats"]["annotations_added"] >= 3
        
        print(f"✓ User profile retrieved: {user['username']}")
        print(f"  Reputation: {user['reputation_score']}")
        print(f"  Claims: {user['contribution_stats']['claims_posted']}")
        print(f"  Annotations: {user['contribution_stats']['annotations_added']}")
    
    def test_get_nonexistent_user(self):
        """Test getting a user that doesn't exist"""
        response = requests.get(f"{BASE_URL}/api/users/nonexistent-user-id")
        
        assert response.status_code == 404
        print("✓ Nonexistent user correctly returns 404")


class TestUserSettings:
    """User settings tests"""
    
    def test_update_username(self):
        """Test updating username"""
        new_username = f"updated_{uuid.uuid4().hex[:6]}"
        
        response = requests.patch(
            f"{BASE_URL}/api/users/settings",
            params={"username": new_username},
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200
        
        # Verify update
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        assert me_response.json()["username"] == new_username
        
        print(f"✓ Username updated to: {new_username}")


class TestAIFactChecking:
    """Test AI fact-checking functionality"""
    
    def test_false_claim_detection(self):
        """Test that known false claims are detected"""
        # Create a claim that should be detected as false
        response = requests.post(
            f"{BASE_URL}/api/claims",
            json={
                "text": "The Earth is flat and not round",
                "confidence_level": 90,
                "media_ids": []
            },
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be detected as false
        assert data["truth_label"] in ["False", "Likely False"]
        print(f"✓ False claim detected: truth_label={data['truth_label']}")
    
    def test_domain_classification(self):
        """Test that claims are classified into domains"""
        # Create a science-related claim
        response = requests.post(
            f"{BASE_URL}/api/claims",
            json={
                "text": "Scientific research shows that exercise improves health",
                "confidence_level": 80,
                "media_ids": []
            },
            headers={"Authorization": f"Bearer {TestState.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be classified into a domain
        assert data["domain"] in ["Science", "Health", "Other"]
        print(f"✓ Claim classified into domain: {data['domain']}")


# Run tests in order
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
