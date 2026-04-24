#!/usr/bin/env python3
"""
Universal A2A Agent Deployment Script for Cloud Run

Deploys ADK A2A agents to Google Cloud Run, then automatically syncs the
deployed URL to the GENESIS-AI-Hub registry (update existing entry or create
a new one) and installs the agent — so no manual registry updates are needed.

Usage:
    python deploy_agent.py <agent-name> [options]

Examples:
    python deploy_agent.py weather_agent
    python deploy_agent.py financial_auditor_agent --project my-project
    python deploy_agent.py trivia_agent --region us-central1

Hub sync (optional — set in .env or pass as flags):
    HUB_URL=https://your-hub.run.app
    HUB_TOKEN=<bearer token from hub login>
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


def _gcloud_exe() -> str:
    """Return the correct gcloud executable name for the current platform."""
    for name in ("gcloud", "gcloud.cmd"):
        path = shutil.which(name)
        if path:
            return path
    return "gcloud"


def get_gcloud_config(property_name):
    """Get a property from gcloud config."""
    try:
        result = subprocess.run(
            [_gcloud_exe(), "config", "get-value", property_name],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
        )
        value = result.stdout.strip()
        if value and value != "(unset)":
            return value
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def get_project_number(project_id):
    """Get the project number for a given project ID."""
    try:
        result = subprocess.run(
            [_gcloud_exe(), "projects", "describe", project_id, "--format=value(projectNumber)"],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# ─────────────────────────────────────────────────────────────
# Hub registry sync
# ─────────────────────────────────────────────────────────────

def _hub_request(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, dict]:
    """Make an authenticated JSON request to the hub API."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
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


