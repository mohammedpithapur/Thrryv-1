import requests
import sys
import json
from datetime import datetime
import tempfile
import os

class ThrryveAPITester:
    def __init__(self, base_url="https://truthscore-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)
        
        if files:
            # Remove Content-Type for file uploads
            test_headers.pop('Content-Type', None)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=test_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return test_user
        return None

    def test_user_login(self, user_data):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": user_data["email"], "password": user_data["password"]}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_get_current_user(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_claim(self):
        """Test creating a claim"""
        claim_data = {
            "text": "Climate change is primarily caused by human activities according to scientific consensus.",
            "domain": "Science",
            "confidence_level": 85,
            "media_ids": []
        }
        
        success, response = self.run_test(
            "Create Claim",
            "POST",
            "claims",
            200,
            data=claim_data
        )
        
        return response.get('id') if success else None

    def test_get_claims(self):
        """Test getting claims feed"""
        success, response = self.run_test(
            "Get Claims Feed",
            "GET",
            "claims",
            200
        )
        return success

    def test_get_claim_detail(self, claim_id):
        """Test getting claim details"""
        success, response = self.run_test(
            "Get Claim Detail",
            "GET",
            f"claims/{claim_id}",
            200
        )
        return success

    def test_create_annotation(self, claim_id):
        """Test creating an annotation"""
        annotation_data = {
            "text": "This is supported by multiple peer-reviewed studies from NASA and NOAA.",
            "annotation_type": "support",
            "media_ids": []
        }
        
        success, response = self.run_test(
            "Create Annotation",
            "POST",
            f"claims/{claim_id}/annotations",
            200,
            data=annotation_data
        )
        
        return response.get('id') if success else None

    def test_get_annotations(self, claim_id):
        """Test getting annotations for a claim"""
        success, response = self.run_test(
            "Get Annotations",
            "GET",
            f"claims/{claim_id}/annotations",
            200
        )
        return success

    def test_vote_annotation(self, annotation_id):
        """Test voting on an annotation"""
        success, response = self.run_test(
            "Vote on Annotation",
            "POST",
            f"annotations/{annotation_id}/vote",
            200,
            data={"helpful": True}
        )
        return success

    def test_get_user_profile(self):
        """Test getting user profile"""
        if not self.user_id:
            self.log_test("Get User Profile", False, "No user ID available")
            return False
            
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            f"users/{self.user_id}",
            200
        )
        return success

    def test_media_upload(self):
        """Test media upload"""
        # Create a small test image file
        try:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
                tmp_file.write(b"Test file content for media upload")
                tmp_file_path = tmp_file.name
            
            with open(tmp_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                success, response = self.run_test(
                    "Media Upload",
                    "POST",
                    "media/upload",
                    200,
                    files=files
                )
            
            # Clean up
            os.unlink(tmp_file_path)
            return response.get('id') if success else None
            
        except Exception as e:
            self.log_test("Media Upload", False, f"File creation error: {str(e)}")
            return None

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Thrryv API Tests...")
        print(f"Testing against: {self.base_url}")
        print("-" * 50)

        # Test user registration and authentication
        user_data = self.test_user_registration()
        if not user_data:
            print("❌ Registration failed, stopping tests")
            return False

        # Test login
        if not self.test_user_login(user_data):
            print("❌ Login failed, stopping tests")
            return False

        # Test authenticated endpoints
        self.test_get_current_user()
        
        # Test media upload
        media_id = self.test_media_upload()
        
        # Test claim creation
        claim_id = self.test_create_claim()
        if not claim_id:
            print("❌ Claim creation failed, skipping dependent tests")
        else:
            # Test claim-related endpoints
            self.test_get_claim_detail(claim_id)
            
            # Test annotation creation
            annotation_id = self.test_create_annotation(claim_id)
            if annotation_id:
                self.test_get_annotations(claim_id)
                # Note: Can't test voting on own annotation, would need second user
                
        # Test feed and profile
        self.test_get_claims()
        self.test_get_user_profile()

        # Print summary
        print("-" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed")
            return False

def main():
    tester = ThrryveAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
            'results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())