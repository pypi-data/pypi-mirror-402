import requests
import os
import base64
import json

class StructOCR:
    """
    StructOCR Python Client
    Get your API Key at: https://structocr.com
    """
    def __init__(self, api_key=None, base_url="https://api.structocr.com/v1"):
        # Allow reading API Key from environment variables for better DX
        self.api_key = api_key or os.environ.get('STRUCTOCR_API_KEY')
        if not self.api_key:
            raise ValueError("API Key is required. Get one at https://structocr.com")
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Updated headers based on your API specification
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "StructOCR-Python/1.0.0"
        })

    def _post_image(self, endpoint, file_path):
        """
        Internal method: Handle image encoding and API request.
        """
        url = f"{self.base_url}/{endpoint}"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # 1. Encode image to Base64
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # 2. Prepare JSON payload
            payload = {
                "img": base64_image
            }

            # 3. Send Request
            response = self.session.post(url, json=payload)
            response.raise_for_status() # Raise error for 4xx/5xx responses
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Handle connection errors or API errors
            raise Exception(f"API Request failed: {str(e)}")

    # --- Public Methods for Developers ---

    def scan_passport(self, file_path):
        """
        Scan a Passport image.
        path: Path to the passport image file.
        Returns: Structured JSON data.
        """
        # Endpoint: /v1/passport
        return self._post_image('passport', file_path)

    def scan_national_id(self, file_path):
        """
        Scan a National ID card.
        path: Path to the ID card image file.
        Returns: Structured JSON data.
        """
        # Endpoint: /v1/national-id 
        return self._post_image('national-id', file_path)

    def scan_driver_license(self, file_path):
        """
        Scan a Driver License.
        path: Path to the driver license image file.
        Returns: Structured JSON data.
        """
        # Endpoint: /v1/driver-license
        return self._post_image('driver-license', file_path)
    
    def scan_driver_license(self, file_path):
        """
        Scan a Invoice.
        path: Path to the invoice image file.
        Returns: Structured JSON data.
        """
        # Endpoint: /v1/invoice 
        return self._post_image('invoice', file_path)