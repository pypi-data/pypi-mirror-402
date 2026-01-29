"""Facia API client for facial analysis operations."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class FaciaClient:
    """Client for interacting with Facia APIs."""

    def __init__(self, client_id: str, client_secret: str, storage_dir: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.facia.ai"
        self.access_token: Optional[str] = None
        self.storage_dir = Path(storage_dir).expanduser() if storage_dir else Path.cwd()

        if not self.client_id or not self.client_secret:
            raise ValueError("Facia client_id and client_secret are required")

    async def _get_access_token(self) -> str:
        """Retrieve and cache access token."""
        if self.access_token:
            return self.access_token

        payload = {"client_id": self.client_id, "client_secret": self.client_secret}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/request-access-token", data=payload, timeout=30.0)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get access token: {resp.status_code} {resp.text}")
        data = resp.json()
        token = data.get("result", {}).get("data", {}).get("token")
        if not token:
            raise RuntimeError(f"Access token missing in response: {data}")
        self.access_token = token
        return token

    def _read_image_bytes(self, image_name: str) -> bytes:
        """Read an image from storage_dir and return bytes."""
        image_path = self.storage_dir / image_name
        if not image_path.exists():
            raise FileNotFoundError(
                f"The image '{image_name}' was not found in the storage directory ({self.storage_dir}). "
                "Please check and list available files before using the Facia tool, and ensure you select only the intended image."
            )
        return image_path.read_bytes()

    async def _post_file(self, endpoint: str, files: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to post multipart request with auth."""
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                data=payload,
                files=files,
                timeout=60.0,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"Facia API error: {resp.status_code} {resp.text}")
        return resp.json()

    async def age_estimation(self, image_name: str) -> Dict[str, Any]:
        image_bytes = self._read_image_bytes(image_name)
        payload = {"type": "age_estimation", "enroll_face": 1, "wait_for_result": 1}
        files = {"file": (image_name, image_bytes, "image/jpeg")}
        result = await self._post_file("age-estimation", files, payload)
        return result.get("result", result)

    async def deepfake_detection(self, image_name: str) -> Dict[str, Any]:
        image_bytes = self._read_image_bytes(image_name)
        payload = {
            "type": "liveness",
            "file": image_name,
            "detect_deepfake": 1,
            "offsite_liveness": 1,
            "wait_for_result": 1,
        }
        files = {"file": (image_name, image_bytes, "image/jpeg")}
        result = await self._post_file("liveness", files, payload)
        return result.get("result", result)

    async def face_match(self, original_image_name: str, matched_image_name: str) -> Dict[str, Any]:
        original_bytes = self._read_image_bytes(original_image_name)
        matched_bytes = self._read_image_bytes(matched_image_name)
        payload = {
            "type": "photo_id_match",
            "allow_override": 0,
            "enroll_face": 0,
            "wait_for_result": 1,
        }
        files = {
            "face_frame": (original_image_name, original_bytes, "image/jpeg"),
            "id_frame": (matched_image_name, matched_bytes, "image/jpeg"),
        }
        result = await self._post_file("face-match", files, payload)
        return result.get("result", result)
