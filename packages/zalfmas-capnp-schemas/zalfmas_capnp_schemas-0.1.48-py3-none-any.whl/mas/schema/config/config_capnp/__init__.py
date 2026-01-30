"""This is an automatically generated stub for `config.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "ED9QBgb/FwdGGe1Mk5wAAQ4AAxEVohEdFxEpZwAC/2NvbmZpZy9jAW9uZmlnLmNhB3BucFEEAQH/2vyuIAZmDYYAEQFCf1NlcnZpY2VREAEC/yxfgL+e+ca5AFEoAgFBPAH/bPmw4/6jXowAUTgCAUFMAf/gK3kjEH+pvgBRSAIBQVQB/7VEDiYBtjDhAFFQAgFBdAEBDAAAEQGi/21hczo6c2NoAWVtYTo6Y29uB2ZpZwAAAQwAABEBkv9tYXMuc2NoZQFtYS5jb25maQFnAAABDAAAEQE6P2NvbmZpZwAAAQwAADEBwgH/Z2l0aHViLmMGb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nby9jb25maWcAAAA=",  # config/config.capnp
    "ECxQBgb/2vyuIAZmDYYAERQD/xcHRhntTJOcAAAAEAEzPAHPAREV4hEhBwAAER1HEXEHEXEP/2NvbmZpZy9jAm9uZmlnLmNhcG5wOlNlcnYHaWNlUAEBUQQDBQAA/9hza0R4F5OKAQuyK9d9FcywERFaAABBEAFBIAERMQf/bmV4dENvbmYAA2lnEQEfUQQCAf/a/K4gBmYNhgABAQAAEQEfUQQCAf/a/K4gBmYNhgABAQAAQAFQAQFBBAERARIBQw==",  # config/config.capnp:Service
    "EBNQBgb/2HNrRHgXk4oAERwBAAAEBxABAAAxFXIBAAT/Y29uZmlnL2MEb25maWcuY2FwbnA6U2VydmljZS5uZXh0Q29uZmlnJFAfYXJhbXM=",  # config/config.capnp:Service.nextConfig$Params
    "EDRQBgb/C7Ir130VzLAAURwBAQAABQEHEAEAADEVegEAAREhdwAB/2NvbmZpZy9jBG9uZmlnLmNhcG5wOlNlcnZpY2UubmV4dENvbmZpZyRSP2VzdWx0c1EIAwQAAAQBAAARKToAAFEkAwFRMAIBAQEUAQEBAREtigAAUTADAVE8AgE/Y29uZmlnARIBAf/a/K4gBmYNhgAAAAESAAH/bm9GdXJ0aGUBckNvbmZpZ3MAAAEBAAIBAQAB",  # config/config.capnp:Service.nextConfig$Results
]

# Load schemas and build module structure
# Use a shared loader stored on capnp module so capabilities work across schema modules
if not hasattr(capnp, "_embedded_schema_loader"):
    capnp._embedded_schema_loader = capnp.SchemaLoader()
_loader = capnp._embedded_schema_loader
for _schema_b64 in _SCHEMA_NODES:
    _schema_data = base64.b64decode(_schema_b64)
    _node_reader = schema_capnp.Node.from_bytes_packed(_schema_data)
    _loader.load_dynamic(_node_reader)

# Build module structure inline
Service = _InterfaceModule(_loader.get(0x860D660620AEFCDA).as_interface(), "Service")

Service.Server.NextconfigResultTuple = NamedTuple(
    "NextconfigResultTuple",
    [("config", object), ("noFurtherConfigs", object)],
)
