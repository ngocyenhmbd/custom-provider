"""Executes the commands configured in provider.yaml."""

import json
import os
import subprocess
import sys


def run(cmd):
    # print(f"Running: {cmd}", file=sys.stderr)
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=True
    ).stdout

# The environment variables are set by DevPod.
rg = os.environ["AZURE_RESOURCE_GROUP"]
region = os.environ["AZURE_REGION"]
bicep = os.environ["BICEP_FILE"]
cmd = sys.argv[1]

if cmd == "create":
    machine = os.environ["MACHINE_ID"]
    deployment_group_name = f"{os.environ['MACHINE_ID']}-dg"
    run(
        f"az deployment group create "
        f"--name {deployment_group_name} "
        f"--resource-group {rg} "
        f"--template-file {bicep} "
        f"--parameters vmName={machine}"
    )
elif cmd == "delete":
    machine = os.environ["MACHINE_ID"]
    deployment_group_name = f"{machine}-dg"

    # 1) Delete the deployment record (just removes the "deployment" metadata, not resources)
    run(
        f"az deployment group delete "
        f"--name {deployment_group_name} "
        f"--resource-group {rg} "
        f"-y || echo 'already deleted'"
    )

    # 2) List resources that have the DeploymentGroup tag
    resources_json = run(
        f"az resource list "
        f"--tag DeploymentGroup={machine} "
        f"--out json"
    )

    import json
    resources = json.loads(resources_json or "[]")

    if not resources:
        print(f"No resources found with tag 'DeploymentGroup={machine}'.")
    else:
        for resource in resources:
            resource_id = resource["id"]
            print(f"Deleting {resource_id}")
            run(f"az resource delete --ids {resource_id}")

elif cmd == "command":
    command = os.environ["COMMAND"]
    machine = os.environ["MACHINE_ID"]
    hostname = run(
        f'az network public-ip show --name {machine}PublicIP --resource-group {rg} --query "dnsSettings.fqdn" --output tsv'
    ).strip()
    subprocess.run(
        [
            "ssh",
            "-o",
            "StrictHostKeyChecking=accept-new",
            f"devpod@{hostname}",
            command,
        ],
        check=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
elif cmd == "status":
    machine = os.environ["MACHINE_ID"]
    status = run(
        f"az vm get-instance-view --resource-group {rg} --name {machine} --query \"instanceView.statuses[?starts_with(code, 'PowerState/')]\" --output json || echo 'not found'"
    ).strip()
    if status == "not found":
        print("NotFound")
    else:
        [status] = json.loads(status)
        if status["code"] == "PowerState/running":
            print("Running")
        else:
            print("Stopped")
