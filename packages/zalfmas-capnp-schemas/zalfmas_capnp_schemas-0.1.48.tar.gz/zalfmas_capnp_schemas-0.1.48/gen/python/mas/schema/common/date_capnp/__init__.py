"""This is an automatically generated stub for `date.capnp`."""

import base64

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "ED9QBgb/KvYHi8Mr6ugAAQwAAxEVkhEdFxEpZwAC/2NvbW1vbi9kAWF0ZS5jYXBuAXBRBAEB/40RIgOs/uaXABEBKg9EYXRlURABAv8sX4C/nvnGuQBRKAIBQTwB/2z5sOP+o16MAFE4AgFBTAH/4Ct5IxB/qb4AUUgCAUFUAf+1RA4mAbYw4QBRUAIBQXQBAQwAABEBov9tYXM6OnNjaAFlbWE6OmNvbQdtb24AAAEMAAARAZL/bWFzLnNjaGUBbWEuY29tbW8BbgAAAQwAABEBOj9jb21tb24AAAEMAAAxAcIB/2dpdGh1Yi5jBm9tL3phbGYtcnBtL21hc19jYXBucHJvdG9fc2NoZW1hcy9nZW4vZ28vY29tbW9uAAAA",  # common/date.capnp
    "ED9QBgb/jREiA6z+5pcAURIBAf8q9geLwyvq6AAEBwAAMzwBJAIRFboRHQcAABEZrwAB/2NvbW1vbi9kAWF0ZS5jYXBuP3A6RGF0ZVABAVEMAwQAAAQBAAARRSoAAFFAAwFRTAIBEQECFAEBAAARSTIAAFFEAwFRUAIBEQIDFAECAAARTSIAAFFIAwFRVAIBD3llYXIBAwACAQMAAR9tb250aAEGAAIBBgABB2RheQEGAAIBBgAB",  # common/date.capnp:Date
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
Date = _StructModule(_loader.get(0x97E6FEAC0322118D).as_struct(), "Date")
