from typing import Optional

import requests

from .config import settings


class FetchError(Exception):
    pass


def fetch_page(url: Optional[str] = None) -> str:
    """
    抓取目标页面 HTML 文本，带简单重试。
    """
    target = url or settings.target_url
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            resp = requests.get(
                target,
                timeout=settings.request_timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/123.0 Safari/537.36"
                    )
                },
            )
            resp.raise_for_status()
            return resp.text
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
    raise FetchError(f"Failed to fetch page after retries: {last_exc}")

