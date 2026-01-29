import environ

env = environ.Env()
environ.Env.read_env("/etc/seqslab/cli_apps.env")

name = "organizations"

__version__ = "v3"

PRIVATE_NAME = env.str("PRIVATE_NAME", "api")
API_HOSTNAME = f"{PRIVATE_NAME}.seqslab.net"

__all__ = [API_HOSTNAME, __version__]
