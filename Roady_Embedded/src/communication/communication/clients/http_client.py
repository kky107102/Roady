from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import requests


class DamageHttpClient:
    def __init__(self, base_url: str, access_token: Optional[str] = None, timeout_sec: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout_sec = timeout_sec

    def upload_damage(
        self,
        robot_id: int | str,
        description: str,
        latitude: float,
        longitude: float,
        captured_at: str | datetime,
        image_paths: Iterable[str | Path],
    ) -> requests.Response:
        url = f"{self.base_url}/api/damages"
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        data = {
            "robotId": str(robot_id),
            "description": description,
            "latitude": f"{float(latitude):.7f}",
            "longitude": f"{float(longitude):.7f}",
            "capturedAt": self._format_captured_at(captured_at),
        }

        with ExitStack() as stack:
            files = []
            for image_path in image_paths:
                path = Path(image_path)
                fp = stack.enter_context(path.open("rb"))
                files.append(("images", (path.name, fp, "image/jpeg")))

            response = requests.post(
                url,
                headers=headers,
                data=data,
                files=files,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            return response

    @staticmethod
    def _format_captured_at(value: str | datetime) -> str:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None).isoformat(timespec="seconds")
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).replace(tzinfo=None).isoformat(timespec="seconds")
        except ValueError:
            return value.replace("+00:00", "").replace("Z", "")
