"""This is an automatically generated stub for `web_berest_data_import.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EFpQBgb/m7drgqJotMQAASYAAzEVYgERKRcROZcAAv9tb2RlbC93ZQRiZXJlc3Qvd2ViX2JlcmVzdF9kYXRhX2ltcG9ydC5jYQdwbnBRBAEB/2+qPhSdraShABEBYv9EV0xBQkltcAAHb3J0URgBAv8sX4C/nvnGuQBRQAIBQVgB/2z5sOP+o16MAFFUAgFBbAH/lrWzA/jI5J4AUWgCAUF4Af/TfB+ItGsGmwBRdAIBQYgB/+AreSMQf6m+AFGEAgFBlAH/tUQOJgG2MOEAUZACAUG4AQEMAAARAer/bWFzOjpzY2gCZW1hOjptb2RlbDo6d2ViZQ9yZXN0AAABDAAAEQHS/21hcy5zY2hlAm1hLm1vZGVsLndlYmVyZXMBdAAAAQwAABEBYv9kZS56YWxmLgAHbWFzAAABDAAAEQGa/1dlYkJlcmVzAXREV0RJbXBvA3J0AAABDAAAEQFK/3dlYmVyZXN0AAABAQwAADEBAgL/Z2l0aHViLmMHb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nby9tb2RlbC93ZWJlcmVzdAAAAA==",  # model/weberest/web_berest_data_import.capnp
    "ECJQBgb/b6o+FJ2tpKEAESwD/5u3a4KiaLTEAAABM8sBSAIxFcIBES0HAAARKUcRVQcAAP9tb2RlbC93ZQZiZXJlc3Qvd2ViX2JlcmVzdF9kYXRhX2ltcG9ydC5jYXBucDpEV0xBQkltcG9ydABQAQFRBAMFAAD/0scjqiyXA+sBB8r8SYxWvLkREVoAAhEJB/9pbXBvcnREYQADdGFAAVABAQ==",  # model/weberest/web_berest_data_import.capnp:DWLABImport
    "EEVQBgb/0scjqiyXA+sAETgBAAAFAwcAATEVUgIAARExrwAB/21vZGVsL3dlCGJlcmVzdC93ZWJfYmVyZXN0X2RhdGFfaW1wb3J0LmNhcG5wOkRXTEFCSW1wb3J0LmltcG9ydERhdGEkUGFyYW0Bc1EMAwQAAAQBAAARRRoAAFFAAwFRTAIBEQEBFAEBAAARSSoAAFFEAwFRUAIBEQICFAECAAARTSoAAFFIAwFRVAIBA2lkAQwAAgEMAAEPZHdsYQENAAIBDQABD2R3bGIBDQACAQ0AAQ==",  # model/weberest/web_berest_data_import.capnp:DWLABImport.importData$Params
    "EEdQBgb/B8r8SYxWvLkAUTgBAQAABQEHAAExFVoCAAERMa8AAf9tb2RlbC93ZQhiZXJlc3Qvd2ViX2JlcmVzdF9kYXRhX2ltcG9ydC5jYXBucDpEV0xBQkltcG9ydC5pbXBvcnREYXRhJFJlc3VsA3RzUQwDBAAABAEAABFFGgAAUUADAVFMAgEBARQBAQAAEUlKAABRSAMBUVQCARECARQBAgAAEVFKAABRUAMBUVwCAQNpZAEMAAIBDAAB/3N1Y2Nlc3NBAAAAAQEAAgEBAAH/c3VjY2Vzc0IAAAABAQACAQEAAQ==",  # model/weberest/web_berest_data_import.capnp:DWLABImport.importData$Results
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
DWLABImport = _InterfaceModule(
    _loader.get(0xA1A4AD9D143EAA6F).as_interface(),
    "DWLABImport",
)

DWLABImport.Server.ImportdataResultTuple = NamedTuple(
    "ImportdataResultTuple",
    [("id", object), ("successA", object), ("successB", object)],
)
