import requests
import json

class GreenhouseOAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://harvest.greenhouse.io/v1"
        self.token_url = "https://api.greenhouse.io/oauth/token"
        self.access_token = None
        
    def get_access_token(self):
        """Get OAuth access token"""
        import base64
        auth_string = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {'Authorization': f'Basic {auth_string}'}
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(self.token_url, headers=headers, data=data)
        print(f"Token response: {response.status_code} - {response.text}")
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data['access_token']
        return self.access_token
    
    def get_candidates(self):
        """Get list of all candidates"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{self.base_url}/candidates", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_candidate_details(self, candidate_id):
        """Get detailed candidate information"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{self.base_url}/candidates/{candidate_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def extract_candidate_info(self):
        """Main function to get candidates and extract required information"""
        candidates = self.get_candidates()
        results = []
        
        for candidate in candidates:
            candidate_id = candidate['id']
            details = self.get_candidate_details(candidate_id)
            
            application_ids = [app['id'] for app in details.get('applications', [])]
            
            resume_link = None
            for attachment in details.get('attachments', []):
                if attachment.get('type') == 'resume':
                    resume_link = attachment.get('url')
                    break
            
            results.append({
                'candidate_id': candidate_id,
                'application_ids': application_ids,
                'resume_link': resume_link
            })
        
        return results

def main():
    client_id = "3P6juCNpC2FmH13Pq8FYeggQbY0W0Vbhssg0-8"
    client_secret = "dM4tN0zeZ3d6FxA3oOg76u0Ujk0dgF01nZ02mtnP"
    
    greenhouse = GreenhouseOAuth(client_id, client_secret)
    
    try:
        candidate_info = greenhouse.extract_candidate_info()
        
        for info in candidate_info:
            print(f"Candidate ID: {info['candidate_id']}")
            print(f"Application IDs: {info['application_ids']}")
            print(f"Resume Link: {info['resume_link']}")
            print("-" * 50)
            
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()