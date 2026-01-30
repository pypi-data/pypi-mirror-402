"""This is an automatically generated stub for `soil_params.capnp`."""

import base64

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EE1QBgb/q5Z5dKCsPPgAARkAAxEV+hEhNxFhZwAC/21vZGVsL21vAm5pY2Evc29pbF9wYXJhbXM/LmNhcG5wUQwBAf+BIk4wJyJo/AAREbr/U7vlsJsK6+QAERXa/0vSs2vJmxabABEdkv9Tb2lsQ2hhcgFhY3RlcmlzdD9pY0RhdGH/U29pbENoYXICYWN0ZXJpc3RpY01vZGlmaQNlcv9DYXBpbGxhcgF5UmlzZVJhdAFlURABAv8sX4C/nvnGuQBRKAIBQTwB/2z5sOP+o16MAFE4AgFBSAH/4Ct5IxB/qb4AUUQCAUFQAf+1RA4mAbYw4QBRTAIBQXQBAQwAABEBkv9tYXM6OnNjaAFlbWE6OnNvaQFsAAABDAAAEQGC/21hcy5zY2hlAW1hLnNvaWwAAAABDAAAEQE6P21vbmljYQAAAQwAADEB8gH/Z2l0aHViLmMGb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nby9tb2RlbC9tH29uaWNhAAA=",  # model/monica/soil_params.capnp
    "ECxQBgb/gSJOMCciaPwAER8B/6uWeXSgrDz4AAUBBwAAMz4BagIxFbIBES0XAAARNT8AAf9tb2RlbC9tbwVuaWNhL3NvaWxfcGFyYW1zLmNhcG5wOlNvaWxDaGFyYWN0ZXJpc3RpH2NEYXRhUQQBAf9j2yXgV6v66gARASoPRGF0YVEEAwQAAAQBAAARDSoAAFEIAwFRJAIBD2xpc3QBDgABUAMBARD/Y9sl4Fer+uoAAAEBDgAB",  # model/monica/soil_params.capnp:SoilCharacteristicData
    "EGdQBgb/Y9sl4Fer+uoAUTYBAf+BIk4wJyJo/AAFAQcAADNiAU8CMRXaARExBwAAMS0fAQAB/21vZGVsL21vBm5pY2Evc29pbF9wYXJhbXMuY2FwbnA6U29pbENoYXJhY3RlcmlzdGljRGF0YS5EYQN0YVABAVEUAwQAAAQBAAARfUoAAFF8AwFRiAIBAQEUAQEAABGFegAAUYQDAVGQAgERAgIUAQIAABGNYgAAUYwDAVGYAgERAwMUAQMAABGVcgAAUZQDAVGgAgERBAQUAQQAABGdegAAUZwDAVGoAgH/c29pbFR5cGUAAAABDAACAQwAAf9zb2lsUmF3RAA/ZW5zaXR5AQMAAgEDAAH/YWlyQ2FwYWMAB2l0eQEGAAIBBgAB/2ZpZWxkQ2FwAB9hY2l0eQEGAAIBBgAB/25GaWVsZENhAD9wYWNpdHkBBgACAQYAAQ==",  # model/monica/soil_params.capnp:SoilCharacteristicData.Data
    "EC1QBgb/U7vlsJsK6+QAER8B/6uWeXSgrDz4AAUBBwAAM2wClQMxFdIBETEXAAAROT8AAf9tb2RlbC9tbwZuaWNhL3NvaWxfcGFyYW1zLmNhcG5wOlNvaWxDaGFyYWN0ZXJpc3RpY01vZGlmaWUBclEEAQH/tLHozWykaKkAEQEqD0RhdGFRBAMEAAAEAQAAEQ0qAABRCAMBUSQCAQ9saXN0AQ4AAVADAQEQ/7Sx6M1spGipAAABAQ4AAQ==",  # model/monica/soil_params.capnp:SoilCharacteristicModifier
    "EGdQBgb/tLHozWykaKkAUToBAf9Tu+Wwmwrr5AAFAQcAADOUAnoDMRX6ARExBwAAMS0fAQAB/21vZGVsL21vBm5pY2Evc29pbF9wYXJhbXMuY2FwbnA6U29pbENoYXJhY3RlcmlzdGljTW9kaWZpZT9yLkRhdGFQAQFRFAMEAAAEAQAAEX1KAABRfAMBUYgCAQEBFAEBAAARhXIAAFGEAwFRkAIBEQIEFAECAAARjWIAAFGMAwFRmAIBEQMFFAEDAAARlXIAAFGUAwFRoAIBEQQGFAEEAAARnXoAAFGcAwFRqAIB/3NvaWxUeXBlAAAAAQwAAgEMAAH/b3JnYW5pY00AH2F0dGVyAQoAAgEKAAH/YWlyQ2FwYWMAB2l0eQECAAIBAgAB/2ZpZWxkQ2FwAB9hY2l0eQECAAIBAgAB/25GaWVsZENhAD9wYWNpdHkBAgACAQIAAQ==",  # model/monica/soil_params.capnp:SoilCharacteristicModifier.Data
    "ECxQBgb/S9Kza8mbFpsAER8B/6uWeXSgrDz4AAUBBwAAM5cDSAQxFYoBES0XAAARNT8AAf9tb2RlbC9tbwVuaWNhL3NvaWxfcGFyYW1zLmNhcG5wOkNhcGlsbGFyeVJpc2VSYXRlAABRBAEB/12IrY/FiYq3ABEBKg9EYXRhUQQDBAAABAEAABENKgAAUQgDAVEkAgEPbGlzdAEOAAFQAwEBEP9diK2PxYmKtwAAAQEOAAE=",  # model/monica/soil_params.capnp:CapillaryRiseRate
    "EEVQBgb/XYitj8WJircAUTEBAf9L0rNryZsWmwAFAQcAADO2Ay0EMRWyAREtBwAAESmvAAH/bW9kZWwvbW8FbmljYS9zb2lsX3BhcmFtcy5jYXBucDpDYXBpbGxhcnlSaXNlUmF0ZR8uRGF0YVABAVEMAwQAAAQBAAARRUoAAFFEAwFRUAIBAQEUAQEAABFNSgAAUUwDAVFYAgERAgEUAQIAABFVKgAAUVADAVFcAgH/c29pbFR5cGUAAAABDAACAQwAAf9kaXN0YW5jZQAAAAEGAAIBBgABD3JhdGUBCgACAQoAAQ==",  # model/monica/soil_params.capnp:CapillaryRiseRate.Data
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
SoilCharacteristicData = _StructModule(
    _loader.get(0xFC682227304E2281).as_struct(),
    "SoilCharacteristicData",
)
SoilCharacteristicData.Data = _StructModule(
    _loader.get(0xEAFAAB57E025DB63).as_struct(),
    "Data",
)
SoilCharacteristicModifier = _StructModule(
    _loader.get(0xE4EB0A9BB0E5BB53).as_struct(),
    "SoilCharacteristicModifier",
)
SoilCharacteristicModifier.Data = _StructModule(
    _loader.get(0xA968A46CCDE8B1B4).as_struct(),
    "Data",
)
CapillaryRiseRate = _StructModule(
    _loader.get(0x9B169BC96BB3D24B).as_struct(),
    "CapillaryRiseRate",
)
CapillaryRiseRate.Data = _StructModule(
    _loader.get(0xB78A89C58FAD885D).as_struct(),
    "Data",
)
