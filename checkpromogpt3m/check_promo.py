import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Tuple


API_BASE_URL = "https://chatgpt.com/backend-api/promotions/eligibility/"
DEFAULT_CODES_FILE = os.path.join(os.path.dirname(__file__), "promocode.txt")

# The user explicitly provided this token and asked to use it.
# You may override it via --token or PROMO_BEARER_TOKEN env var.
USER_PROVIDED_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc1NTQ3MjU1NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLVdhOGZqbXlTeEFON0p5aFNkSFEwUWFxcyJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJsYWdhMjEzNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImlhdCI6MTc1NDYwODU1NSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIwZWY5NDc0Mi1mMjU0LTQxMWEtODQ1Yy1iYzdkNDVlNTQ4YjIiLCJuYmYiOjE3NTQ2MDg1NTUsInB3ZF9hdXRoX3RpbWUiOjE3NTQ2MDg1NTMwMTMsInNjcCI6WyJvcGVuaWQiLCJlbWFpbCIsInByb2ZpbGUiLCJvZmZsaW5lX2FjY2VzcyIsIm1vZGVsLnJlcXVlc3QiLCJtb2RlbC5yZWFkIiwib3JnYW5pemF0aW9uLnJlYWQiLCJvcmdhbml6YXRpb24ud3JpdGUiXSwic2Vzc2lvbl9pZCI6ImF1dGhzZXNzX0s3Z0V1bmhNOE1mbU83TGh1YVdiOGRYWiIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MTgwODE5MDAzMjg4MzcxODEwIn0.GrYZm_mrbmB9mQdOoTgtUNUJh3sKC9I9LBY7vVmwuqOYivuaSV-UjGBHbbP-CeeZg-v0XWPeVMaOxVoz_Kf64ahUIewsmWQW2h-J0kZQatqY4bgnrergURjdExwNWjhzArSKzbcW8DX6fQDE9s4XQ3c9XNLq8XlE6EJQmX5HrmJVYlm2bhDZ4WdrdRGIXivSbLJAWNOhHHnFAvrnnzp_LbqyLld7913BGloj4jA_ss4CeHTzJIKM6DklFv6wT0lvtCsCCkMcUeKAEcRCGuQN8K0pm3-jm_ADxQ0m_JQivLKLTi6eBvwCkN6adEEanGZSOQKpLSoRUf-qwI2lwIJSJEWb_F4Qv-9J6eEPFvlRGg3vvkV45EE2Gr86BVQ2LJ29eoLJlTlYXqG7Lfy5zz08Lc5V2DNwPj94trmIYjTi9K-3uOLpJxdbPSQxvjgmivCwzr-bWIi3F1Fc_MEbYy1QHgRmAo3ksPiYoEHbQHYxPOWRD7TcQfAwAo97i25RtPJ4TQ8xYc0LK4hMCIal6CsCdG6bc3eoYPuEGnT65FQwjuzd3zD6Kt0g2Is3P0hpBAE2yz-9UvusX6Za8pDH9DYme03KgR76XsZjxIYUG_dvEmMTQyh2iPMywmAff8kwNeFbK0wbUcmuuykSDpo02psB81EJEPrLAd5xP6qfaLG0aWw"
)


