# Set environment variables for local tests

import docker  # type: ignore

print(
    "\nRun the following commands to set the variable environments "
    "needed to run the tests locally."
)
client = docker.APIClient()
containers = client.containers(limit=-1)
gitlab_ports = containers[0]["Ports"]
gitlab_80_ports = [
    port["PublicPort"] for port in gitlab_ports if port["PrivatePort"] == 80
]
IP_address = containers[0]["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
print("\nFor zsh and bash shells:")
command = "export GITLAB_HOST=0.0.0.0"
print(command)
command = f"export GITLAB_80_TCP_PORT={str(gitlab_80_ports[0])}"
print(command)
print("\nFor PowerShell:")
command = "$Env:GITLAB_HOST = '0.0.0.0'"
print(command)
command = f"$Env:GITLAB_80_TCP_PORT = '{str(gitlab_80_ports[0])}'"
print(command)
