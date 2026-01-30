"""This is an automatically generated stub for `a.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EE1QBgb/QLHwEGFhLfIAAQcAAxEVahEZFxEllwAC/3Rlc3QvYS5jAA9hcG5wUQQBAf83TTuRNn8G8gARARIBQVEYAQL/LF+Av575xrkAUUACAUFQAf9s+bDj/qNejABRTAIBQVwB/5a1swP4yOSeAFFYAgFBaAH/03wfiLRrBpsAUWQCAUFwAf/gK3kjEH+pvgBRbAIBQXgB/7VEDiYBtjDhAFF0AgFBmAEBDAAAEQF6/21hczo6cnBjAD86OnRlc3QAAAEMAAARAYL/bWFzLnNjaGUBbWEudGVzdAAAAAEMAAARAWL/ZGUuemFsZi4AB21hcwAAAQwAABEBOj9PdXRlckEAAAEMAAARASoPdGVzdAAAAQwAADEBsgH/Z2l0aHViLmMFb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nbx8vdGVzdAAA",  # test/a.capnp
    "EBxQBgb/N007kTZ/BvIAEQ0D/0Cx8BBhYS3yAAABM5kB1AERFXoRGQcAABEVRxE9BwAA/3Rlc3QvYS5jAD9hcG5wOkFQAQFRBAMFAAD/MnUTrclmGPkBBEUEJH6bpvEREToAAhEFBz9tZXRob2RAAVABAQ==",  # test/a.capnp:A
    "ECFQBgb/MnUTrclmGPkAEQ8BAAAFAQcAAREV6gABERk/AAH/dGVzdC9hLmMCYXBucDpBLm1ldGhvZCRQYQ9yYW1zUQQDBAAABAEAABENMgAAUQgDAVEUAgEfcGFyYW0BDAACAQwAAQ==",  # test/a.capnp:A.method$Params
    "ECFQBgb/BEUEJH6bpvEAEQ8BAAAFAQcAAREV8gABERk/AAH/dGVzdC9hLmMCYXBucDpBLm1ldGhvZCRSZR9zdWx0c1EEAwQAAAQBAAARDSIAAFEIAwFRFAIBB3JlcwEMAAIBDAAB",  # test/a.capnp:A.method$Results
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
A = _InterfaceModule(_loader.get(0xF2067F36913B4D37).as_interface(), "A")

A.Server.MethodResultTuple = NamedTuple("MethodResultTuple", [("res", object)])
