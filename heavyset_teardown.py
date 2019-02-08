import docker
from fabric.colors import blue, red, green

def shutdown_heavyset():
    print blue("Attempting graceful shutdown of systemd container...")

    client = docker.from_env()

    try:
        heavyset = client.containers.get('stage-host')
        print green("Shutdown was successful")
        heavyset.remove(force=True)
    except docker.errors.APIError as e:
        print red("Could not gracefully shutdown & remove systemd container: %s" % e)

if __name__== "__main__":
  shutdown_heavyset()