def read_codes(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        print(f"Codes file not found: {file_path}", file=sys.stderr)
        return []
    codes: List[str] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            codes.append(line)
    return codes


def build_headers(token: str, cookie: Optional[str], accept_language: Optional[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Python/urllib Safari/537.36",
        "Origin": "https://chatgpt.com",
        "Referer": "https://chatgpt.com/",
    }
    if accept_language:
        headers["Accept-Language"] = accept_language
    if cookie:
        headers["Cookie"] = cookie
    return headers


def fetch_eligibility(code: str, headers: Dict[str, str], timeout_seconds: float = 15.0) -> Tuple[Optional[bool], Optional[str], Optional[int], Optional[str], Optional[bytes]]:
    url = API_BASE_URL + urllib.parse.quote(code)
    request = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.getcode()
            data = response.read()
            # Try parse JSON
            try:
                payload = json.loads(data.decode("utf-8"))
                return (
                    payload.get("is_eligible"),
                    payload.get("ineligible_reason"),
                    status_code,
                    None,
                    data,
                )
            except json.JSONDecodeError:
                return None, None, status_code, "Invalid JSON in response", data
    except urllib.error.HTTPError as e:
        error_body = None
        try:
            error_body = e.read()
        except Exception:
            error_body = None
        return None, None, e.code, None if error_body is None else error_body.decode("utf-8", errors="ignore"), error_body
    except urllib.error.URLError as e:
        return None, None, None, str(e.reason), None


def with_retries(code: str, headers: Dict[str, str], retries: int = 2, backoff_seconds: float = 1.0) -> Tuple[Optional[bool], Optional[str], Optional[int], Optional[str], Optional[bytes]]:
    attempt = 0
    while True:
        is_eligible, reason, status, error, raw = fetch_eligibility(code, headers)
        if status in (429, 500, 502, 503, 504) and attempt < retries:
            attempt += 1
            time.sleep(backoff_seconds * attempt)
            continue
        return is_eligible, reason, status, error, raw


def save_debug_body(code: str, body: Optional[bytes], output_dir: str) -> Optional[str]:
    if not body:
        return None
    path = os.path.join(output_dir, f"debug_last_response_{code}.txt")
    try:
        with open(path, "wb") as f:
            f.write(body)
        return path
    except Exception:
        return None


def write_valid_results(valid_results: List[str], output_dir: str) -> None:
    valid_path = os.path.join(output_dir, "valid_codes.txt")
    with open(valid_path, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_results))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check promo eligibility via API.")
    parser.add_argument(
        "--codes",
        default=DEFAULT_CODES_FILE,
        help=f"Path to codes file (default: {DEFAULT_CODES_FILE})",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("PROMO_BEARER_TOKEN", USER_PROVIDED_TOKEN),
        help="Bearer token. If omitted, will use PROMO_BEARER_TOKEN env var or the embedded token.",
    )
    parser.add_argument(
        "--cookie",
        default=os.getenv("PROMO_COOKIE"),
        help="Optional Cookie header value, if needed (e.g., Cloudflare cookies).",
    )
    parser.add_argument(
        "--accept-language",
        default=os.getenv("PROMO_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
        help="Optional Accept-Language header value.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.dirname(__file__),
        help="Directory to write result files (valid_codes.txt and debug files).",
    )
    args = parser.parse_args()

    codes = read_codes(args.codes)
    if not codes:
        print("No promo codes found to check.")
        return 1

    if not args.token:
        print("Missing bearer token. Provide --token or set PROMO_BEARER_TOKEN.", file=sys.stderr)
        return 2

    headers = build_headers(args.token, args.cookie, args.accept_language)

    valid_results: List[str] = []

    print("Checking promo codes...\n")
    for idx, code in enumerate(codes, start=1):
        is_eligible, reason, status, error, raw = with_retries(code, headers)
        if is_eligible is True:
            print(f"[{idx}/{len(codes)}] {code}: ELIGIBLE")
            valid_results.append(code)
        elif is_eligible is False:
            display_reason = reason if reason else "unknown"
            print(f"[{idx}/{len(codes)}] {code}: INELIGIBLE - {display_reason}")
        else:
            detail = f"status={status}" if status is not None else "no_status"
            if error:
                detail += f", error={(error[:200] if isinstance(error, str) else str(error))}"
            debug_path = save_debug_body(code, raw, args.output_dir)
            if debug_path:
                detail += f", saved={os.path.basename(debug_path)}"
            print(f"[{idx}/{len(codes)}] {code}: ERROR - {detail}")

    write_valid_results(valid_results, args.output_dir)

    print("\nDone.")
    print(f"Valid codes saved to: {os.path.join(args.output_dir, 'valid_codes.txt')}")

    if not valid_results:
        print("Hint: If you see HTML in debug files, pass --cookie with your chatgpt.com session cookies.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
