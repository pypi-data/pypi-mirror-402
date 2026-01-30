"""
Terso API client.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, BinaryIO

import requests
from tqdm import tqdm

from terso.config import get_api_key, get_base_url


class TersoError(Exception):
    """Base exception for Terso errors."""
    pass


class AuthenticationError(TersoError):
    """Raised when API key is invalid or missing."""
    pass


class NotFoundError(TersoError):
    """Raised when a resource is not found."""
    pass


class Client:
    """
    Client for the Terso API.
    
    Usage:
        client = Client(api_key="your-key")
        
        # Upload a video
        clip = client.upload("video.mp4", task="pour_latte")
        print(f"Clip ID: {clip['id']}")
        
        # Wait for processing
        clip = client.wait(clip["id"])
        
        # Download results
        client.download(clip["id"], "output/")
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the Terso client.
        
        Args:
            api_key: Your API key. If not provided, reads from TERSO_API_KEY
                    environment variable or ~/.terso/config.json
            base_url: API base URL. Defaults to https://api.terso.ai
        """
        self.api_key = api_key or get_api_key()
        self.base_url = (base_url or get_base_url()).rstrip("/")
        
        self._session = requests.Session()
        if self.api_key:
            self._session.headers["x-api-key"] = self.api_key
    
    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> requests.Response:
        """Make an API request."""
        url = f"{self.base_url}{path}"
        response = self._session.request(method, url, **kwargs)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid or missing API key")
        if response.status_code == 404:
            raise NotFoundError(f"Not found: {path}")
        
        response.raise_for_status()
        return response
    
    def upload(
        self,
        video_path: str | Path,
        *,
        task: str | None = None,
        partner_id: str | None = None,
        wait: bool = False,
        timeout: int = 600,
    ) -> dict[str, Any]:
        """
        Upload a video for processing.
        
        Args:
            video_path: Path to video file (mp4, mov, avi, mkv)
            task: Task type (e.g., "pour_latte", "pick_object")
            partner_id: Partner ID for attribution
            wait: If True, wait for processing to complete
            timeout: Timeout in seconds when waiting
            
        Returns:
            Clip metadata dict with id, status, etc.
            
        Example:
            clip = client.upload("demo.mp4", task="pour", wait=True)
            print(clip["status"])  # "ready"
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        with open(video_path, "rb") as f:
            files = {"file": (video_path.name, f, "video/mp4")}
            data = {}
            if task:
                data["task"] = task
            if partner_id:
                data["partnerId"] = partner_id
            
            response = self._request(
                "POST",
                "/clips/upload",
                files=files,
                data=data,
            )
        
        result = response.json()
        
        if wait:
            result = self.wait(result["id"], timeout=timeout)
        
        return result
    
    def wait(
        self,
        clip_id: str,
        timeout: int = 600,
        poll_interval: int = 2,
    ) -> dict[str, Any]:
        """
        Wait for clip processing to complete.
        
        Args:
            clip_id: Clip ID from upload
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status
            
        Returns:
            Final clip metadata
        """
        start = time.time()
        
        with tqdm(total=100, desc="Processing", unit="%", leave=False) as pbar:
            last_progress = 0
            
            while time.time() - start < timeout:
                clip = self.get(clip_id)
                status = clip["status"]
                
                # Map status to progress
                progress_map = {
                    "pending": 5,
                    "validating": 20,
                    "processing": 50,
                    "ready": 100,
                    "rejected": 100,
                }
                progress = progress_map.get(status, 0)
                
                # Use detailed progress if available
                if clip.get("progress"):
                    progress = clip["progress"].get("percent", progress)
                
                pbar.update(progress - last_progress)
                last_progress = progress
                
                if status in ("ready", "rejected"):
                    break
                
                time.sleep(poll_interval)
            else:
                raise TimeoutError(f"Processing timed out after {timeout}s")
        
        return clip
    
    def get(self, clip_id: str) -> dict[str, Any]:
        """
        Get clip metadata.
        
        Args:
            clip_id: Clip ID
            
        Returns:
            Clip metadata dict
        """
        response = self._request("GET", f"/clips/{clip_id}")
        return response.json()
    
    def status(self, clip_id: str) -> dict[str, Any]:
        """
        Get clip processing status.
        
        Args:
            clip_id: Clip ID
            
        Returns:
            Status dict with status and progress
        """
        response = self._request("GET", f"/clips/{clip_id}/status")
        return response.json()
    
    def list(
        self,
        *,
        task: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List clips.
        
        Args:
            task: Filter by task type
            status: Filter by status (pending, processing, ready, rejected)
            limit: Max results to return
            offset: Pagination offset
            
        Returns:
            Dict with "clips" list and "total" count
        """
        params = {"limit": limit, "offset": offset}
        if task:
            params["task"] = task
        if status:
            params["status"] = status
        
        response = self._request("GET", "/clips", params=params)
        return response.json()
    
    def download(
        self,
        clip_id: str,
        output_dir: str | Path,
        *,
        extract: bool = True,
    ) -> Path:
        """
        Download a processed clip with annotations.
        
        Args:
            clip_id: Clip ID
            output_dir: Directory to save to
            extract: Whether to extract the zip archive
            
        Returns:
            Path to downloaded clip directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        response = self._request(
            "GET",
            f"/clips/{clip_id}/download",
            stream=True,
        )
        
        archive_path = output_dir / f"{clip_id}.zip"
        total_size = int(response.headers.get("content-length", 0))
        
        with open(archive_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        if extract:
            import zipfile
            
            clip_dir = output_dir / clip_id
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(clip_dir)
            
            archive_path.unlink()
            return clip_dir
        
        return archive_path
    
    def annotation(
        self,
        clip_id: str,
        annotation_type: str,
    ) -> Any:
        """
        Get a specific annotation.
        
        Args:
            clip_id: Clip ID
            annotation_type: One of: hand_poses, actions, depth_maps, objects, metadata
            
        Returns:
            Annotation data (format depends on type)
        """
        response = self._request("GET", f"/clips/{clip_id}/annotations/{annotation_type}")
        return response.json()
    
    def delete(self, clip_id: str) -> bool:
        """
        Delete a clip.
        
        Args:
            clip_id: Clip ID
            
        Returns:
            True if deleted
        """
        self._request("DELETE", f"/clips/{clip_id}")
        return True
    
    def retry(self, clip_id: str) -> dict[str, Any]:
        """
        Retry processing a failed clip.
        
        Args:
            clip_id: Clip ID of a rejected clip
            
        Returns:
            Updated clip metadata
        """
        response = self._request("POST", f"/clips/{clip_id}/retry")
        return response.json()


# Module-level convenience functions using default client
_default_client: Client | None = None


def _get_client() -> Client:
    """Get or create default client."""
    global _default_client
    if _default_client is None:
        _default_client = Client()
    return _default_client


def upload(video_path: str | Path, **kwargs) -> dict[str, Any]:
    """
    Upload a video. See Client.upload for args.
    
    Example:
        from terso import upload
        clip = upload("video.mp4", task="pour", wait=True)
    """
    return _get_client().upload(video_path, **kwargs)


def download(clip_id: str, output_dir: str | Path, **kwargs) -> Path:
    """
    Download a clip. See Client.download for args.
    
    Example:
        from terso import download
        path = download("abc123", "./output")
    """
    return _get_client().download(clip_id, output_dir, **kwargs)
