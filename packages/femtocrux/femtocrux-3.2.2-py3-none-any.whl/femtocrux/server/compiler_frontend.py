"""
 Copyright Femtosense 2024

 By using this software package, you agree to abide by the terms and conditions
 in the license agreement found at https://femtosense.ai/legal/eula/
"""

import numpy as np
import os
import tempfile
import torch
import zipfile

from fmot import ConvertedModel
from fmot.fqir import GraphProto
from femtomapper import compile as femtomapper_compile
from femtobehav.fasmir import FASMIR
from femtobehav.sim import SimRunner
from femtorun import IOSpec
from typing import Any, Literal


class CompilerFrontend:
    """A generic compiler frontend, must be subclassed for each input IR/framework"""

    def __init__(self, input_ir: Any, fasmir: FASMIR = None):
        self.input_ir = input_ir
        self.fasmir = fasmir
        self.iospec = None
        self.memory_reservations = None
        # self.io_wrapper = io_wrapper

    @property
    def is_compiled(self):
        return self.fasmir is not None

    def _compile(self, input_ir: Any) -> FASMIR:
        """
        Runs FM compiler to generate FASMIR, and encode io information in a
        SimIOWrapper object.

        Must be implemented for each frontend subclass.

        returns FASMIR
        """
        raise NotImplementedError(
            "Subclasses need to implement this based on their input ir"
        )

    def compile(
        self,
        input_ir: GraphProto,
        iospec: IOSpec | None = None,
        opt_profile: Literal["efficient", "fast", "conservative"] | None = None,
        user_configuration: dict | None = None,
        memory_reservations: dict | None = None,
    ) -> tuple[FASMIR, IOSpec, dict]:
        if not self.is_compiled:
            self.fasmir, self.iospec, self.memory_reservations = self._compile(
                input_ir, iospec, opt_profile, user_configuration, memory_reservations
            )
        return self.fasmir, self.iospec, self.memory_reservations

    def dump_bitfile(self, encrypt: bool = True) -> bytes:
        """Dumps a bitfile used to program the SPU."""
        if not self.is_compiled:
            raise RuntimeError("Model must be compiled before dumping bitfile")

        with tempfile.TemporaryFile() as tmpfile:
            with tempfile.TemporaryDirectory() as dirname:
                # Dump memory files to a directory
                runner = SimRunner(
                    self.fasmir, io_spec=self.iospec, data_dir=dirname, encrypt=encrypt
                )
                runner.reset()
                runner.finish()

                # Archive the directory
                with zipfile.ZipFile(
                    tmpfile, mode="w", compression=zipfile.ZIP_DEFLATED
                ) as archive:
                    for relpath in os.listdir(dirname):
                        abspath = os.path.join(dirname, relpath)
                        archive.write(abspath, arcname=relpath)

            # Read out the bytes in the archive
            tmpfile.seek(0)
            bitfile = tmpfile.read()

        return bitfile

    def _get_padded_len(self, fasmir: FASMIR, name: str):
        try:
            fasmir_var = fasmir.data_vars[name]
        except KeyError:
            raise ValueError(
                "Failed to find FASMIR variable corresponding to name %s" % name
            )
        return fasmir_var.numpy.shape[0]

    def run_behavioral_simulator(
        self,
        inputs: dict[str, np.ndarray] | list[dict[str, np.ndarray]],
        input_period: float = None,
        iospec: IOSpec | None = None,
        **kwargs
    ):
        """
        Runs the behavioral simulator and returns outputs and metrics.

        Arguments:
            args (np.ndarray): Input tensors to the simulator, as numpy arrays. Either
                               floating-point or integer (see `quantize_inputs` for
                               more detail on input datatypes).
            input_period (float, optional): total simulation time.

        """
        runner = SimRunner(self.fasmir, io_spec=iospec, **kwargs)
        runner.reset()
        outputs, __, __ = runner.run(inputs)
        metrics = runner.get_metrics(input_period, concise=True, as_yamlable=True)
        runner.finish()
        return outputs, metrics


class TorchCompiler(CompilerFrontend):
    def __init__(self, graph: GraphProto, batch_dim: int = None, seq_dim: int = None):
        assert isinstance(graph, GraphProto)

        super().__init__(input_ir=graph)
        self.batch_dim = batch_dim
        self.seq_dim = seq_dim

    def _compile(
        self,
        input_ir: GraphProto,
        iospec: IOSpec | None = None,
        opt_profile: Literal["efficient", "fast", "conservative"] | None = None,
        user_configuration: dict | None = None,
        memory_reservations: dict | None = None,
    ) -> tuple[FASMIR, IOSpec, dict]:
        mapper_state, iospec, memory_reservations = femtomapper_compile(
            input_ir, iospec, opt_profile, user_configuration, memory_reservations
        )
        fasmir = mapper_state.fasmir
        return fasmir, iospec, memory_reservations

    @classmethod
    def from_fqir(cls, graph: GraphProto, batch_dim: int = None, seq_dim: int = None):
        assert isinstance(graph, GraphProto)
        return cls(graph, batch_dim, seq_dim)

    @classmethod
    def from_converted_model(
        cls,
        model: ConvertedModel,
        batch_dim: int = None,
        seq_dim: int = None,
        experimental_tracing=False,
    ):
        assert isinstance(model, ConvertedModel)
        graph = model.trace(experimental_hybrid_tracing=experimental_tracing)
        return cls(graph, batch_dim, seq_dim)

    @classmethod
    def from_torch_module(
        cls,
        module: torch.nn.Module,
        calibration_data,
        precision: str = "double",
        batch_dim: int = None,
        seq_dim: int = None,
        experimental_tracing=False,
        conversion_kwargs: dict = {},
    ):
        cmodel = ConvertedModel(
            module, precision, batch_dim=batch_dim, seq_dim=seq_dim, **conversion_kwargs
        )
        cmodel.quantize(calibration_data)

        return TorchCompiler.from_converted_model(
            cmodel, batch_dim, seq_dim, experimental_tracing
        )
