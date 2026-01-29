from __future__ import annotations

import re
from typing import Any

import httpx

from .constants import BASE_URL

app_bundle_path_regex = re.compile(r'<script src="([^"]+_app-[^"]+.js)"')


class SystembolagetClient(httpx.Client):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()

        self.api_key = self._fetch_api_key()
        self.headers = {
            "Origin": BASE_URL,
            "Access-Control-Allow-Origin": "*",
            "Pragma": "no-cache",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": self.api_key,
        }

    def _fetch_api_key(self) -> str:
        response = httpx.get(BASE_URL)
        response.raise_for_status()

        if match := app_bundle_path_regex.search(response.text):
            bundle_path = match.group(1)
        else:
            raise AssertionError("Could not find app bundle path")

        bundle_url = f"{BASE_URL}{bundle_path}"

        return self._extract_api_key_from_bundle(bundle_url=bundle_url)

    def _extract_api_key_from_bundle(self, bundle_url: str) -> str:
        response = httpx.get(bundle_url)
        response.raise_for_status()

        match = re.search(
            r'NEXT_PUBLIC_API_KEY_APIM:"([a-f0-9]+)"',
            response.text,
        )
        if match:
            api_key = match.group(1)
        else:
            raise AssertionError(f"No API key found in {bundle_url}")

        return api_key
