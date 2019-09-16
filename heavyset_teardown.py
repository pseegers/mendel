import docker
from docker.errors import APIError

from mendel.util.colors import blue
from mendel.util.colors import green
from mendel.util.colors import red


def shutdown_heavyset():
    print(blue("Attempting graceful shutdown of systemd container..."))

    client = docker.from_env()

    try:
        heavyset = client.containers.get('stage-host')
        print(green("Shutdown was successful"))
        heavyset.remove(force=True)
    except APIError as e:
        print(red("Could not gracefully shutdown & remove systemd container: %s" % e))


if __name__ == "__main__":
    shutdown_heavyset()
