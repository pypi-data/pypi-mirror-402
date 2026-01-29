""" Utils for client-server communication. """
import json
import numpy as np
import torch
from typing import Any
import sys
import termios

import femtocrux.grpc.compiler_service_pb2 as cs_pb2


def field_or_none(message: Any, field_name: str) -> Any:
    """Convert empty message fields to None."""
    return getattr(message, field_name) if message.HasField(field_name) else None


def get_channel_options(max_message_mb: int = 32):
    # Set the maximum message size
    megabyte_size = 2**20
    max_message_size = max_message_mb * megabyte_size
    return [
        ("grpc.max_send_message_length", max_message_size),
        ("grpc.max_receive_message_length", max_message_size),
    ]


def serialize_numpy_array(arr: np.ndarray) -> cs_pb2.ndarray:
    """Serializes a NumPy array into a NumpyArrayProto message."""
    return cs_pb2.ndarray(
        data=arr.tobytes(), shape=list(arr.shape), dtype=str(arr.dtype)
    )


def prepare_array_for_serialization(array, type_of_input="dict"):
    """
    Check that the arrays that are sent for inputs have the correct types and shapes.

    They have to be np.ndarrays and have the appropriate shapes:
    List[Dict[str, np.ndarray]] the ndarray has to only have 1 dimension of features
    Dict[str, np.ndarray] the ndarray can have 2 dimensions, one for sequence and
    another for features.
    """
    if isinstance(array, torch.Tensor):
        array_to_serialize = array.numpy()
    elif isinstance(array, np.ndarray):
        array_to_serialize = array
    else:
        raise (Exception("Input array was not of type torch.Tensor or np.ndarray"))

    if not np.issubdtype(array_to_serialize.dtype, np.integer):
        raise (
            Exception(
                "Input data is not an integer type. Please quantize your"
                "data to int16 or lower."
            )
        )
    shape_size = 2
    if type_of_input == "dict":
        shape_size = 2
    elif type_of_input == "list":
        shape_size = 1

    if len(array_to_serialize.shape) > shape_size:
        raise (
            Exception(
                f"Expected {shape_size} dimensions for input and got shape: "
                f"{array_to_serialize.shape} Your input array has too many "
                f"dimensions. When in inference mode, please remove any batch "
                f"dimensions."
            )
        )
    return array_to_serialize


def serialize_sim_inputs_message(
    input_data: list | dict, input_period: float
) -> cs_pb2.simulation_data:
    """
    Serialize input_data which could be the list[dict[str, np.ndarray]] or
    dict[str, np.ndarray] format of input into oneof.

    list_str_array_map or str_array_map proto messages and create a larger
    simulation_data proto message.

    return simulation_data proto message
    """
    message = cs_pb2.simulation_data()

    if isinstance(input_data, list):
        for single_entry in input_data:
            input_map = message.list_inputs.maps.add()
            for key, array in single_entry.items():
                array_to_serialize = prepare_array_for_serialization(
                    array, type_of_input="list"
                )
                input_map.data[key].CopyFrom(serialize_numpy_array(array_to_serialize))

    elif isinstance(input_data, dict):
        for key, array in input_data.items():
            array_to_serialize = prepare_array_for_serialization(
                array, type_of_input="dict"
            )
            message.inputs.data[key].CopyFrom(serialize_numpy_array(array_to_serialize))
    else:
        raise (
            Exception(f"input_data was of type {type(input_data)}, not dict or list.")
        )
    message.input_period = input_period
    return message


def serialize_simulation_output(
    output_data: dict | list, report
) -> cs_pb2.simulation_output:
    """
    Serialize the output_data and report into a proto message simulation_output.

    We have both the list[dict[str, np.ndarray]] and the dict[str, np.ndarray]
    as possible output formats.

    We serialize whichever one we get as message.list_outputs or message.outputs

    return the proto message
    """
    message = cs_pb2.simulation_output()

    if isinstance(output_data, list):
        for single_entry in output_data:
            output_map = message.list_outputs.maps.add()
            for key, array in single_entry.items():
                output_map.data[key].CopyFrom(serialize_numpy_array(array))
    elif isinstance(output_data, dict):
        for key, array in output_data.items():
            message.outputs.data[key].CopyFrom(serialize_numpy_array(array))

    message.report = json.dumps(report)
    message.status.CopyFrom(cs_pb2.status(success=True))

    return message


def deserialize_numpy_array(proto: cs_pb2.ndarray) -> np.ndarray:
    """Deserializes a NumpyArrayProto message back into a NumPy array."""
    return np.frombuffer(proto.data, dtype=np.dtype(proto.dtype)).reshape(proto.shape)


def deserialize_simulation_data(proto: cs_pb2.str_array_map) -> dict:
    """Deserializes a LargerMessage back into a dictionary of NumPy arrays."""
    return {key: deserialize_numpy_array(value) for key, value in proto.data.items()}


def deserialize_simulation_data_list(list_input: cs_pb2.list_str_array_map) -> list:
    """
    Convert proto list_str_array_map into a python list[dict[str, np.ndarray]]
    """
    list_of_dicts = []
    for input_map in list_input.maps:
        dict_entry = {}
        for key, ndarray_proto in input_map.data.items():
            # Convert ndarray proto to whatever format you need
            dict_entry[key] = deserialize_numpy_array(ndarray_proto)
        list_of_dicts.append(dict_entry)
    return list_of_dicts


def read_secret_raw(prompt="Secret: "):
    """Read a secret from stdin without echoing or overflowing buffer"""
    fd = sys.stdin.fileno()
    sys.stdout.write(prompt)
    sys.stdout.flush()
    old = termios.tcgetattr(fd)
    try:
        new = termios.tcgetattr(fd)
        new[3] &= ~(termios.ECHO | termios.ICANON)  # no echo, raw-ish
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        chunks = []
        while True:
            ch = sys.stdin.buffer.read(1)
            if ch in (b"\n", b"\r"):
                break
            chunks.append(ch)
        sys.stdout.write("\n")
        sys.stdout.flush()
        return b"".join(chunks).decode("utf-8", "replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
