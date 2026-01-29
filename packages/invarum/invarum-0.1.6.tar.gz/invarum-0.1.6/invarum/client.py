# invarum-cli/invarum/client.py
import os
import requests
import time
from typing import Dict, Any
from invarum import __version__

# Default to localhost for now, but ready for prod
DEFAULT_API_BASE = "https://api.invarum.com"

class InvarumClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv("INVARUM_API_BASE", DEFAULT_API_BASE)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Invarum-Version": __version__
        }

    def submit_run(
        self, 
        prompt: str, 
        task: str, 
        domain: str,
        reference: str = None,
        temperature: float = None
    ) -> Dict[str, Any]:  
        """Submits a run and returns the full response object"""
        url = f"{self.base_url}/runs"
        
        payload = {
            "prompt": prompt, 
            "task": task, 
            "domain": domain
        }
        
        if reference:
            payload["reference"] = reference

        if temperature is not None:
            payload["temperature"] = temperature

        try:
            resp = requests.post(
                url, 
                json=payload, 
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json() # Returns the full dict {run_id, message, system_message...}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API Key")
            raise e

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Fetches run details"""
        url = f"{self.base_url}/runs/{run_id}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def wait_for_run(self, run_id: str, poll_interval=2) -> Dict[str, Any]:
        """Polls until run is complete"""
        while True:
            data = self.get_run(run_id)
            status = data.get("status")
            
            if status == "succeeded":
                return data
            if status == "failed":
                raise RuntimeError(f"Run failed: {data.get('error')}")
            
            time.sleep(poll_interval)

    def get_run_evidence(self, run_id: str) -> Dict[str, Any]:
            """Fetches the evidence bundle (contains the text response)"""
            url = f"{self.base_url}/runs/{run_id}/evidence"
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 404:
                return {} # Handle case where evidence isn't ready yet
            resp.raise_for_status()
            return resp.json()

    def get_audit_pdf(self, run_id: str) -> bytes:
        """Fetches the PDF audit report as binary data"""
        # Note: Ensure your API endpoint matches this path
        url = f"{self.base_url}/runs/{run_id}/audit.pdf?include_spans=1&include_sensitivity=1"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 404:
            raise ValueError("Run not found or PDF not available")
        resp.raise_for_status()
        return resp.content