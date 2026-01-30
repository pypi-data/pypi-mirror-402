"""This is an automatically generated stub for `x.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EEZQBgb/excm8PJq0P8AAQcAAxEVahEZRxFJZwAC/3Rlc3QveC5jAA9hcG5wURABAf9HxgveaO8n0gARGRL/FeZN+oGO8twAERUS/72mLKhaHhKsABEREv+rwiVkICZFxgARDRIBUwFYAVkBWlEQAQL/LF+Av575xrkAUSgCAUE8Af9s+bDj/qNejABROAIBQUgB/+AreSMQf6m+AFFEAgFBUAH/tUQOJgG2MOEAUUwCAUFwAQEMAAARAZL/bWFzOjpzY2gBZW1hOjp0ZXMBdAAAAQwAABEBgv9tYXMuc2NoZQFtYS50ZXN0AAAAAQwAABEBKg90ZXN0AAABDAAAMQGyAf9naXRodWIuYwVvbS96YWxmLXJwbS9tYXNfY2FwbnByb3RvX3NjaGVtYXMvZ2VuL2dvHy90ZXN0AAA=",  # test/x.capnp
    "ECBQBgb/R8YL3mjvJ9IAEQ0B/3sXJvDyatD/AAUBBwAAMzQBTQERFXoRGQcAABEVPwAB/3Rlc3QveC5jAD9hcG5wOlNQAQFRBAMEAAAEAQAAEQ0SAABRCAMBURQCAQFjARH/FeZN+oGO8twAAAEBEQAB",  # test/x.capnp:S
    "EBxQBgb/FeZN+oGO8twAEQ0D/3sXJvDyatD/AAABM08BgAERFXoRGQcAABEVRxE9BwAA/3Rlc3QveC5jAD9hcG5wOlhQAQFRBAMFAAD/QCraWmljhcYBDZca7rzmqoYRERIAAhEFBwFtQAFQAQE=",  # test/x.capnp:X
    "ECBQBgb/QCraWmljhcYAUQ8BAQAABAcAAREVwgABERU/AAH/dGVzdC94LmMCYXBucDpYLm0kUGFyYW1zAFEEAwQAAAQBAAARDRIAAFEIAwFRFAIBAWkBBQACAQUAAQ==",  # test/x.capnp:X.m$Params
    "ECFQBgb/DZca7rzmqoYAEQ8BAAAFAQcAAREVygABERk/AAH/dGVzdC94LmMCYXBucDpYLm0kUmVzdWx0cwAAUQQDBAAABAEAABENEgAAUQgDAVEUAgEBdAEMAAIBDAAB",  # test/x.capnp:X.m$Results
    "EBxQBgb/vaYsqFoeEqwAEQ0D/3sXJvDyatD/AAABM4IBqQERFXoRGQcAABEVRxE9BwAA/3Rlc3QveC5jAD9hcG5wOllQAQFRBAMFAAD/kuCsp5y7AsEBEmhU75uL9dwRERIAAhEFBwFtQAFQAQE=",  # test/x.capnp:Y
    "ECBQBgb/kuCsp5y7AsEAEQ8BAAAFAQcAAREVwgABERU/AAH/dGVzdC94LmMCYXBucDpZLm0kUGFyYW1zAFEEAwQAAAQBAAARDTIAAFEIAwFRFAIBH2hlbGxvAQwAAgEMAAE=",  # test/x.capnp:Y.m$Params
    "EBFQBgb/EmhU75uL9dwAEQ8BAAAEBwABERXKAAT/dGVzdC94LmMCYXBucDpZLm0kUmVzdWx0cwAA",  # test/x.capnp:Y.m$Results
    "EBxQBgb/q8IlZCAmRcYAEQ0D/3sXJvDyatD/AAABM6sB3wERFXoRGQcAABEVRxE9BwAA/3Rlc3QveC5jAD9hcG5wOlpQAQFRBAMFAAD/yYzJbckIHfABU2saU2OmRNQRERIAAhEFBwFtQAFQAQE=",  # test/x.capnp:Z
    "ECBQBgb/yYzJbckIHfAAUQ8BAQAABAcAAREVwgABERU/AAH/dGVzdC94LmMCYXBucDpaLm0kUGFyYW1zAFEEAwQAAAQBAAARDRIAAFEIAwFRFAIBAW4BBQACAQUAAQ==",  # test/x.capnp:Z.m$Params
    "ECFQBgb/U2saU2OmRNQAUQ8BAQAABAcAAREVygABERk/AAH/dGVzdC94LmMCYXBucDpaLm0kUmVzdWx0cwAAUQQDBAAABAEAABENEgAAUQgDAVEUAgEBcgELAAIBCwAB",  # test/x.capnp:Z.m$Results
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
S = _StructModule(_loader.get(0xD227EF68DE0BC647).as_struct(), "S")
X = _InterfaceModule(_loader.get(0xDCF28E81FA4DE615).as_interface(), "X")
Y = _InterfaceModule(_loader.get(0xAC121E5AA82CA6BD).as_interface(), "Y")
Z = _InterfaceModule(_loader.get(0xC64526206425C2AB).as_interface(), "Z")

X.Server.MResultTuple = NamedTuple("MResultTuple", [("t", object)])
Z.Server.MResultTuple = NamedTuple("MResultTuple", [("r", object)])