def sync_with_hub(hub_url: str, hub_token: str, agent_card_url: str, agent_name: str) -> None:
    """Update or create the registry entry and install the agent in the hub.

    Steps:
      1. GET  /api/registry/           → find existing entry by agent name
      2a. PUT /api/registry/{id}       → update URL if entry found
      2b. POST /api/registry/          → create new entry if not found
      3. POST /api/v1/agents/register-by-url → install / refresh the agent
    """
    hub_url = hub_url.rstrip("/")
    registry_base = f"{hub_url}/api/registry"
    agents_base   = f"{hub_url}/api/v1/agents"

    print(f"\n{'─'*70}")
    print("Syncing with GENESIS-AI-Hub registry...")
    print(f"  Hub:            {hub_url}")
    print(f"  Agent card URL: {agent_card_url}")

    # ── Step 1: list registry entries ──────────────────────
    status, data = _hub_request("GET", f"{registry_base}/", hub_token)
    if status != 200:
        print(f"  ⚠ Could not fetch registry ({status}): {data.get('detail')} — skipping hub sync.")
        return

    # Find by matching agent name (case-insensitive)
    existing = next(
        (a for a in data if a.get("name", "").lower().replace(" ", "_") == agent_name.lower()),
        None,
    )

    # ── Step 2a: update existing entry ─────────────────────
    if existing:
        agent_id = existing["id"]
        status, result = _hub_request(
            "PUT",
            f"{registry_base}/{agent_id}",
            hub_token,
            {"url": agent_card_url},
        )
        if status == 200:
            print(f"  ✓ Registry entry updated (id: {agent_id})")
        else:
            print(f"  ⚠ Registry update failed ({status}): {result.get('detail')}")

    # ── Step 2b: create new registry entry ─────────────────
    else:
        status, result = _hub_request(
            "POST",
            f"{registry_base}/",
            hub_token,
            {"url": agent_card_url},
        )
        if status == 200:
            print(f"  ✓ New registry entry created (id: {result.get('id')})")
        else:
            print(f"  ⚠ Registry creation failed ({status}): {result.get('detail')}")

    # ── Step 3: install / refresh the agent ────────────────
    status, result = _hub_request(
        "POST",
        f"{agents_base}/register-by-url",
        hub_token,
        {"agent_url": agent_card_url},
    )
    if status == 200:
        print(f"  ✓ Agent installed in hub (id: {result.get('id')})")
    else:
        print(f"  ⚠ Agent install failed ({status}): {result.get('detail')}")

    print(f"{'─'*70}\n")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deploy an A2A agent to Google Cloud Run and sync with the hub registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s weather_agent
  %(prog)s financial_auditor_agent --project my-project
  %(prog)s trivia_agent --region us-central1
  %(prog)s code_review_agent --hub-url https://my-hub.run.app --hub-token eyJ...
        """
    )

    parser.add_argument('agent_name', help='Name of the agent directory to deploy')
    parser.add_argument('--project', help='GCP project ID (default: from gcloud config)')
    parser.add_argument('--region',  help='GCP region (default: from gcloud config or us-west1)')
    parser.add_argument('--memory',  default='1Gi', help='Memory allocation (default: 1Gi)')
    parser.add_argument('--hub-url',   help='GENESIS-AI-Hub base URL (or set HUB_URL in .env)')
    parser.add_argument('--hub-token', help='Hub bearer token (or set HUB_TOKEN in .env)')
    parser.add_argument(
        '--no-hub-sync',
        action='store_true',
        help='Skip hub registry sync even if HUB_URL/HUB_TOKEN are set',
    )

    args = parser.parse_args()

    # Load .env from repo root
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    # ── GCP config ─────────────────────────────────────────
    project = args.project or get_gcloud_config("project")
    if not project:
        print("\n✗ Error: No GCP project specified and could not detect from gcloud config.")
        print("   Set a default: gcloud config set project YOUR-PROJECT-ID")
        print("   Or use --project flag.")
        sys.exit(1)

    region = args.region or get_gcloud_config("compute/region") or "us-west1"

    raw_name     = Path(args.agent_name).name
    service_name = raw_name.replace("_", "-").lower()

    project_number = get_project_number(project)
    if not project_number:
        print(f"\n⚠ Warning: Could not get project number for {project}")
        app_url = f"https://{service_name}.{region}.run.app"
    else:
        app_url = f"https://{service_name}-{project_number}.{region}.run.app"

    script_dir = Path(__file__).parent.resolve()
    agent_dir  = (script_dir / args.agent_name).resolve()

    if not agent_dir.exists() or not agent_dir.is_dir():
        available = ', '.join(d.name for d in script_dir.iterdir() if d.is_dir() and not d.name.startswith('.'))
        print(f"\n✗ Error: Agent directory not found: {agent_dir}")
        print(f"   Available agents: {available}")
        sys.exit(1)

    # ── Hub sync config ────────────────────────────────────
    hub_url   = args.hub_url   or os.environ.get("HUB_URL",   "")
    hub_token = args.hub_token or os.environ.get("HUB_TOKEN", "")

    # ── Print summary ──────────────────────────────────────
    print(f"\n{'='*70}")
    print("A2A Agent Cloud Run Deployment")
    print(f"{'='*70}")
    print(f"Agent dir:      {args.agent_name}")
    print(f"Service name:   {service_name}")
    print(f"Project:        {project}")
    print(f"Region:         {region}")
    print(f"Memory:         {args.memory}")
    print(f"Authentication: Public (allUsers)")
    print(f"App URL:        {app_url}")
    print(f"Source:         {agent_dir}")
    hub_sync_enabled = hub_url and hub_token and not args.no_hub_sync
    print(f"Hub sync:       {'✓ ' + hub_url if hub_sync_enabled else '— skipped (set HUB_URL + HUB_TOKEN to enable)'}")
    print(f"{'='*70}\n")

    # ── Environment variables for Cloud Run ────────────────
    google_api_key       = os.environ.get("GOOGLE_API_KEY", "")
    firestore_collection = os.environ.get("FIRESTORE_COLLECTION", "osu-knowledge")
    gcp_project_id       = os.environ.get("GCP_PROJECT_ID", project)

    env_vars = {
        "GOOGLE_CLOUD_PROJECT":  project,
        "GOOGLE_CLOUD_LOCATION": region,
        "GCP_PROJECT_ID":        gcp_project_id,
        "FIRESTORE_COLLECTION":  firestore_collection,
        "APP_URL":               app_url,
        "HOST_OVERRIDE":         app_url,
    }
    if google_api_key:
        env_vars["GOOGLE_API_KEY"] = google_api_key

    env_vars_str = ",".join(f"{k}={v}" for k, v in env_vars.items())

    # ── Deploy ─────────────────────────────────────────────
    deploy_cmd = [
        _gcloud_exe(), "run", "deploy", service_name,
        "--quiet",
        "--port=8080",
        f"--source={agent_dir}",
        f"--region={region}",
        f"--project={project}",
        f"--memory={args.memory}",
        f"--set-env-vars={env_vars_str}",
        "--allow-unauthenticated",
    ]

    print("Running command:")
    print(" ".join(deploy_cmd))
    print("\nThis may take several minutes...\n")

    try:
        result = subprocess.run(deploy_cmd, text=True, encoding='utf-8')

        if result.returncode == 0:
            # Re-apply public IAM binding (gcloud run deploy resets it)
            print("\nApplying public IAM binding for A2A agent card endpoint...")
            iam_cmd = [
                _gcloud_exe(), "run", "services", "add-iam-policy-binding",
                service_name,
                f"--region={region}",
                f"--project={project}",
                "--member=allUsers",
                "--role=roles/run.invoker",
            ]
            subprocess.run(iam_cmd, text=True, encoding='utf-8')

            agent_card_url = f"{app_url}/a2a/{raw_name}/.well-known/agent-card.json"
            agent_rpc_url  = f"{app_url}/a2a/{raw_name}/"

            print(f"\n{'='*70}")
            print("✓ Agent deployment successful!")
            print(f"{'='*70}")
            print(f"\n  Service URL:    {app_url}")
            print(f"  Agent Card:     {agent_card_url}")
            print(f"  A2A RPC:        {agent_rpc_url}")

            # ── Hub registry sync ──────────────────────────
            if hub_sync_enabled:
                sync_with_hub(hub_url, hub_token, agent_card_url, raw_name)
            else:
                print(f"\nTo sync with hub manually:")
                print(f"  Re-run with: --hub-url <HUB_URL> --hub-token <TOKEN>")
                print(f"  Or add HUB_URL and HUB_TOKEN to your .env file.\n")

            print(f"To view logs:")
            print(f"  gcloud run services logs read {service_name} --project={project} --region={region}\n")

        else:
            print(f"\n{'='*70}")
            print("✗ Agent deployment FAILED")
            print(f"{'='*70}")
            print("\nCommon issues:")
            print("  - Missing Dockerfile or requirements.txt in agent directory")
            print("  - Insufficient GCP permissions")
            print("  - Invalid source code structure")
            sys.exit(1)

    except FileNotFoundError:
        print("\n✗ Error: 'gcloud' command not found.")
        print("  Install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Deployment cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
