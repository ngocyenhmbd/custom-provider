"""Executes the commands configured in provider.yaml."""

import json
import os
import subprocess
import sys


def run(cmd):
    print(f"Running: {cmd}", file=sys.stderr)
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=True
    ).stdout


# The environment variables are set by DevPod.
rg = os.environ["AZURE_RESOURCE_GROUP"]
region = os.environ["AZURE_REGION"]
bicep = os.environ["BICEP_FILE"]
cmd = sys.argv[1]
if cmd == "create":
    #run(f"az group create --name {rg} --location {region}")
    machine = os.environ["MACHINE_ID"]
    stack_name = f"{os.environ['MACHINE_ID']}-sg"
    run(
        f"az stack group create --name {stack_name} --resource-group {rg} --template-file {bicep} --parameters vmName={machine} --aou 'detachAll' --dm 'none'"
    )
elif cmd == "delete":
    machine = os.environ["MACHINE_ID"]
    stack_name = f"{os.environ['MACHINE_ID']}-sg"
    run(f"az stack group delete --name {stack_name} --resource-group {rg} --action-on-unmanage 'deleteResources'  || echo 'already deleted'")
elif cmd == "command":
    command = os.environ["COMMAND"]
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
