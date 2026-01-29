# liberal_alpha/client.py
from __future__ import annotations

import os
import time
import math
import json
import gzip
import hashlib
import logging
import datetime as dt
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

import requests

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore

try:
    import msgpack
except Exception:  # pragma: no cover
    msgpack = None  # type: ignore

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

from eth_account import Account
from eth_account.messages import encode_defunct

from .crypto import get_wallet_address, decrypt_alpha_message
from .proto_utils import parse_length_prefixed_messages

# ---- endpoints ----
DEFAULT_API_BASE = os.getenv("LIBALPHA_API_BASE", "https://api.liberalalpha.com").rstrip("/")
AUTH_PATH = "/api/users/auth"  # POST
WITHOUT_ENTRIES_PATH = "/api/entries/v2/without_entries"  # GET
ENTRIES_PATH = "/api/entries/v2/entries"  # GET
# protobuf file download (length-prefixed)
ENTRY_DOWNLOAD_LINKS_PATH = "/api/entries/download-links"  # GET

# upload endpoints (api-key auth)
UPLOAD_CREATE_PATH = "/api/entries/upload-session/create"  # POST (json)
UPLOAD_PROGRESS_PATH = "/api/entries/upload-session/{session_id}/progress"  # GET
UPLOAD_CHUNK_PATH = "/api/entries/upload-session/{session_id}/chunk"  # POST (multipart)
UPLOAD_FINALIZE_PATH = "/api/entries/upload-session/{session_id}/finalize"  # POST

# ✅ V2 additions (do not change existing logic; only add new capabilities)
RECORDS_PATH = "/api/records"
SUBSCRIPTIONS_CANDIDATE_PATHS = [
    "/api/subscriptions",
    "/api/users/subscriptions",
    "/api/users/me/subscriptions",
    "/api/records/subscriptions",
]
WS_V1_PATH = os.getenv("LIBALPHA_WS_V1_PATH", "/ws/data")
WS_V2_PATH = os.getenv("LIBALPHA_WS_V2_PATH", "/ws/data/v2")


# ----------------------------
# Exceptions (keep simple)
# ----------------------------
class ConfigurationError(Exception):
    pass


class RequestError(Exception):
    pass


# ----------------------------
# helpers
# ----------------------------
def _ensure_pandas():
    if pd is None:
        raise ImportError("pandas is required. Please `pip install pandas`.")


def _ensure_msgpack():
    if msgpack is None:
        raise ImportError("msgpack is required for upload_data(). Please `pip install msgpack`.")


def _normalize_private_key(pk: Optional[str]) -> Optional[str]:
    if not pk:
        return None
    pk = pk.strip()
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return pk


