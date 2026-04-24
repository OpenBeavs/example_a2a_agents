#!/usr/bin/env python3
"""
Universal A2A Agent Deployment Script for Cloud Run

Deploys ADK A2A agents to Google Cloud Run.

Usage:
    python deploy_agent.py <agent-name> [options]

Examples:
    python deploy_agent.py weather_agent
    python deploy_agent.py trivia_agent --project my-project
    python deploy_agent.py financial_auditor_agent --region us-central1
"""

import subprocess
import sys
import os
import argparse
import shutil
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
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deploy an A2A agent to Google Cloud Run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s weather_agent
  %(prog)s trivia_agent --project my-project
  %(prog)s financial_auditor_agent --region us-central1
        """
    )
    parser.add_argument("agent_name", help="Agent directory name to deploy")
    parser.add_argument("--project", help="GCP project ID (default: from gcloud config)")
    parser.add_argument("--region",  help="GCP region (default: from gcloud config or us-west1)")
    parser.add_argument("--memory",  default="1Gi", help="Cloud Run memory (default: 1Gi)")
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

    print(f"\n{'='*70}")
    print("A2A Agent Cloud Run Deployment")
    print(f"{'='*70}")
    print(f"  Agent:   {args.agent_name}")
    print(f"  Service: {service_name}")
    print(f"  Project: {project}")
    print(f"  Region:  {region}")
    print(f"  Memory:  {args.memory}")
    print(f"  URL:     {app_url}")
    print(f"{'='*70}\n")

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
        print(f"  Service URL: {app_url}")
        print(f"  Agent card:  {agent_card_url}")
        print(f"  A2A RPC:     {agent_rpc_url}")
        print(f"\n  To register in the hub, paste the agent card URL into Workspace → Agents.")
        print(f"\nLogs: gcloud run services logs read {service_name} --project={project} --region={region}\n")

    except FileNotFoundError:
        print("\n✗ gcloud not found. Install: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✗ Cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
