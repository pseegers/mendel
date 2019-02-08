import docker
from fabric.colors import blue
from fabric import state

def initialize_heavyset():
    """
        This function starts up heavyset, which is an ubuntu 18.04 based container with
        systemd installed and test-fixtured config.
    """

    state.env.user = 'vagrant'
    state.env.password = 'vagrant'

    client = docker.from_env()

    http_port = '8081'
    ssh_port = '2223'

    print blue("Setting your machine up to work with systemd container...")
    client.containers.run(
        image='solita/ubuntu-systemd:18.04',
        command='setup',
        volumes=['/:/host'],
        privileged=True,
        remove=True
    )


    print blue("Running ubuntu 18.04 based systemd container...")
    client.containers.run(
        image='ihamisu/heavyset:1.0.4',
        detach=True,
        name='stage-host',
        security_opt=['seccomp=unconfined'],
        tmpfs= {
            '/run': '',
            '/run/lock': ''
        },
        volumes=['/sys/fs/cgroup:/sys/fs/cgroup:ro'],
        ports={
            '8080/tcp': http_port,
            '22/tcp': ssh_port
        }
    )

if __name__== "__main__":
  initialize_heavyset()