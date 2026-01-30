"""Shim package for monica model submodules."""

from mas.schema.model.monica import (
    monica_management_capnp,
    monica_params_capnp,
    monica_state_capnp,
)

__all__ = [
    "monica_management_capnp",
    "monica_params_capnp",
    "monica_state_capnp",
]
