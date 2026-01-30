import time
from .retry import DEFAULT_RETRY, compute_backoff, parse_retry_after
import os
from typing import Optional, Any, Dict
import requests

from .http import make_default_session
from .errors import raise_for_status
from .types import TimeoutType

DEFAULT_BASE_URL = "https://api.solidarity.tech"

class SolidarityClient:
    """
    Low-level Solidarity Tech client that manages the base URL and a requests session.

    Create via:
        client = SolidarityClient(base_url, api_key)
        client = SolidarityClient.from_env()

    Then use resources, e.g.:
        client.users
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        session: Optional[requests.Session] = None,
        timeout: TimeoutType = (10, 60),
        user_agent: str = "pysolidarity/0.1",
    ) -> None:
        if not base_url:
            raise RuntimeError("Missing base_url")
        if not api_key:
            raise RuntimeError("Missing api_key")

        if "Zapier" not in user_agent:
            user_agent = f"{user_agent} Zapier"

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session or make_default_session(
            api_key=api_key, timeout=timeout, user_agent=user_agent
        )
        self.timeout = timeout
        self.retry = DEFAULT_RETRY

    @classmethod
    def from_env(
        cls,
        *,
        session: Optional[requests.Session] = None,
        timeout: TimeoutType = (10, 60),
        user_agent: str = "pysolidarity/0.1",
    ) -> "SolidarityClient":
        base_url = os.getenv("SOLIDARITY_BASE_URL", DEFAULT_BASE_URL)
        api_key = os.getenv("SOLIDARITY_API_KEY")
        if not api_key:
            raise RuntimeError("Missing env: SOLIDARITY_API_KEY")
        return cls(
            base_url,
            api_key,
            session=session,
            timeout=timeout,
            user_agent=user_agent,
        )

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        url = self._url(path)
        attempt = 0
        last_exc = None
        last_resp = None

        while True:
            try:
                resp = self.session.request(
                    method, url, json=json, params=params,
                    timeout=getattr(self.session, "_default_timeout", self.timeout)
                )
                last_resp = resp
            except self.retry.retry_on_exceptions as exc:
                last_exc = exc
                if attempt >= self.retry.max_retries:
                    # Give a clear terminal signal
                    raise RetryExhausted(method, url, attempts=attempt+1, last_exception=exc)
                delay = compute_backoff(attempt, self.retry.backoff_initial, self.retry.backoff_max, self.retry.jitter)
                time.sleep(delay)
                attempt += 1
                continue

            # Success
            if 200 <= resp.status_code < 300:
                if not resp.content:
                    return None
                try:
                    return resp.json()
                except Exception:
                    return resp.text

            # Retryable statuses
            if resp.status_code in self.retry.retry_on_statuses and attempt < self.retry.max_retries:
                delay = compute_backoff(attempt, self.retry.backoff_initial, self.retry.backoff_max, self.retry.jitter)
                if resp.status_code in (429, 503):  # both often publish Retry-After
                    ra = parse_retry_after(resp.headers.get("Retry-After"))
                    if ra is not None:
                        delay = max(delay, ra)
                time.sleep(delay)
                attempt += 1
                continue

            # Non-retryable → raise specific error
            if resp.status_code in self.retry.retry_on_statuses:
                # retry budget exhausted
                raise RetryExhausted(method, url, attempts=attempt+1, last_response=resp)
            raise_for_status(resp)

    @property
    def users(self) -> "UsersResource":
        from .resources.users import UsersResource
        return UsersResource(self)
    
    def send_sms(self,
                 user_id: int, 
                 body: str
                 ) -> None:
        """
        Send an SMS to a user at their primary phone number.

        :param int user_id: The ID of the user to send the text to.
        :param str body: The content of the message.
        """
        # https://www.solidarity.tech/reference/post_texts
        params = {
            "user_id": user_id,
            "body": body
        }
        self.request(
            "POST",
            "/v1/texts",
            params=params)

    def send_email(self,
                   user_id: int, 
                   subject: str,
                   body_html: str,
                   body_plain: str | None = None,
                   sender_id: int | None = None,
                   reply_to: str | None = None,
                   attachment_urls: list[str] | None = None,
                   track_opens: bool = True,
                   track_clicks: bool = True
                   ) -> None:
        if not attachment_urls:
            attachment_urls = None
        params = {
            "user_id": user_id,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "email_sender_id": sender_id,
            "reply_to": reply_to,
            "attachment_urls": attachment_urls,
            "track_opens": track_opens,
            "track_clicks": track_clicks,
        }

        self.request(
            "POST",
            "/v1/emails",
            params=params
        )
