#!/usr/bin/env python3
"""
Universal A2A Agent Deployment Script for Cloud Run

Deploys ADK A2A agents to Google Cloud Run, then automatically signs into
the GENESIS-AI-Hub and syncs the deployed URL to the registry + installs
the agent. No manual token copying required.

.env keys (all optional for hub sync):
    HUB_URL      = https://your-hub.run.app
    HUB_EMAIL    = your@email.com
    HUB_PASSWORD = yourpassword

Usage:
    python deploy_agent.py <agent-name> [options]

Examples:
    python deploy_agent.py weather_agent
    python deploy_agent.py financial_auditor_agent --project my-project
    python deploy_agent.py trivia_agent --no-hub-sync
"""

import subprocess
import sys
import os
import argparse
import shutil
import urllib.request
import urllib.error
import json
from pathlib import Path
from dotenv import load_dotenv


# ─────────────────────────────────────────────────────────────
# GCloud helpers
# ─────────────────────────────────────────────────────────────

def _gcloud_exe() -> str:
    for name in ("gcloud", "gcloud.cmd"):
        path = shutil.which(name)
        if path:
            return path
    return "gcloud"


def get_gcloud_config(property_name: str):
    try:
        result = subprocess.run(
            [_gcloud_exe(), "config", "get-value", property_name],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        value = result.stdout.strip()
        return value if value and value != "(unset)" else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_project_number(project_id: str):
    try:
        result = subprocess.run(
            [_gcloud_exe(), "projects", "describe", project_id, "--format=value(projectNumber)"],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# ─────────────────────────────────────────────────────────────
# Hub helpers
# ─────────────────────────────────────────────────────────────

def _hub_request(method, url, token, body=None):
    """Authenticated JSON request to the hub. Returns (status_code, dict)."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode()).get("detail", str(e))
        except Exception:
            detail = str(e)
        return e.code, {"detail": detail}
    except Exception as e:
        return 0, {"detail": str(e)}


def hub_signin(hub_url, email, password):
    """POST /api/auths/signin and return the bearer token, or None on failure."""
    url = f"{hub_url}/api/auths/signin"
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode()).get("token")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode()).get("detail", str(e))
        except Exception:
            detail = str(e)
        print(f"  ✗ Hub signin failed ({e.code}): {detail}")
        return None
    except Exception as e:
        print(f"  ✗ Hub signin error: {e}")
        return None


def sync_with_hub(hub_url, email, password, agent_card_url, agent_name):
    """Sign in automatically, then update/create registry entry and install agent."""
    hub_url = hub_url.rstrip("/")

    print(f"\n{'─'*70}")
    print("Syncing with GENESIS-AI-Hub...")
    print(f"  Hub:       {hub_url}")
    print(f"  Card URL:  {agent_card_url}")
    print(f"  Signing in as {email}...")

    token = hub_signin(hub_url, email, password)
    if not token:
        print("  ⚠ Skipping hub sync — check HUB_EMAIL / HUB_PASSWORD in .env")
        print(f"{'─'*70}\n")
        return

    registry_base = f"{hub_url}/api/registry"
    agents_base   = f"{hub_url}/api/v1/agents"

    # 1. Search registry for an existing entry matching this agent
    status, entries = _hub_request("GET", f"{registry_base}/", token)
    if status != 200:
        print(f"  ⚠ Could not read registry ({status}): {entries.get('detail')}")
        print(f"{'─'*70}\n")
        return

    existing = next(
        (a for a in entries
         if a.get("name", "").lower().replace(" ", "_") == agent_name.lower()),
        None,
    )

    # 2a. Update existing entry
    if existing:
        status, result = _hub_request(
            "PUT", f"{registry_base}/{existing['id']}", token, {"url": agent_card_url}
        )
        if status == 200:
            print(f"  ✓ Registry entry updated  (id: {existing['id']})")
        else:
            print(f"  ⚠ Registry update failed ({status}): {result.get('detail')}")

    # 2b. Create new entry — POST fetches the live agent card automatically
    else:
        status, result = _hub_request(
            "POST", f"{registry_base}/", token, {"url": agent_card_url}
        )
        if status == 200:
            print(f"  ✓ Registry entry created  (id: {result.get('id')})")
        else:
            print(f"  ⚠ Registry creation failed ({status}): {result.get('detail')}")

    # 3. Install the agent
    status, result = _hub_request(
        "POST", f"{agents_base}/register-by-url", token, {"agent_url": agent_card_url}
    )
    if status == 200:
        print(f"  ✓ Agent installed in hub  (id: {result.get('id')})")
    else:
        print(f"  ⚠ Agent install failed ({status}): {result.get('detail')}")

    print(f"{'─'*70}\n")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deploy an A2A agent to Cloud Run and auto-sync with the hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Add to .env for fully automatic hub sync (no token needed):
  HUB_URL      = https://your-hub.run.app
  HUB_EMAIL    = your@email.com
  HUB_PASSWORD = yourpassword

Examples:
  %(prog)s weather_agent
  %(prog)s financial_auditor_agent --project my-project
  %(prog)s trivia_agent --no-hub-sync
        """
    )
    parser.add_argument("agent_name", help="Agent directory name to deploy")
    parser.add_argument("--project",     help="GCP project ID (default: from gcloud config)")
    parser.add_argument("--region",      help="GCP region (default: from gcloud config or us-west1)")
    parser.add_argument("--memory",      default="1Gi", help="Cloud Run memory (default: 1Gi)")
    parser.add_argument("--no-hub-sync", action="store_true", help="Skip hub registry sync")
    args = parser.parse_args()

    load_dotenv(Path(__file__).parent / ".env")

    # GCP
    project = args.project or get_gcloud_config("project")
    if not project:
        print("\n✗ No GCP project. Run: gcloud config set project YOUR-PROJECT-ID")
        sys.exit(1)

    region       = args.region or get_gcloud_config("compute/region") or "us-west1"
    raw_name     = Path(args.agent_name).name
    service_name = raw_name.replace("_", "-").lower()
    proj_num     = get_project_number(project)
    app_url      = (
        f"https://{service_name}-{proj_num}.{region}.run.app"
        if proj_num else f"https://{service_name}.{region}.run.app"
    )

    script_dir = Path(__file__).parent.resolve()
    agent_dir  = (script_dir / args.agent_name).resolve()
    if not agent_dir.exists() or not agent_dir.is_dir():
        available = ", ".join(d.name for d in script_dir.iterdir() if d.is_dir() and not d.name.startswith("."))
        print(f"\n✗ Agent directory not found: {agent_dir}")
        print(f"  Available: {available}")
        sys.exit(1)

    # Hub
    hub_url      = os.environ.get("HUB_URL",      "").rstrip("/")
    hub_email    = os.environ.get("HUB_EMAIL",    "")
    hub_password = os.environ.get("HUB_PASSWORD", "")
    hub_sync     = bool(hub_url and hub_email and hub_password) and not args.no_hub_sync

    print(f"\n{'='*70}")
    print("A2A Agent Cloud Run Deployment")
    print(f"{'='*70}")
    print(f"  Agent:    {args.agent_name}")
    print(f"  Service:  {service_name}")
    print(f"  Project:  {project}")
    print(f"  Region:   {region}")
    print(f"  Memory:   {args.memory}")
    print(f"  URL:      {app_url}")
    print(f"  Hub sync: {'✓  ' + hub_url + '  (as ' + hub_email + ')' if hub_sync else '—  add HUB_URL + HUB_EMAIL + HUB_PASSWORD to .env to enable'}")
    print(f"{'='*70}\n")

    # Env vars for Cloud Run
    env_vars = {
        "GOOGLE_CLOUD_PROJECT":  project,
        "GOOGLE_CLOUD_LOCATION": region,
        "GCP_PROJECT_ID":        os.environ.get("GCP_PROJECT_ID", project),
        "FIRESTORE_COLLECTION":  os.environ.get("FIRESTORE_COLLECTION", "osu-knowledge"),
        "APP_URL":               app_url,
        "HOST_OVERRIDE":         app_url,
    }
    if os.environ.get("GOOGLE_API_KEY"):
        env_vars["GOOGLE_API_KEY"] = os.environ["GOOGLE_API_KEY"]

    env_vars_str = ",".join(f"{k}={v}" for k, v in env_vars.items())

    deploy_cmd = [
        _gcloud_exe(), "run", "deploy", service_name,
        "--quiet", "--port=8080",
        f"--source={agent_dir}",
        f"--region={region}",
        f"--project={project}",
        f"--memory={args.memory}",
        f"--set-env-vars={env_vars_str}",
        "--allow-unauthenticated",
    ]

    print("Running:", " ".join(deploy_cmd))
    print("\nThis may take several minutes...\n")

    try:
        result = subprocess.run(deploy_cmd, text=True, encoding="utf-8")
        if result.returncode != 0:
            print("\n✗ Deployment failed.")
            sys.exit(1)

        # Re-apply public IAM binding (gcloud run deploy resets it)
        print("\nApplying public IAM binding...")
        subprocess.run([
            _gcloud_exe(), "run", "services", "add-iam-policy-binding", service_name,
            f"--region={region}", f"--project={project}",
            "--member=allUsers", "--role=roles/run.invoker",
        ], text=True, encoding="utf-8")

        agent_card_url = f"{app_url}/a2a/{raw_name}/.well-known/agent-card.json"
        agent_rpc_url  = f"{app_url}/a2a/{raw_name}/"

        print(f"\n{'='*70}")
        print("✓ Deployment successful!")
        print(f"{'='*70}")
        print(f"  Service URL:  {app_url}")
        print(f"  Agent card:   {agent_card_url}")
        print(f"  A2A RPC:      {agent_rpc_url}")

        if hub_sync:
            sync_with_hub(hub_url, hub_email, hub_password, agent_card_url, raw_name)
        else:
            print(f"\n  Tip: add HUB_URL + HUB_EMAIL + HUB_PASSWORD to .env for automatic hub sync.\n")

        print(f"Logs: gcloud run services logs read {service_name} --project={project} --region={region}\n")

    except FileNotFoundError:
        print("\n✗ gcloud not found. Install: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✗ Cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