def _utc_iso_z(ts: Optional[dt.datetime] = None) -> str:
    if ts is None:
        ts = dt.datetime.now(dt.timezone.utc)
    ts = ts.astimezone(dt.timezone.utc)
    return ts.replace(microsecond=(ts.microsecond // 1000) * 1000).isoformat().replace("+00:00", "Z")


def _parse_iso_any(s: str) -> Optional[dt.datetime]:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def _normalize_tz(tz_info: Union[dt.tzinfo, str, int, float, None]) -> dt.tzinfo:
    """
    Accept:
      - tzinfo instance
      - "Asia/Singapore"
      - "+8" / "-4"
      - 8 / -4 / 5.5 etc
    """
    if tz_info is None:
        return dt.timezone.utc

    if isinstance(tz_info, dt.tzinfo):
        return tz_info

    if isinstance(tz_info, (int, float)):
        hours = float(tz_info)
        minutes = int(round((hours - math.trunc(hours)) * 60))
        return dt.timezone(dt.timedelta(hours=int(math.trunc(hours)), minutes=minutes))

    if isinstance(tz_info, str):
        s = tz_info.strip()
        # "+8" "-4" "5.5"
        if (s.startswith(("+", "-")) and s[1:].replace(".", "", 1).isdigit()) or s.replace(".", "", 1).isdigit():
            return _normalize_tz(float(s))
        # "Asia/xxx"
        if ZoneInfo is None:
            raise ImportError("zoneinfo not available. Use tz offset int like 8 / -4.")
        return ZoneInfo(s)

    raise TypeError(f"Unsupported tz_info type: {type(tz_info)}")


def _guess_timestamp_ms(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        iv = int(value)
    except Exception:
        return None
    # seconds vs ms heuristic
    if iv < 10_000_000_000:
        return iv * 1000
    return iv


def _guess_timestamp_us(value: Any) -> Optional[int]:
    """
    Heuristic for unix timestamps:
      - seconds  (1e9)  -> * 1e6
      - millis   (1e12) -> * 1e3
      - micros   (1e15) -> as-is
    """
    if value is None:
        return None
    try:
        iv = int(value)
    except Exception:
        return None
    # seconds
    if iv < 100_000_000_000:
        return iv * 1_000_000
    # milliseconds
    if iv < 100_000_000_000_000:
        return iv * 1_000
    # microseconds
    return iv


def _dt_to_us(ts: dt.datetime) -> int:
    if not isinstance(ts, dt.datetime):
        raise TypeError("ts must be datetime")
    if ts.tzinfo is None:
        # treat naive as UTC for backward-compat
        ts = ts.replace(tzinfo=dt.timezone.utc)
    ts = ts.astimezone(dt.timezone.utc)
    return int(ts.timestamp() * 1_000_000)


def _normalize_time_range_us(
    start: Union[int, float, str, dt.datetime],
    end: Union[int, float, str, dt.datetime],
) -> Tuple[int, int]:
    """
    Normalize inputs to (start_us, end_us) inclusive.
    Accept:
      - datetime
      - int/float: seconds/ms/us heuristic
      - str: ISO8601
    """
    def to_us(v: Union[int, float, str, dt.datetime]) -> Optional[int]:
        if isinstance(v, dt.datetime):
            return _dt_to_us(v)
        if isinstance(v, str):
            dd = _parse_iso_any(v)
            return _dt_to_us(dd) if dd else None
        if isinstance(v, (int, float)):
            return _guess_timestamp_us(int(v))
        return None

    s = to_us(start)
    e = to_us(end)
    if s is None or e is None:
        raise ValueError("start/end must be datetime, ISO string, or unix timestamp (sec/ms/us)")
    if e < s:
        raise ValueError("end must be >= start")
    return int(s), int(e)


def _split_range_us_24h(start_us: int, end_us: int) -> List[Tuple[int, int]]:
    """
    Split [start_us, end_us] into chunks where each chunk <= 24h.
    """
    max_span = int(dt.timedelta(hours=24).total_seconds() * 1_000_000)
    out: List[Tuple[int, int]] = []
    cur = int(start_us)
    while cur <= int(end_us):
        chunk_end = min(int(end_us), cur + max_span - 1)
        out.append((cur, chunk_end))
        cur = chunk_end + 1
    return out


def _normalize_download_links(payload: Any) -> List[Dict[str, Any]]:
    """
    backend: { status, data: { links: [ {path, download_url, minute}, ... ] } }
    """
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    links = data.get("links")
    if not isinstance(links, list):
        return []
    return [x for x in links if isinstance(x, dict)]


def _infer_entry_type_from_path(path: Any) -> Optional[str]:
    if not path:
        return None
    p = str(path).lower()
    if "alpha_record_" in p:
        return "alpha"
    if "record_" in p:
        return "data"
    return None


def _local_yyyymmdd(ts_ms: int, tz: dt.tzinfo) -> int:
    d = dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc).astimezone(tz).date()
    return d.year * 10000 + d.month * 100 + d.day


def _cursor_end_of_day_utc(yyyymmdd: int, tz: dt.tzinfo) -> str:
    """
    Given local date (yyyymmdd) in tz, return UTC ISO cursor string at that day's 23:59:59.999 local time.
    """
    y = int(yyyymmdd) // 10000
    m = (int(yyyymmdd) // 100) % 100
    d = int(yyyymmdd) % 100

    local_dt = dt.datetime(y, m, d, 23, 59, 59, 999000, tzinfo=tz)
    utc_dt = local_dt.astimezone(dt.timezone.utc)
    return utc_dt.isoformat().replace("+00:00", "Z")


def _ensure_0x(hex_str: str) -> str:
    if not isinstance(hex_str, str):
        hex_str = str(hex_str)
    hex_str = hex_str.strip()
    if not hex_str.startswith("0x"):
        return "0x" + hex_str
    return hex_str


def _strip_0x(hex_str: str) -> str:
    if not isinstance(hex_str, str):
        hex_str = str(hex_str)
    hex_str = hex_str.strip()
    if hex_str.startswith("0x"):
        return hex_str[2:]
    return hex_str


def _is_nan(v: Any) -> bool:
    return isinstance(v, float) and math.isnan(v)


# ✅ V2 additions: ws url helper (no impact on existing logic)
def _to_ws_url(api_base: str) -> str:
    """
    https://api.xxx -> wss://api.xxx
    http://localhost:8080 -> ws://localhost:8080
    """
    b = (api_base or "").strip()
    if b.startswith("https://"):
        return "wss://" + b[len("https://") :]
    if b.startswith("http://"):
        return "ws://" + b[len("http://") :]
    return b


# ----------------------------
# Client
# ----------------------------
class LiberalAlphaClient:
    """
    API client (no local runner required).

    Auth model:
      - For upload endpoints: API key (X-API-Key).
      - For entries download endpoint (/api/entries/v2/...): Authorization: Bearer <JWT>.
      - This client can auto-get JWT via POST /api/users/auth using your private key.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key: Optional[str] = None,
        api_base: str = DEFAULT_API_BASE,
        timeout: int = 30,
        # ✅ V2 additions: runner compat (optional; defaults keep old behavior)
        host: Optional[str] = None,
        port: Optional[int] = None,
        base_url: Optional[str] = None,
        # HTTP behavior: whether to respect environment / system proxy settings (WinINET)
        # In some corporate networks, system proxy can break TLS for Python requests (EOF).
        trust_env: Optional[bool] = None,
    ):
        # ✅ keep existing behavior: api_base default stays, but allow base_url override for v2 script
        if base_url:
            api_base = base_url

        self.api_key = api_key or os.getenv("LIBALPHA_API_KEY")
        self.private_key = _normalize_private_key(private_key or os.getenv("LIBALPHA_PRIVATE_KEY"))
        self.api_base = (api_base or DEFAULT_API_BASE).rstrip("/")
        self.timeout = timeout

        # ----------------------------
        # HTTP session (for connection reuse + optional proxy bypass)
        # ----------------------------
        if trust_env is None:
            # Default: respect env/system proxy, but allow disabling via env var.
            # LIBALPHA_HTTP_TRUST_ENV=0 => disable
            trust_env = os.getenv("LIBALPHA_HTTP_TRUST_ENV", "1") != "0"
        self._http_trust_env = bool(trust_env)
        self._http = requests.Session()
        self._http.trust_env = self._http_trust_env

        # ✅ runner fields (not used unless you call send_data)
        self.runner_host = host or os.getenv("LIBALPHA_RUNNER_HOST", "127.0.0.1")
        self.runner_port = int(port or os.getenv("LIBALPHA_RUNNER_PORT", "8128"))

        self.wallet: Optional[str] = None
        if self.private_key:
            self.wallet = get_wallet_address(self.private_key)
            logger.info("Wallet address derived: %s", self.wallet)

        self._jwt_token: Optional[str] = None
        self._jwt_obtained_at: Optional[float] = None
        self._auth_scheme_used: Optional[str] = None

        # ----------------------------
        # Minimal HTTP retry policy
        # ----------------------------
        # Retry ONCE for transient backend/network issues:
        # - status: 502/503/504
        # - network: timeout / connection error
        self._http_retry_503 = int(os.getenv("LIBALPHA_HTTP_RETRY_503", "1"))
        self._http_retry_timeout = int(os.getenv("LIBALPHA_HTTP_RETRY_TIMEOUT", "1"))
        self._http_retry_sleep = float(os.getenv("LIBALPHA_HTTP_RETRY_SLEEP", "1.0"))
        self._http_retry_jitter = float(os.getenv("LIBALPHA_HTTP_RETRY_JITTER", "0.5"))

        # Upload defaults (do NOT expose in public method signature)
        self._upload_chunk_size = int(os.getenv("LIBALPHA_UPLOAD_CHUNK_SIZE", str(1024 * 1024)))  # 1MB
        # align with "retry at most once" preference by default
        self._upload_max_retries = int(os.getenv("LIBALPHA_UPLOAD_MAX_RETRIES", "1"))
        self._upload_resume = os.getenv("LIBALPHA_UPLOAD_RESUME", "1") != "0"
        self._upload_timeout = int(os.getenv("LIBALPHA_UPLOAD_TIMEOUT", "60"))

        # Optional batch_id via env (since public API has only 2 args)
        env_batch = os.getenv("LIBALPHA_UPLOAD_BATCH_ID", "").strip()
        self._upload_batch_id: Optional[int] = int(env_batch) if env_batch.isdigit() else None

        # Session cache for real resume across process restarts
        self._upload_cache_path = Path(
            os.getenv("LIBALPHA_UPLOAD_CACHE_PATH", str(Path.home() / ".libalpha_upload_sessions.json"))
        )

    def _is_retryable_status(self, code: int) -> bool:
        return code in (502, 503, 504)

    def _sleep_before_retry(self, attempt: int) -> None:
        # attempt: 0 for first retry
        time.sleep(self._http_retry_sleep + random.random() * self._http_retry_jitter)

    # ----------------------------
    # Auth: get JWT via /api/users/auth
    # ----------------------------
    def _build_auth_candidates(self, wallet_checksum: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Return list of (scheme_name, payload) to try.
        Compatible variants:
          - wallet checksum vs lowercase
          - signature with 0x vs without 0x
          - timestamp in seconds vs milliseconds
          - personal_sign(text=timestamp or template)
        """
        now_sec = int(time.time())
        now_ms = int(time.time() * 1000)

        ts_candidates = [str(now_sec), str(now_ms)]
        msg_tmpl = os.getenv("LIBALPHA_AUTH_MSG_TEMPLATE", "{timestamp}")

        def sign_personal(message_text: str) -> str:
            msg = encode_defunct(text=message_text)
            signed = Account.sign_message(msg, private_key=self.private_key)  # type: ignore[arg-type]
            return signed.signature.hex()

        candidates: List[Tuple[str, Dict[str, Any]]] = []
        seen = set()

        for ts in ts_candidates:
            message_text = msg_tmpl.format(timestamp=ts, wallet=wallet_checksum)

            sig = sign_personal(message_text)
            sig_with_0x = _ensure_0x(sig)
            sig_no_0x = _strip_0x(sig_with_0x)

            for wallet_variant in [wallet_checksum, wallet_checksum.lower()]:
                for sig_variant, sig_tag in [(sig_with_0x, "sig_0x"), (sig_no_0x, "sig_no0x")]:
                    scheme = f"personal_sign(msg='{message_text}', ts='{ts}', wallet='{wallet_variant}', {sig_tag})"
                    payload = {
                        "wallet_address": wallet_variant,
                        "signature": sig_variant,
                        "timestamp": ts,
                        "metadata": {
                            "sdk": "liberal_alpha_python_sdk",
                            "auth_scheme": scheme,
                        },
                    }
                    key = (payload["wallet_address"], payload["signature"], payload["timestamp"])
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append((scheme, payload))

        return candidates

    def _ensure_jwt(self, force_refresh: bool = False) -> str:
        if self._jwt_token and not force_refresh:
            return self._jwt_token

        if not self.private_key:
            raise ConfigurationError("Missing private_key (LIBALPHA_PRIVATE_KEY). Entries download needs JWT.")

        wallet_checksum = Account.from_key(self.private_key).address
        self.wallet = wallet_checksum
        logger.info("Wallet address derived: %s", self.wallet)

        url = f"{self.api_base}{AUTH_PATH}"
        candidates = self._build_auth_candidates(wallet_checksum)

        last_401_text = None

        for scheme, payload in candidates:
            try:
                msg_tmpl = os.getenv("LIBALPHA_AUTH_MSG_TEMPLATE", "{timestamp}")
                message_text = msg_tmpl.format(timestamp=payload["timestamp"], wallet=wallet_checksum)
                msg = encode_defunct(text=message_text)
                sig_local = _ensure_0x(payload["signature"])
                recovered = Account.recover_message(msg, signature=sig_local)
                if recovered.lower() != wallet_checksum.lower():
                    logger.debug("Skip scheme (local recover mismatch): %s recovered=%s", scheme, recovered)
                    continue
            except Exception as e:
                logger.debug("Skip scheme (local check error): %s err=%s", scheme, e)
                continue

            # --- POST with minimal retry (once) for transient failures ---
            resp = None
            net_retry_used = 0
            status_retry_used = 0
            while True:
                try:
                    resp = requests.post(url, json=payload, timeout=self.timeout, headers={"Accept": "application/json"})
                except (requests.Timeout, requests.ConnectionError) as e:
                    if net_retry_used < self._http_retry_timeout:
                        net_retry_used += 1
                        logger.warning(
                            "Auth network/timeout error: %s. retry=%s/%s",
                            e,
                            net_retry_used,
                            self._http_retry_timeout,
                        )
                        self._sleep_before_retry(net_retry_used - 1)
                        continue
                    raise RequestError(f"Auth request failed: {e}") from e
                except requests.RequestException as e:
                    raise RequestError(f"Auth request failed: {e}") from e

                if (
                    resp is not None
                    and self._is_retryable_status(resp.status_code)
                    and status_retry_used < self._http_retry_503
                ):
                    status_retry_used += 1
                    logger.warning(
                        "Auth HTTP %s: %s. retry=%s/%s",
                        resp.status_code,
                        resp.text.strip()[:200],
                        status_retry_used,
                        self._http_retry_503,
                    )
                    self._sleep_before_retry(status_retry_used - 1)
                    continue
                break

            assert resp is not None

            if resp.status_code == 401:
                last_401_text = resp.text.strip()
                logger.debug("Auth 401 with scheme: %s, resp=%s", scheme, last_401_text[:300])
                continue

            if resp.status_code >= 400:
                raise RequestError(f"Auth HTTP {resp.status_code}: {resp.text.strip()}")

            try:
                data = resp.json()
            except Exception:
                raise RequestError(f"Auth response not JSON: {resp.text[:200]}")

            token = None
            if isinstance(data, dict):
                d = data.get("data")
                if isinstance(d, dict):
                    token = d.get("token") or d.get("jwt") or d.get("access_token")
                if token is None and "token" in data:
                    token = data.get("token")

            if not token:
                raise RequestError(f"Auth succeeded but no token in response: {data}")

            self._jwt_token = token
            self._jwt_obtained_at = time.time()
            self._auth_scheme_used = scheme
            logger.info("JWT token obtained via /api/users/auth (scheme=%s)", scheme)
            return token

        raise RequestError(
            "Auth HTTP 401: Invalid signature for all tried signing variants. "
            f"Last 401 response: {last_401_text or ''}".strip()
        )

    # ----------------------------
    # HTTP helpers
    # ----------------------------
    def _headers_api_key(self) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    def _headers_bearer(self) -> Dict[str, str]:
        token = self._ensure_jwt()
        return {"Accept": "application/json", "Authorization": f"Bearer {token}"}

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        auth: str = "bearer",  # "bearer" or "api_key" or "none"
        _retry: bool = True,
    ) -> Any:
        url = f"{self.api_base}{path}"

        if auth == "bearer":
            headers = self._headers_bearer()
        elif auth == "api_key":
            headers = self._headers_api_key()
            if not self.api_key:
                raise ConfigurationError("Missing api_key (LIBALPHA_API_KEY).")
        else:
            headers = {"Accept": "application/json"}

        max_status_retries = self._http_retry_503 if _retry else 0
        max_net_retries = self._http_retry_timeout if _retry else 0

        status_retry_used = 0
        net_retry_used = 0

        while True:
            try:
                resp = self._http.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self.timeout,
                )
            except (requests.Timeout, requests.ConnectionError) as e:
                if net_retry_used < max_net_retries:
                    net_retry_used += 1
                    logger.warning(
                        "HTTP network/timeout error (%s %s): %s. retry=%s/%s",
                        method,
                        url,
                        e,
                        net_retry_used,
                        max_net_retries,
                    )
                    self._sleep_before_retry(net_retry_used - 1)
                    continue
                raise RequestError(f"HTTP request failed: {e}") from e
            except requests.RequestException as e:
                raise RequestError(f"HTTP request failed: {e}") from e

            # bearer 401 => refresh once
            if resp.status_code == 401 and auth == "bearer" and _retry:
                self._ensure_jwt(force_refresh=True)
                return self._request(method, path, params=params, json_body=json_body, auth=auth, _retry=False)

            # retry once for 502/503/504
            if self._is_retryable_status(resp.status_code) and status_retry_used < max_status_retries:
                status_retry_used += 1
                logger.warning(
                    "HTTP %s from %s %s: %s. retry=%s/%s",
                    resp.status_code,
                    method,
                    url,
                    resp.text.strip()[:200],
                    status_retry_used,
                    max_status_retries,
                )
                self._sleep_before_retry(status_retry_used - 1)
                continue

            if resp.status_code >= 400:
                raise RequestError(f"HTTP {resp.status_code}: {resp.text.strip()}")

            ct = resp.headers.get("Content-Type", "")
            if "application/json" in ct:
                try:
                    return resp.json()
                except Exception:
                    return resp.text

            try:
                return resp.json()
            except Exception:
                return resp.text

    # ----------------------------
    # Records endpoint (optional)
    # ----------------------------
    def my_records(self) -> Any:
        return self._request("GET", "/api/records", auth="api_key")

    # ✅ V2 additions: subscriptions (does not alter any existing behavior)
    def my_subscriptions(self) -> Any:
        last_err: Optional[Exception] = None
        for path in SUBSCRIPTIONS_CANDIDATE_PATHS:
            # subscriptions通常更像“用户态”，优先 bearer
            for auth in ("bearer", "api_key"):
                try:
                    return self._request("GET", path, auth=auth)
                except Exception as e:
                    last_err = e
                    continue
        raise RequestError(f"Cannot fetch subscriptions. Tried paths={SUBSCRIPTIONS_CANDIDATE_PATHS}. Last error={last_err}")

    # ----------------------------
    # Download helpers: get symbols
    # ----------------------------
    def _get_symbols_via_without_entries(self, record_id: int) -> List[str]:
        payload = self._request(
            "GET",
            WITHOUT_ENTRIES_PATH,
            params={"record_id": int(record_id)},
            auth="bearer",
        )

        if not isinstance(payload, dict):
            return []

        data = payload.get("data")
        if not isinstance(data, dict):
            return []

        record = data.get("record")
        if isinstance(record, dict):
            syms = record.get("symbols")
            if isinstance(syms, list):
                return [str(s).strip() for s in syms if str(s).strip()]

            sd = record.get("symbol_data")
            if isinstance(sd, dict):
                return [str(k).strip() for k in sd.keys() if str(k).strip()]

        syms = data.get("symbols")
        if isinstance(syms, list):
            return [str(s).strip() for s in syms if str(s).strip()]

        return []

    # ----------------------------
    # Extract entries
    # ----------------------------
    def _extract_entries(self, payload: Any) -> List[Dict[str, Any]]:
        """
        Supports both:
          data.entries = [ {...}, {...} ]
          data.entries = { "SYM": [ {...}, {...} ], ... }
        """
        if payload is None:
            return []
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if not isinstance(payload, dict):
            return []

        data = payload.get("data")

        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]

        if isinstance(data, dict):
            v = data.get("entries")

            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]

            if isinstance(v, dict):
                out: List[Dict[str, Any]] = []
                for sym, arr in v.items():
                    if isinstance(arr, list):
                        for item in arr:
                            if isinstance(item, dict):
                                if "symbol" not in item and isinstance(sym, str):
                                    item = dict(item)
                                    item["symbol"] = sym
                                out.append(item)
                return out

        return []

    # ----------------------------
    # Entry -> row
    # ----------------------------
    def _entry_to_row(
        self,
        e: Dict[str, Any],
        *,
        record_id: int,
        tz: dt.tzinfo,
        decrypt_if_needed: bool,
    ) -> Dict[str, Any]:
        symbol = e.get("symbol") or e.get("target_asset") or e.get("asset") or ""

        ts_ms = (
            _guess_timestamp_ms(e.get("timestamp_ms"))
            or _guess_timestamp_ms(e.get("timestamp"))
            or _guess_timestamp_ms(e.get("time"))
            or _guess_timestamp_ms(e.get("created_at"))
        ) or 0

        utc_dt = dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc) if ts_ms else None
        local_dt = utc_dt.astimezone(tz) if utc_dt else None
        local_date = _local_yyyymmdd(ts_ms, tz) if ts_ms else None

        batch_id = e.get("batch_id") or e.get("batchId")

        plain_data: Dict[str, Any] = {}
        encrypted_payload = None

        if isinstance(e.get("data"), dict):
            plain_data = e["data"]
        elif isinstance(e.get("data"), str):
            encrypted_payload = e["data"]
        else:
            for k in ("encrypted_data", "encryptedData", "encrypted_payload", "encryptedPayload"):
                if k in e:
                    encrypted_payload = e.get(k)
                    break

        decrypted_obj = None
        if encrypted_payload is not None and decrypt_if_needed and self.private_key:
            decrypted_obj = decrypt_alpha_message(self.private_key, encrypted_payload)
            if isinstance(decrypted_obj, dict):
                plain_data = decrypted_obj

        return {
            "record_id": record_id,
            "symbol": symbol,
            "timestamp_ms": ts_ms,
            "datetime_utc": utc_dt.isoformat() if utc_dt else None,
            "datetime_local": local_dt.isoformat() if local_dt else None,
            "local_date": local_date,
            "batch_id": batch_id,
            "is_encrypted": encrypted_payload is not None,
            "decrypt_ok": isinstance(decrypted_obj, dict) if encrypted_payload is not None else None,
            "data": plain_data if isinstance(plain_data, dict) else {},
            "raw_entry": e,
        }

    # ----------------------------
    # Public API: download_data()
    # ----------------------------
    def download_data(
        self,
        record_id: int,
        symbols: List[str],
        dates: List[int],
        tz_info: Union[dt.tzinfo, str, int, float] = "Asia/Singapore",
        *,
        size: int = 500,
        max_pages: int = 2000,
        cursor: Optional[str] = None,
        decrypt_if_needed: bool = True,
        auto_symbols: bool = True,
        fetch_all: bool = True,  # ✅ default fetch all
    ):
        _ensure_pandas()

        if record_id <= 0:
            raise ValueError("record_id must be positive int")

        tz = _normalize_tz(tz_info)

        sym_list = [s.strip() for s in (symbols or []) if isinstance(s, str) and s.strip()]
        sym_set = set(sym_list)
        date_set = set(int(d) for d in (dates or []))

        if auto_symbols and not sym_list:
            fetched = self._get_symbols_via_without_entries(record_id)
            sym_list = fetched
            sym_set = set(sym_list)

        # -------------------------
        # Decide query plan
        # -------------------------
        manual_cursor = cursor.strip() if isinstance(cursor, str) and cursor.strip() else None

        # If user supplies cursor: one run, filter by date_set if provided.
        # If user supplies dates but NOT cursor: run per-date with cursor = end-of-day of that date (in tz).
        # Otherwise: one run starting from now() cursor.
        runs: List[Tuple[Optional[int], str, set[int]]] = []

        if manual_cursor:
            start_cur = manual_cursor
            runs.append((None, start_cur, date_set))
        elif date_set:
            # ✅ per-date runs (prevents "one busy day blocks other days")
            for d in sorted(date_set, reverse=True):
                runs.append((d, _cursor_end_of_day_utc(d, tz), {d}))
        else:
            runs.append((None, _utc_iso_z(), set()))

        rows: List[Dict[str, Any]] = []

        # -------------------------
        # Execute runs
        # -------------------------
        for target_date, start_cursor, run_date_set in runs:
            cur = start_cursor

            page = 0
            seen_cursors: set[str] = set()

            while True:
                # Only enforce max_pages when fetch_all is False
                if (not fetch_all) and page >= int(max_pages):
                    break

                if not cur or cur in seen_cursors:
                    break
                seen_cursors.add(cur)

                params: Dict[str, Any] = {
                    "record_id": int(record_id),
                    "size": int(size),
                    "cursor": cur,
                }
                if sym_list:
                    params["symbol"] = ",".join(sym_list)

                payload = self._request("GET", ENTRIES_PATH, params=params, auth="bearer")
                entries = self._extract_entries(payload)

                if not entries:
                    break

                batch_oldest_dt: Optional[dt.datetime] = None
                batch_oldest_ms: Optional[int] = None
                batch_min_local_date: Optional[int] = None

                for e in entries:
                    row = self._entry_to_row(e, record_id=record_id, tz=tz, decrypt_if_needed=decrypt_if_needed)

                    # symbol filter
                    if sym_set:
                        sym = (row.get("symbol") or "").strip()
                        if sym and sym not in sym_set:
                            continue

                    # date filter (per-run)
                    if run_date_set:
                        yyyymmdd = row.get("local_date")
                        if yyyymmdd not in run_date_set:
                            continue

                    rows.append(row)

                    # Track oldest cursor candidates
                    ca = e.get("created_at")
                    ca_dt = _parse_iso_any(ca) if isinstance(ca, str) else None
                    if ca_dt:
                        if batch_oldest_dt is None or ca_dt < batch_oldest_dt:
                            batch_oldest_dt = ca_dt

                    tms = _guess_timestamp_ms(e.get("timestamp")) or _guess_timestamp_ms(e.get("timestamp_ms"))
                    if tms:
                        if batch_oldest_ms is None or tms < batch_oldest_ms:
                            batch_oldest_ms = tms

                    # Track min local_date in this page (for per-date stop)
                    ld = row.get("local_date")
                    if isinstance(ld, int):
                        if batch_min_local_date is None or ld < batch_min_local_date:
                            batch_min_local_date = ld

                # compute next cursor
                next_cursor = None
                if batch_oldest_dt:
                    batch_oldest_dt = batch_oldest_dt.astimezone(dt.timezone.utc) - dt.timedelta(milliseconds=1)
                    next_cursor = batch_oldest_dt.isoformat().replace("+00:00", "Z")
                elif batch_oldest_ms:
                    odt = dt.datetime.fromtimestamp(batch_oldest_ms / 1000.0, tz=dt.timezone.utc) - dt.timedelta(
                        milliseconds=1
                    )
                    next_cursor = odt.isoformat().replace("+00:00", "Z")

                # If we are doing a per-date run and this page already crossed into earlier date, stop this run.
                if target_date is not None and batch_min_local_date is not None and batch_min_local_date < int(target_date):
                    break

                if not next_cursor or next_cursor == cur:
                    break
                cur = next_cursor

                # If server returned fewer than requested, no more pages.
                if len(entries) < int(size):
                    break

                page += 1

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        if "data" in df.columns:
            data_df = pd.json_normalize(df["data"].apply(lambda x: x if isinstance(x, dict) else {}))
            for c in list(data_df.columns):
                if c in df.columns:
                    data_df.rename(columns={c: f"data.{c}"}, inplace=True)
            df = df.drop(columns=["data"]).reset_index(drop=True)
            df = pd.concat([df, data_df], axis=1)

        return df

    # ----------------------------
    # Public API: download_history_data() (protobuf length-prefixed)
    # ----------------------------
    def download_history_data(
        self,
        *,
        record_id: int,
        symbol: str,
        start: Union[int, float, str, dt.datetime],
        end: Union[int, float, str, dt.datetime],
        dedupe: bool = True,
        include_datetime_cols: bool = True,
    ):
        """
        Download historical data by time range using /api/entries/download-links.

        Backend constraint: end-start must be <= 24h, so this method auto-splits
        the requested range and merges results locally.

        Params:
          - record_id: int
          - symbol: str
          - start/end: datetime | ISO string | unix timestamp (sec/ms/us)
        Returns:
            pandas.DataFrame
        """
        _ensure_pandas()

        if record_id <= 0:
            raise ValueError("record_id must be positive int")
        sym = (symbol or "").strip()
        if not sym:
            raise ValueError("symbol is required")
        # choose auth: backend uses CombinedAuthMiddleware (JWT or API key)
        if self.private_key:
            auth = "bearer"
        elif self.api_key:
            auth = "api_key"
        else:
            raise ConfigurationError("Missing private_key or api_key. download_history_data needs auth.")

        start_us, end_us = _normalize_time_range_us(start, end)
        chunks = _split_range_us_24h(start_us, end_us)

        try:
            from .proto import data_entry_pb2
        except Exception as e:
            raise ConfigurationError(
                "Cannot import data_entry_pb2. Ensure SDK package includes liberal_alpha/proto/data_entry_pb2.py "
                "and protobuf>=5.29.0 is installed."
            ) from e

        entry_type = "data"
        try:
            rec_payload = self._request("GET", f"/api/records/{int(record_id)}", auth=auth)
            if isinstance(rec_payload, dict):
                rec_data = rec_payload.get("data")
                if isinstance(rec_data, dict):
                    rec_type = rec_data.get("type")
                    if isinstance(rec_type, str):
                        if rec_type.lower() == "alpha":
                            entry_type = "alpha"
                        elif rec_type.lower() == "data":
                            entry_type = "data"
        except Exception:
            pass

        msg_cls = data_entry_pb2.DataEntry if entry_type == "data" else data_entry_pb2.AlphaEntry

        # Use the same session to keep consistent trust_env behavior (proxy/no-proxy)
        session = self._http
        dl_timeout = max(int(self.timeout), 60)

        rows: List[Dict[str, Any]] = []
        seen_entry_ids: set[int] = set()

        for s_us, e_us in chunks:
            payload = self._request(
                "GET",
                ENTRY_DOWNLOAD_LINKS_PATH,
                params={
                    "record_id": int(record_id),
                    "symbol": sym,
                    "start_timestamp": int(s_us),
                    "end_timestamp": int(e_us),
                },
                auth=auth,
            )

            links = _normalize_download_links(payload)
            if not links:
                continue

            # Fallback: infer entry type from download path prefix if needed.
            if entry_type == "data":
                for item in links:
                    inferred = _infer_entry_type_from_path(item.get("path"))
                    if inferred in ("data", "alpha"):
                        entry_type = inferred
                        msg_cls = data_entry_pb2.DataEntry if entry_type == "data" else data_entry_pb2.AlphaEntry
                        break

            for item in links:
                download_url = item.get("download_url")
                path = item.get("path")
                if not download_url:
                    continue

                resp = session.get(str(download_url), timeout=dl_timeout)
                if resp.status_code >= 400:
                    raise RequestError(f"Failed to download file: HTTP {resp.status_code} path={path}")

                messages = parse_length_prefixed_messages(resp.content, msg_cls)
                for msg in messages:
                    if entry_type == "data":
                        d = {
                            "entry_id": int(getattr(msg, "entry_id", 0)),
                            "record_id": int(getattr(msg, "record_id", 0)),
                            "symbol": str(getattr(msg, "symbol", "")),
                            "features": dict(getattr(msg, "features", {})),
                            "timestamp": int(getattr(msg, "timestamp", 0)),
                            "runner_timestamp": int(getattr(msg, "runner_timestamp", 0)),
                            "server_timestamp": int(getattr(msg, "server_timestamp", 0)),
                            "commitment": str(getattr(msg, "commitment", "")),
                            "request_id": str(getattr(msg, "request_id", "")),
                            "batch_id": int(getattr(msg, "batch_id", 0)),
                        }
                    else:
                        d = {
                            "entry_id": int(getattr(msg, "entry_id", 0)),
                            "record_id": int(getattr(msg, "record_id", 0)),
                            "symbol": str(getattr(msg, "symbol", "")),
                            "alpha": float(getattr(msg, "alpha", 0.0)),
                            "timestamp": int(getattr(msg, "timestamp", 0)),
                            "runner_timestamp": int(getattr(msg, "runner_timestamp", 0)),
                            "server_timestamp": int(getattr(msg, "server_timestamp", 0)),
                            "request_id": str(getattr(msg, "request_id", "")),
                            "batch_id": int(getattr(msg, "batch_id", 0)),
                        }

                    if path:
                        d["source_path"] = str(path)

                    # optional dedupe (safe when ranges overlap or backend returns duplicates)
                    if dedupe:
                        eid = int(d.get("entry_id") or 0)
                        if eid and eid in seen_entry_ids:
                            continue
                        if eid:
                            seen_entry_ids.add(eid)

                    rows.append(d)

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        if include_datetime_cols:
            # microseconds -> datetime
            for c in ("timestamp", "runner_timestamp", "server_timestamp"):
                if c in df.columns:
                    df[f"{c}_dt"] = pd.to_datetime(df[c], unit="us", utc=True, errors="coerce")

        return df

    # ============================================================
    # Historical Upload API (Public): upload_data(record_id, df)->bool
    # ============================================================
    def upload_data(self, record_id: int, df) -> bool:
        """
        Historical Upload API (Python)

        Public interface: ONLY (record_id, df) -> bool

        Accept TWO dataframe formats:

        Format B (recommended):
          columns: record_id, symbol, timestamp, <any other columns...>
          All extra columns will be packed into data(dict) automatically.

        Format A (also supported):
          columns: record_id, symbol, timestamp, data(dict)

        Auth: api_key (X-API-Key)
        """
        try:
            _ensure_pandas()
            _ensure_msgpack()

            if record_id <= 0:
                raise ValueError("record_id must be positive int")

            if not self.api_key:
                raise ConfigurationError("Missing api_key (LIBALPHA_API_KEY). Upload needs X-API-Key.")

            if df is None or getattr(df, "empty", True):
                logger.info("upload_data: empty dataframe, nothing to upload.")
                return True

            compressed, checksum, total_size, meta = self._prepare_compressed_payload(record_id, df)
            batch_id = meta.get("batch_id")

            # resume via local cache (keyed by record_id + checksum)
            session_id = None
            if self._upload_resume:
                session_id = self._load_cached_session_id(record_id, checksum)

            if session_id:
                logger.info("upload_data: resume with cached session_id=%s", session_id)

            # if no session => create new session
            if not session_id:
                session_id = self._upload_create_session(total_size=total_size, checksum=checksum, metadata=meta)
                if self._upload_resume:
                    self._save_cached_session_id(record_id, checksum, session_id)

            ok = self._upload_data_internal(
                session_id=session_id,
                compressed_data=compressed,
                checksum=checksum,
                record_id=record_id,
                batch_id=batch_id,
            )

            if ok and self._upload_resume:
                self._delete_cached_session_id(record_id, checksum)

            return ok

        except Exception as e:
            logger.error("upload_data failed: %s", e)
            return False

    # ----------------------------
    # Upload internals
    # ----------------------------
    def _prepare_compressed_payload(self, record_id: int, df) -> Tuple[bytes, str, int, Dict[str, Any]]:
        """
        Base required columns:
          - record_id
          - symbol
          - timestamp

        Then:
          - If `data` column exists (dict or JSON string), use as base_data.
          - Any extra columns (except batch_id) will be packed into data dict.
          - Merge policy: extra columns override keys in `data`.
        """
        base_required = {"record_id", "symbol", "timestamp"}
        missing = [c for c in base_required if c not in df.columns]
        if missing:
            raise ValueError(f"DataFrame missing columns: {missing}. Required: {sorted(base_required)}")

        # batch_id: from df['batch_id'] (single value) OR env LIBALPHA_UPLOAD_BATCH_ID
        batch_id: Optional[int] = None
        if "batch_id" in df.columns:
            vals = [v for v in df["batch_id"].dropna().unique().tolist()]
            if len(vals) == 1:
                try:
                    batch_id = int(vals[0])
                except Exception:
                    batch_id = None
        if batch_id is None:
            batch_id = self._upload_batch_id

        # Validate record_id consistency
        unique_rids = [int(x) for x in df["record_id"].dropna().unique().tolist()]
        if unique_rids and (len(unique_rids) != 1 or unique_rids[0] != int(record_id)):
            raise ValueError(f"DataFrame record_id mismatch: df has {unique_rids}, but argument record_id={record_id}.")

        reserved = {"record_id", "symbol", "timestamp", "batch_id"}
        has_data_col = "data" in df.columns
        extra_cols = [c for c in df.columns if c not in reserved and c != "data"]

        if (not has_data_col) and (not extra_cols):
            raise ValueError("DataFrame must contain either a 'data' column (dict/JSON) OR extra columns to pack into data.")

        items: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            rid = int(row["record_id"])
            sym = str(row["symbol"])
            ts_ms = _guess_timestamp_ms(row["timestamp"]) or 0

            base_data: Dict[str, Any] = {}

            if has_data_col:
                v = row["data"]
                if isinstance(v, dict):
                    base_data = dict(v)
                elif v is None or _is_nan(v):
                    base_data = {}
                elif isinstance(v, str) and v.strip():
                    try:
                        parsed = json.loads(v)
                        base_data = dict(parsed) if isinstance(parsed, dict) else {}
                    except Exception:
                        base_data = {}
                else:
                    base_data = {}

            if extra_cols:
                extra_data: Dict[str, Any] = {}
                for c in extra_cols:
                    val = row[c]
                    if val is None or _is_nan(val):
                        continue
                    try:
                        if hasattr(val, "item"):
                            val = val.item()
                    except Exception:
                        pass
                    extra_data[c] = val

                if extra_data:
                    merged = dict(base_data)
                    merged.update(extra_data)  # extra overrides base
                    base_data = merged

            items.append({"record_id": rid, "symbol": sym, "data": base_data, "timestamp": ts_ms})

        meta = {
            "record_id": int(record_id),
            "batch_id": batch_id,
            "total_records": len(items),
            "compression": "msgpack+gzip",
            "created_at": int(time.time() * 1000),
            "sdk": "liberal_alpha_python_sdk",
        }

        payload = {"batch_id": batch_id, "items": items, "metadata": meta}

        raw = msgpack.packb(payload, use_bin_type=True)  # type: ignore[union-attr]
        compressed = gzip.compress(raw, compresslevel=6)
        checksum = hashlib.sha256(compressed).hexdigest()
        total_size = len(compressed)

        logger.info(
            "Prepared upload payload: records=%s raw=%sB compressed=%sB ratio=%.1f%% batch_id=%s",
            len(items),
            len(raw),
            len(compressed),
            (len(compressed) / max(len(raw), 1)) * 100.0,
            batch_id,
        )

        return compressed, checksum, total_size, meta

    def _upload_data_internal(
        self,
        *,
        session_id: str,
        compressed_data: bytes,
        checksum: str,
        record_id: int,
        batch_id: Optional[int],
    ) -> bool:
        chunk_size = int(self._upload_chunk_size)
        max_retries = int(self._upload_max_retries)
        timeout = int(self._upload_timeout)

        total_size = len(compressed_data)
        total_chunks = int(math.ceil(total_size / chunk_size)) if total_size > 0 else 0
        logger.info("Uploading %s bytes in %s chunks (chunk_size=%s)", total_size, total_chunks, chunk_size)

        uploaded_chunks: set[int] = set()
        if self._upload_resume:
            try:
                prog = self._upload_get_progress(session_id, timeout=timeout)
                uploaded_chunks = set(int(x) for x in (prog.get("uploaded_chunks") or []))
                logger.info("Resume info: %s/%s chunks already uploaded", len(uploaded_chunks), total_chunks)
            except Exception as e:
                logger.warning("Progress query failed (session_id=%s): %s. Will recreate session.", session_id, e)
                session_id = self._upload_create_session(
                    total_size=total_size,
                    checksum=checksum,
                    metadata={
                        "record_id": int(record_id),
                        "batch_id": batch_id,
                        "total_records": None,
                        "compression": "msgpack+gzip",
                        "created_at": int(time.time() * 1000),
                        "sdk": "liberal_alpha_python_sdk",
                    },
                )
                if self._upload_resume:
                    self._save_cached_session_id(record_id, checksum, session_id)
                uploaded_chunks = set()

        for idx in range(total_chunks):
            if self._upload_resume and idx in uploaded_chunks:
                logger.info("Chunk %s already uploaded, skipping (resume)", idx)
                continue

            start = idx * chunk_size
            end = min(start + chunk_size, total_size)
            chunk = compressed_data[start:end]
            chunk_checksum = hashlib.sha256(chunk).hexdigest()
            is_last = idx == total_chunks - 1

            ok = False
            for attempt in range(max_retries):
                if self._upload_chunk(
                    session_id=session_id,
                    chunk_index=idx,
                    chunk_data=chunk,
                    chunk_checksum=chunk_checksum,
                    is_last=is_last,
                    timeout=timeout,
                ):
                    ok = True
                    break
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    logger.info("Retry chunk %s in %ss ...", idx, wait)
                    time.sleep(wait)

            if not ok:
                logger.error("Failed to upload chunk %s after %s attempts (session_id=%s)", idx, max_retries, session_id)
                return False

            logger.info("Upload progress: %.1f%% (%s/%s)", (idx + 1) / total_chunks * 100, idx + 1, total_chunks)

        return self._upload_finalize(session_id, timeout=timeout)

    def _upload_create_session(self, *, total_size: int, checksum: str, metadata: Dict[str, Any]) -> str:
        url = f"{self.api_base}{UPLOAD_CREATE_PATH}"
        headers = self._headers_api_key()

        net_retry_used = 0
        status_retry_used = 0

        while True:
            try:
                resp = requests.post(
                    url,
                    json={"total_size": int(total_size), "checksum": checksum, "metadata": metadata},
                    headers=headers,
                    timeout=self.timeout,
                )
            except (requests.Timeout, requests.ConnectionError) as e:
                if net_retry_used < self._http_retry_timeout:
                    net_retry_used += 1
                    logger.warning(
                        "Create upload session network/timeout error: %s. retry=%s/%s",
                        e,
                        net_retry_used,
                        self._http_retry_timeout,
                    )
                    self._sleep_before_retry(net_retry_used - 1)
                    continue
                raise RequestError(f"Create upload session failed: {e}") from e
            except requests.RequestException as e:
                raise RequestError(f"Create upload session failed: {e}") from e

            if self._is_retryable_status(resp.status_code) and status_retry_used < self._http_retry_503:
                status_retry_used += 1
                logger.warning(
                    "Create upload session HTTP %s: %s. retry=%s/%s",
                    resp.status_code,
                    resp.text.strip()[:200],
                    status_retry_used,
                    self._http_retry_503,
                )
                self._sleep_before_retry(status_retry_used - 1)
                continue

            if resp.status_code >= 400:
                raise RequestError(f"Create upload session HTTP {resp.status_code}: {resp.text.strip()}")

            data = resp.json()
            if data.get("status") != "success":
                raise RequestError(f"Create upload session failed: {data}")

            session_id = data["data"]["session_id"]
            logger.info("Created upload session: %s", session_id)
            return session_id

    def _upload_get_progress(self, session_id: str, *, timeout: int) -> Dict[str, Any]:
        url = f"{self.api_base}{UPLOAD_PROGRESS_PATH.format(session_id=session_id)}"
        headers = self._headers_api_key()

        net_retry_used = 0
        status_retry_used = 0

        while True:
            try:
                resp = requests.get(url, headers=headers, timeout=timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                if net_retry_used < self._http_retry_timeout:
                    net_retry_used += 1
                    logger.warning(
                        "Get upload progress network/timeout error: %s. retry=%s/%s",
                        e,
                        net_retry_used,
                        self._http_retry_timeout,
                    )
                    self._sleep_before_retry(net_retry_used - 1)
                    continue
                raise RequestError(f"Get upload progress failed: {e}") from e
            except requests.RequestException as e:
                raise RequestError(f"Get upload progress failed: {e}") from e

            if self._is_retryable_status(resp.status_code) and status_retry_used < self._http_retry_503:
                status_retry_used += 1
                logger.warning(
                    "Get upload progress HTTP %s: %s. retry=%s/%s",
                    resp.status_code,
                    resp.text.strip()[:200],
                    status_retry_used,
                    self._http_retry_503,
                )
                self._sleep_before_retry(status_retry_used - 1)
                continue

            if resp.status_code >= 400:
                raise RequestError(f"Get upload progress HTTP {resp.status_code}: {resp.text.strip()}")

            data = resp.json()
            if data.get("status") != "success":
                raise RequestError(f"Get upload progress failed: {data}")

            return data["data"]

    def _upload_chunk(
        self,
        *,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes,
        chunk_checksum: str,
        is_last: bool,
        timeout: int,
    ) -> bool:
        url = f"{self.api_base}{UPLOAD_CHUNK_PATH.format(session_id=session_id)}"
        headers = self._headers_api_key()

        files = {"chunk": ("chunk", chunk_data, "application/octet-stream")}
        data = {
            "chunk_index": str(int(chunk_index)),
            "chunk_checksum": chunk_checksum,
            "is_last": "true" if is_last else "false",
        }

        try:
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=timeout)
        except requests.RequestException as e:
            logger.error("Chunk %s upload error: %s", chunk_index, e)
            return False

        if resp.status_code >= 400:
            logger.error("Chunk %s upload HTTP %s: %s", chunk_index, resp.status_code, resp.text.strip())
            return False

        try:
            out = resp.json()
        except Exception:
            logger.error("Chunk %s upload non-JSON response: %s", chunk_index, resp.text[:200])
            return False

        if out.get("status") != "success":
            logger.error("Chunk %s upload failed: %s", chunk_index, out)
            return False

        logger.info("Chunk %s uploaded successfully", chunk_index)
        return True

    def _upload_finalize(self, session_id: str, *, timeout: int) -> bool:
        url = f"{self.api_base}{UPLOAD_FINALIZE_PATH.format(session_id=session_id)}"
        headers = self._headers_api_key()

        net_retry_used = 0
        status_retry_used = 0

        while True:
            try:
                resp = requests.post(url, headers=headers, timeout=timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                if net_retry_used < self._http_retry_timeout:
                    net_retry_used += 1
                    logger.warning(
                        "Finalize upload network/timeout error: %s. retry=%s/%s",
                        e,
                        net_retry_used,
                        self._http_retry_timeout,
                    )
                    self._sleep_before_retry(net_retry_used - 1)
                    continue
                logger.error("Finalize upload failed: %s", e)
                return False
            except requests.RequestException as e:
                logger.error("Finalize upload failed: %s", e)
                return False

            if self._is_retryable_status(resp.status_code) and status_retry_used < self._http_retry_503:
                status_retry_used += 1
                logger.warning(
                    "Finalize upload HTTP %s: %s. retry=%s/%s",
                    resp.status_code,
                    resp.text.strip()[:200],
                    status_retry_used,
                    self._http_retry_503,
                )
                self._sleep_before_retry(status_retry_used - 1)
                continue

            if resp.status_code >= 400:
                logger.error("Finalize upload HTTP %s: %s", resp.status_code, resp.text.strip())
                return False

            data = resp.json()
            if data.get("status") != "success":
                logger.error("Finalize upload failed: %s", data)
                return False

            logger.info("Upload session %s finalized successfully", session_id)
            return True

    # -------- session cache (resume across restarts) --------
    def _load_cached_session_id(self, record_id: int, checksum: str) -> Optional[str]:
        key = f"{int(record_id)}:{checksum}"
        try:
            if not self._upload_cache_path.exists():
                return None
            obj = json.loads(self._upload_cache_path.read_text("utf-8"))
            v = obj.get(key)
            return str(v) if v else None
        except Exception:
            return None

    def _save_cached_session_id(self, record_id: int, checksum: str, session_id: str) -> None:
        key = f"{int(record_id)}:{checksum}"
        try:
            obj = {}
            if self._upload_cache_path.exists():
                obj = json.loads(self._upload_cache_path.read_text("utf-8"))
            obj[key] = session_id
            self._upload_cache_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")
        except Exception:
            return

    def _delete_cached_session_id(self, record_id: int, checksum: str) -> None:
        key = f"{int(record_id)}:{checksum}"
        try:
            if not self._upload_cache_path.exists():
                return
            obj = json.loads(self._upload_cache_path.read_text("utf-8"))
            if key in obj:
                obj.pop(key, None)
                self._upload_cache_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")
        except Exception:
            return

    # ============================================================
    # ✅ V2 additions: gRPC send_data() (Runner) - does not affect existing HTTP logic
    # ============================================================
    def _grpc_pick_stub_and_request(self):
        """
        Pick gRPC Stub + Request message class from generated proto module.

        Compatible with your current generated file:
        - service_pb2_grpc.JsonServiceStub
        - service_pb2.JsonRequest
        Also works if names change (falls back to any *Stub / *Request).
        """
        try:
            import grpc  # noqa: F401
        except Exception as e:
            raise ConfigurationError("grpcio is required for send_data(). Please `pip install grpcio`.") from e

        try:
            from .proto import service_pb2_grpc, service_pb2
        except Exception as e:
            raise ConfigurationError(
                "Cannot import proto modules. Expected liberal_alpha/proto/service_pb2.py and service_pb2_grpc.py"
            ) from e

        # ---- pick stub ----
        stub_cls = None
        if hasattr(service_pb2_grpc, "JsonServiceStub"):
            stub_cls = getattr(service_pb2_grpc, "JsonServiceStub")
        else:
            for name in dir(service_pb2_grpc):
                if name.endswith("Stub"):
                    stub_cls = getattr(service_pb2_grpc, name)
                    break
        if stub_cls is None:
            raise ConfigurationError("Cannot find gRPC stub class in proto module (service_pb2_grpc).")

        # ---- pick request msg ----
        req_cls = None
        if hasattr(service_pb2, "JsonRequest"):
            req_cls = getattr(service_pb2, "JsonRequest")
        else:
            for name in dir(service_pb2):
                if name.endswith("Request"):
                    obj = getattr(service_pb2, name)
                    if hasattr(obj, "DESCRIPTOR"):
                        req_cls = obj
                        break
        if req_cls is None:
            raise ConfigurationError("Cannot find gRPC request message class in proto module (service_pb2).")

        return stub_cls, req_cls

    def _grpc_build_request(self, req_cls, identifier: str, data: dict, record_id: int, event_type: str):
        """
        Build protobuf request message in a field-safe way:
        - Only set fields that actually exist in the generated message schema.

        Your current proto(JsonRequest) is typically:
          - json_data: string
          - event_type: string
          - timestamp: int64
          - metadata: map<string,string>
        """
        # discover fields
        try:
            field_names = {f.name for f in req_cls.DESCRIPTOR.fields}
        except Exception:
            field_names = set()

        ts_ms = int(time.time() * 1000)

        # Put everything (including record_id/identifier) into json_data to be proto-compatible
        payload_json = json.dumps(data or {}, ensure_ascii=False)


        md = {
            "record_id": str(record_id),
            "identifier": str(identifier),
            "event_type": str(event_type),
        }

        kwargs: Dict[str, Any] = {}

        # common request shapes
        if "json_data" in field_names:
            kwargs["json_data"] = payload_json
        elif "jsonData" in field_names:
            kwargs["jsonData"] = payload_json
        elif "data" in field_names:
            # could be string or bytes; try string first
            kwargs["data"] = payload_json
        elif "payload" in field_names:
            kwargs["payload"] = payload_json
        elif "message" in field_names:
            kwargs["message"] = payload_json

        if "event_type" in field_names:
            kwargs["event_type"] = str(event_type)
        elif "eventType" in field_names:
            kwargs["eventType"] = str(event_type)

        if "timestamp" in field_names:
            kwargs["timestamp"] = ts_ms
        elif "timestamp_ms" in field_names:
            kwargs["timestamp_ms"] = ts_ms
        elif "timestampMs" in field_names:
            kwargs["timestampMs"] = ts_ms

        if "metadata" in field_names:
            kwargs["metadata"] = md

        # create message
        try:
            req = req_cls(**kwargs)
        except TypeError:
            req = req_cls()
            for k, v in kwargs.items():
                try:
                    setattr(req, k, v)
                except Exception:
                    pass

        # If schema expects bytes for 'data', convert
        try:
            if "data" in field_names:
                f = req_cls.DESCRIPTOR.fields_by_name.get("data")
                # TYPE_BYTES == 12
                if f is not None and getattr(f, "type", None) == 12 and isinstance(getattr(req, "data", None), str):
                    setattr(req, "data", payload_json.encode("utf-8"))
        except Exception:
            pass

        return req

    def send_data(
        self,
        *,
        identifier: str,
        data: dict,
        record_id: int,
        event_type: str = "raw",
        timeout: Optional[float] = None,
    ):
        """
        Send one JSON payload to local gRPC runner.

        Compatible with generated service:
        - stub: JsonServiceStub
        - rpc: ProcessJson
        - request: JsonRequest (field-safe population)
        """
        # ---- runner host/port ----
        host = (
            getattr(self, "host", None)
            or getattr(self, "runner_host", None)
            or os.getenv("LIBALPHA_RUNNER_HOST", "127.0.0.1")
        )
        port = int(
            getattr(self, "port", None)
            or getattr(self, "runner_port", None)
            or os.getenv("LIBALPHA_RUNNER_PORT", "8128")
        )
        target = f"{host}:{port}"

        # ---- grpc deps ----
        import grpc

        stub_cls, req_cls = self._grpc_pick_stub_and_request()

        req = self._grpc_build_request(
            req_cls=req_cls,
            identifier=str(identifier),
            data=data or {},
            record_id=int(record_id),
            event_type=str(event_type),
        )

        # ---- call ----
        call_timeout = float(timeout) if timeout is not None else float(getattr(self, "timeout", 30))

        try:
            with grpc.insecure_channel(target) as channel:
                stub = stub_cls(channel)

                if hasattr(stub, "ProcessJson"):
                    return stub.ProcessJson(req, timeout=call_timeout)

                # fallback: find a callable attr
                for name in dir(stub):
                    if name.startswith("_"):
                        continue
                    fn = getattr(stub, name, None)
                    if callable(fn):
                        return fn(req, timeout=call_timeout)

                raise ConfigurationError("No callable RPC method found on gRPC stub.")
        except grpc.RpcError as e:
            raise RequestError(f"gRPC call failed: {e}") from e

    # ============================================================
    # ✅ V2 additions: WebSocket subscribe_data(use_v2)
    # ============================================================
    def subscribe_data(
        self,
        *,
        record_id: int,
        max_reconnect: int = 3,
        on_message: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Any], None]] = None,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        use_v2: bool = True,
    ) -> None:
        """
        Blocking websocket subscription. Typical usage: run in a daemon thread.

        - Uses JWT bearer header by default
        - Reconnects up to max_reconnect
        """
        try:
            import websocket  # type: ignore
        except Exception as e:
            raise ConfigurationError("websocket-client not installed. `pip install websocket-client`") from e

        ws_base = _to_ws_url(self.api_base)
        path = WS_V2_PATH if use_v2 else WS_V1_PATH

        # best-effort: support both query styles
        url1 = f"{ws_base}{path}?record_id={int(record_id)}"
        url2 = f"{ws_base}{path}/{int(record_id)}"
        logger.info("WS urls: %s | %s", url1, url2)

        token = self._ensure_jwt()
        headers = [f"Authorization: Bearer {token}"]
        if self.api_key:
            headers.append(f"X-API-Key: {self.api_key}")

        def _wrap_on_message(ws, msg):
            try:
                obj: Any
                try:
                    obj = json.loads(msg)
                except Exception:
                    obj = msg
                if on_message:
                    on_message(obj)
            except Exception as e:
                if on_error:
                    on_error(e)
                else:
                    logger.exception("on_message handler error: %s", e)

        def _wrap_on_error(ws, err):
            if on_error:
                on_error(err)
            else:
                logger.error("WebSocket error: %s", err)

        def _wrap_on_open(ws):
            if on_open:
                try:
                    on_open(ws)  
                except TypeError:
                    on_open()     


        def _wrap_on_close(ws, code, reason):
            if on_close:
                try:
                    on_close(code, reason)
                except TypeError:
                    on_close()


        attempts = 0
        last_err: Optional[Exception] = None

        while attempts <= int(max_reconnect):
            attempts += 1

            for url in (url1,):
                try:
                    logger.info("WebSocket connect: %s (attempt %s/%s)", url, attempts, max_reconnect + 1)
                    wsapp = websocket.WebSocketApp(
                        url,
                        header=headers,
                        on_message=_wrap_on_message,
                        on_error=_wrap_on_error,
                        on_open=_wrap_on_open,
                        on_close=_wrap_on_close,
                    )
                    wsapp.run_forever(ping_interval=20, ping_timeout=10)
                except Exception as e:
                    last_err = e
                    continue

            if attempts <= int(max_reconnect):
                time.sleep(min(2 ** (attempts - 1), 10))

        raise RequestError(f"WebSocket subscription failed after retries. last_err={last_err}")


# ----------------------------
# Keep compatibility with liberal_alpha/__init__.py
# ----------------------------
liberal: Optional[LiberalAlphaClient] = None


def initialize(
    api_key: Optional[str] = None,
    private_key: Optional[str] = None,
    api_base: str = DEFAULT_API_BASE,
    timeout: int = 30,
) -> LiberalAlphaClient:
    global liberal
    liberal = LiberalAlphaClient(
        api_key=api_key,
        private_key=private_key,
        api_base=api_base,
        timeout=timeout,
    )
    return liberal
