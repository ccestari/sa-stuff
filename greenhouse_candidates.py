import requests
import json
import base64
import time
import csv
import boto3
import os
from urllib.parse import urlparse

class GreenhouseAPI:
    def __init__(self, api_key):
        self.base_url = "https://harvest.greenhouse.io/v1"
        credentials = base64.b64encode(f"{api_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'greenhouse-application-storage'
    
    def get_candidates(self):
        """Get list of all candidates with pagination"""
        all_candidates = []
        page = 1
        per_page = 100
        
        while True:
            params = {'page': page, 'per_page': per_page}
            response = requests.get(f"{self.base_url}/candidates", headers=self.headers, params=params)
            response.raise_for_status()
            candidates = response.json()
            
            if not candidates:
                break
                
            all_candidates.extend(candidates)
            print(f"Fetched page {page}: {len(candidates)} candidates (total: {len(all_candidates)})")
            
            if len(candidates) < per_page:
                break
                
            page += 1
            time.sleep(0.2)  # Rate limiting between pages
            
        return all_candidates
    
    def get_candidate_details(self, candidate_id):
        """Get detailed candidate information including resume"""
        time.sleep(0.5)  # Rate limiting
        response = requests.get(f"{self.base_url}/candidates/{candidate_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def download_and_upload_resume(self, resume_url, candidate_id):
        """Download resume and upload to S3"""
        if not resume_url:
            return None
            
        try:
            response = requests.get(resume_url)
            response.raise_for_status()
            
            # Get file extension from URL
            parsed_url = urlparse(resume_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.pdf'
            
            # Create S3 key
            s3_key = f"resumes/{candidate_id}{file_ext}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=response.content
            )
            
            return f"s3://{self.bucket_name}/{s3_key}"
            
        except Exception as e:
            print(f"Error uploading resume for candidate {candidate_id}: {e}")
            return None
    
    def extract_candidate_info(self):
        """Main function to get candidates and extract required information"""
        candidates = self.get_candidates()
        results = []
        
        for candidate in candidates:
            candidate_id = candidate['id']
            details = self.get_candidate_details(candidate_id)
            
            # Extract application IDs
            application_ids = ','.join(str(app['id']) for app in details.get('applications', []))
            
            # Extract resume link
            resume_link = None
            for attachment in details.get('attachments', []):
                if attachment.get('type') == 'resume':
                    resume_link = attachment.get('url')
                    break
            
            # Download and upload resume to S3
            s3_resume_path = self.download_and_upload_resume(resume_link, candidate_id)
            
            results.append({
                'candidate_id': candidate_id,
                'application_ids': application_ids,
                'resume_link': resume_link,
                's3_resume_path': s3_resume_path
            })
        
        return results
    
    def save_to_csv(self, data, filename='greenhouse_candidates.csv'):
        """Save results to CSV file"""
        if not data:
            return
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['candidate_id', 'application_ids', 'resume_link', 's3_resume_path']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)

def main():
    api_key = "6761621a2aaed595723894a78314b51f-8"
    
    greenhouse = GreenhouseAPI(api_key)
    
    try:
        print("Extracting candidate information...")
        candidate_info = greenhouse.extract_candidate_info()
        
        print(f"Saving {len(candidate_info)} candidates to CSV...")
        greenhouse.save_to_csv(candidate_info)
        
        print("Process completed successfully!")
        print(f"CSV file: greenhouse_candidates.csv")
        print(f"Resumes uploaded to: s3://greenhouse-application-storage/resumes/")
            
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()