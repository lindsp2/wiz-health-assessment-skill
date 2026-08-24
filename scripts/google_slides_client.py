"""
Google Drive & Slides Client for QBR Deck Builder.

Handles:
- Copying the QBR Google Slides template (1ga4sflsBPZS2lsXi6k6fUY1jU5dOrqQ9bQ1JEp3B5GM)
- Applying batchUpdate variable replacements
- Token sweep for unreplaced {{TOKEN}} markers
- Moving previous decks into customer archive subfolder
"""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import os
import urllib.parse


QBR_TEMPLATE_ID = "1ga4sflsBPZS2lsXi6k6fUY1jU5dOrqQ9bQ1JEp3B5GM"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
SLIDES_API_BASE = "https://slides.googleapis.com/v1"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleSlidesClient:
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls) -> Optional["GoogleSlidesClient"]:
        """Instantiate client by loading credentials from .env and refreshing access token."""
        env_data = {}
        env_file = Path(__file__).resolve().parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_data[k.strip()] = v.strip().strip('"').strip("'")
                break

        client_id = env_data.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = env_data.get("GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET")
        refresh_token = env_data.get("GOOGLE_REFRESH_TOKEN") or os.environ.get("GOOGLE_REFRESH_TOKEN")

        if not (client_id and client_secret and refresh_token):
            return None

        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        data = urllib.parse.urlencode(token_payload).encode("utf-8")
        req = urllib.request.Request(TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                access_token = res.get("access_token")
                if access_token:
                    return cls(access_token)
        except Exception as e:
            print(f"[WARN] Failed to refresh Google OAuth token: {e}")

        return None

    def _request(self, method: str, url: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def copy_template(self, customer_name: str, timestamp_str: str, customer_folder_id: str) -> Dict[str, Any]:
        deck_name = f"QBR Deck - {customer_name} - {timestamp_str}"
        url = f"{DRIVE_API_BASE}/files/{QBR_TEMPLATE_ID}/copy?fields=id,name,webViewLink"
        body = {
            "name": deck_name,
            "parents": [customer_folder_id],
        }
        return self._request("POST", url, body)

    def batch_update_presentation(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{SLIDES_API_BASE}/presentations/{presentation_id}:batchUpdate"
        body = {"requests": requests}
        return self._request("POST", url, body)

    def sweep_remaining_tokens(self, presentation_id: str) -> Dict[str, Any]:
        url = f"{SLIDES_API_BASE}/presentations/{presentation_id}"
        pres = self._request("GET", url)

        tokens: Set[str] = set()
        for slide in pres.get("slides", []):
            for elem in slide.get("pageElements", []):
                shape = elem.get("shape") or {}
                text_obj = shape.get("text") or {}
                for te in text_obj.get("textElements", []):
                    content = (te.get("textRun") or {}).get("content", "")
                    for match in re.findall(r"\{\{[A-Z0-9_]+\}\}", content):
                        tokens.add(match)

        if not tokens:
            return {"swept_count": 0}

        sweep_requests = [
            {"replaceAllText": {"containsText": {"text": t, "matchCase": True}, "replaceText": ""}}
            for t in tokens
        ]
        # Clean up Slide 11 empty CI_CBC Issue labels
        for idx in [1, 2, 3]:
            sweep_requests.append({
                "replaceAllText": {
                    "containsText": {"text": f"{{{{CI_CBC_{idx}}}}} Issues", "matchCase": True},
                    "replaceText": ""
                }
            })

        # Clean up Slide 12 hardcoded customer text
        sweep_requests.append({
            "replaceAllText": {
                "containsText": {"text": "custom TWDC Graph Controls", "matchCase": True},
                "replaceText": "custom Graph Controls"
            }
        })
        # Clean up %%%%%% artifacts on Slide 4
        for pat in ["%%%%%%", "%%%%%", "%%%%", "%%%", "%%"]:
            sweep_requests.append({
                "replaceAllText": {
                    "containsText": {"text": pat, "matchCase": True},
                    "replaceText": ""
                }
            })
        # Clean up Agent Enabled labels when Not Deployed / N/A
        for pat in ["Enabled\x0bNot Deployed", "Enabled\nNot Deployed", "Enabled\r\nNot Deployed", "Enabled\x0bN/A", "Enabled\nN/A"]:
            sweep_requests.append({
                "replaceAllText": {
                    "containsText": {"text": pat, "matchCase": True},
                    "replaceText": "Not Deployed"
                }
            })
        self.batch_update_presentation(presentation_id, sweep_requests)
        return {"swept_count": len(tokens), "tokens": list(tokens)}

    def archive_prior_decks(self, customer_folder_id: str, new_deck_id: str) -> int:
        query = f"'{customer_folder_id}' in parents and name contains 'QBR Deck' and trashed=false"
        url = f"{DRIVE_API_BASE}/files?q={urllib.parse.quote(query)}&fields=files(id,name)&pageSize=50"
        res = self._request("GET", url)
        files = res.get("files", [])
        prior_files = [f for f in files if f.get("id") != new_deck_id]

        if not prior_files:
            return 0

        # Find or create archive folder
        arch_query = f"name='archive' and mimeType='application/vnd.google-apps.folder' and '{customer_folder_id}' in parents and trashed=false"
        arch_url = f"{DRIVE_API_BASE}/files?q={urllib.parse.quote(arch_query)}&fields=files(id,name)&pageSize=1"
        arch_res = self._request("GET", arch_url)
        arch_files = arch_res.get("files", [])

        if arch_files:
            archive_folder_id = arch_files[0]["id"]
        else:
            create_body = {
                "name": "archive",
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [customer_folder_id],
            }
            create_res = self._request("POST", f"{DRIVE_API_BASE}/files?fields=id,name", create_body)
            archive_folder_id = create_res["id"]

        # Move prior files
        for pf in prior_files:
            fid = pf["id"]
            patch_url = f"{DRIVE_API_BASE}/files/{fid}?addParents={archive_folder_id}&removeParents={customer_folder_id}&fields=id,name,parents"
            self._request("PATCH", patch_url)

        return len(prior_files)

    def export_pdf(self, presentation_id: str, output_path: str) -> str:
        """
        Export a Google Slides presentation directly to a high-resolution PDF file.
        Uses Drive API export endpoint: /files/{presentation_id}/export?mimeType=application/pdf
        """
        url = f"{DRIVE_API_BASE}/files/{presentation_id}/export?mimeType=application/pdf"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.auth_token}"})
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(req, timeout=120) as resp:
            pdf_bytes = resp.read()
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
        return output_path
