"""
Script to check the server's health. Returns 0 if healthy, 1 otherwise.

This is used by the docker HEALTHCHECK command.
"""

import argparse
import grpc
import sys

from femtocrux.server.server import default_port
from femtocrux.server.exceptions import format_exception
from femtocrux.util.utils import get_channel_options

# Import GRPC artifacts
import femtocrux.grpc.compiler_service_pb2 as cs_pb2
import femtocrux.grpc.compiler_service_pb2_grpc as cs_pb2_grpc

# Health codes
healthy = 0
unhealthy = 1


def handle_exception(type, value, tb):
    """Handle uncaught exceptions."""
    print("Healthcheck raised uncaught exception:\n")
    print(format_exception(type, value, tb))
    exit(unhealthy)


# Handle exceptions
sys.excepthook = handle_exception

# Parse arguments
parser = argparse.ArgumentParser(description="Configures the health check client.")
default_port = default_port
parser.add_argument(
    "--port",
    dest="port",
    default=default_port,
    help="the port used for RPCs (default: %s)" % default_port,
)
args = parser.parse_args()

# Create a channel on the given port
sock_name = "localhost:%s" % args.port
channel = grpc.insecure_channel(sock_name, options=get_channel_options())
print("Created gRPC channel at %s" % sock_name)

# Ping the server
message = b"01234"
stub = cs_pb2_grpc.CompileStub(channel)
response = stub.ping(cs_pb2.data(data=message))

# Check the data
if response.data != message:
    print("Ping response doesn't match!")
    exit(unhealthy)

# Server is healthy
print("Server is healthy.")
exit(healthy)
