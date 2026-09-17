"""Small dependency-free client used by the desktop app's cloud data layer."""

import json
from urllib import error, parse, request

from cloud_config import load_cloud_settings


class CloudConnectionError(RuntimeError):
    pass


class SupabaseClient:
    """REST client with an authenticated-user token when one is available."""

    def __init__(self):
        self.settings = load_cloud_settings()
        self.base_url = self.settings["supabase_url"].rstrip("/")
        self.publishable_key = self.settings.get("supabase_publishable_key", "").strip()
        self.access_token = None

    @property
    def configured(self):
        return bool(self.base_url and self.publishable_key)

    def _request(self, method, path, payload=None, query=None, extra_headers=None):
        if not self.configured:
            raise CloudConnectionError("Cloud settings are not configured.")
        url = self.base_url + path
        if query:
            url += "?" + parse.urlencode(query, doseq=True)
        headers = {
            "apikey": self.publishable_key,
            "Accept": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra_headers:
            headers.update(extra_headers)
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CloudConnectionError(f"Cloud request failed ({exc.code}): {detail}") from exc
        except error.URLError as exc:
            raise CloudConnectionError(f"Cannot reach the cloud service: {exc.reason}") from exc

    def sign_in(self, email, password):
        result = self._request(
            "POST", "/auth/v1/token", {"email": email, "password": password},
            {"grant_type": "password"},
        )
        self.access_token = result["access_token"]
        return result

    def list_records(self, collection, domain=None):
        filters = {"collection": f"eq.{collection}", "select": "*", "order": "updated_at.desc"}
        if domain:
            filters["domain"] = f"eq.{domain}"
        return self._request("GET", "/rest/v1/company_records", query=filters)

    def upsert_record(self, domain, collection, source_key, data, version=None):
        """Create/update one record. Versioning prevents silent overwrites."""
        payload = {
            "domain": domain,
            "collection": collection,
            "source_key": str(source_key),
            "data": data,
        }
        headers = {"Prefer": "resolution=merge-duplicates,return=representation"}
        if version is not None:
            payload["record_version"] = version + 1
        return self._request("POST", "/rest/v1/company_records", [payload], extra_headers=headers)
