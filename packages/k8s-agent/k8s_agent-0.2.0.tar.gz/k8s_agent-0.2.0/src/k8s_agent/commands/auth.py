"""Authentication commands: login, logout, whoami."""

import time
import webbrowser

import click

from ..config import AgentConfig
from ..http import K8sVMgrAPI, APIError


def _default_api_url():
    import os
    return os.environ.get("K8SVMGR_API_URL", "").strip()


def _normalize_api_url(api_url: str) -> str:
    api_url = (api_url or "").strip().rstrip("/")
    if api_url.lower().endswith("/api"):
        api_url = api_url[:-4]
    return api_url


def _extract_data(resp: dict) -> dict:
    return resp.get("data") if isinstance(resp.get("data"), dict) else {}


@click.group()
def auth_commands():
    """Authentication commands."""
    pass


@auth_commands.command(name="login")
@click.option("--api-url", "api_url", default="", help="Base URL, e.g. http://127.0.0.1:5000")
@click.option("--no-browser", is_flag=True, default=False, help="Do not auto-open browser")
@click.option("--timeout", default=600, show_default=True, type=int, help="Timeout seconds")
def login(api_url: str, no_browser: bool, timeout: int):
    """Login via browser approval (device-code flow)."""
    cfg = AgentConfig.load()
    api_url = _normalize_api_url(api_url or cfg.api_url or _default_api_url())
    if not api_url:
        raise click.ClickException(
            "Missing --api-url (or set env K8SVMGR_API_URL, or login once to save it)"
        )

    api = K8sVMgrAPI(api_url)

    # 1) Start device flow
    try:
        start = api.request("POST", "/api/oauth/device/code", json_body={"client_id": "k8s-agent"})
    except APIError as e:
        raise click.ClickException(f"Start login failed: {e}")
    data = _extract_data(start)
    device_code = data.get("device_code", "")
    user_code = data.get("user_code", "")
    verify_complete = data.get("verification_uri_complete", "")
    interval = int(data.get("interval") or 2)

    if not device_code or not user_code or not verify_complete:
        raise click.ClickException(f"Unexpected response: {start}")

    click.echo(f"User code: {user_code}")
    click.echo(f"Open this URL to approve: {verify_complete}")
    if not no_browser:
        try:
            webbrowser.open(verify_complete)
        except Exception:
            pass

    # 2) Poll until approved
    deadline = time.time() + timeout
    click.echo("Waiting for approval...")
    while True:
        if time.time() > deadline:
            raise click.ClickException("Timeout waiting for approval.")

        try:
            tok = api.request("POST", "/api/oauth/device/token", json_body={"device_code": device_code})
            tok_data = _extract_data(tok)
            access_token = tok_data.get("access_token", "")
            refresh_token = tok_data.get("refresh_token") or ""
            if access_token:
                cfg.api_url = api_url
                cfg.access_token = access_token
                cfg.refresh_token = refresh_token
                cfg.save()
                break
        except APIError as e:
            payload = e.payload or {}
            err = str(payload.get("error") or "")
            if e.status_code == 428 and err == "authorization_pending":
                time.sleep(max(1, interval))
                continue
            raise click.ClickException(f"Login failed: {e}")

        time.sleep(max(1, interval))

    # 3) Verify token by calling /api/user
    try:
        api2 = K8sVMgrAPI(api_url, access_token=cfg.access_token)
        me = api2.request("GET", "/api/user")
        me_data = _extract_data(me)
        renter = me_data.get("renter") or "(unknown)"
        click.echo(f"Logged in as: {renter}")
    except APIError as e:
        click.echo(f"Logged in, but failed to fetch user info: {e}")
        click.echo("Token was saved. Try: k8s-agent whoami")


@auth_commands.command(name="logout")
def logout():
    """Remove local tokens."""
    cfg = AgentConfig.load()
    if not cfg.is_logged_in():
        click.echo("Not logged in.")
        return
    cfg.clear_tokens()
    cfg.save()
    click.echo("Logged out.")


@auth_commands.command(name="whoami")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def whoami(api_url: str):
    """Show current user (requires login)."""
    cfg = AgentConfig.load()
    api_url = _normalize_api_url(api_url or cfg.api_url or _default_api_url())
    if not api_url or not cfg.access_token:
        raise click.ClickException("Not logged in. Run: k8s-agent login")
    api = K8sVMgrAPI(api_url, access_token=cfg.access_token)
    try:
        me = api.request("GET", "/api/user")
    except APIError as e:
        raise click.ClickException(str(e))
    me_data = _extract_data(me)
    click.echo(me_data.get("renter") or "")
