"""This is an automatically generated stub for `soil.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EFFQBgb/URmJEQ81P/8AAQoAAxEVghEZdxF1ZwAC/3NvaWwvc29pAWwuY2FwbnAAURwBAf8KtGH/yKPkwgARMTL/ZyXNxuEaOZ4AES1q/0/aOlvwQEaYABEtMv8NyiJ+CGVAvQARKTL/kIc6iBy/S98AESVi/ymcQZOlwmf/ABElQv/hZNwnFKeaoAARIUIfU1R5cGX/UHJvcGVydHkAD05hbWUfTGF5ZXIfUXVlcnn/UHJvZmlsZUQAB2F0YX9Qcm9maWxlf1NlcnZpY2VREAEC/yxfgL+e+ca5AFEoAgFBPAH/bPmw4/6jXowAUTgCAUFIAf/gK3kjEH+pvgBRRAIBQVAB/7VEDiYBtjDhAFFMAgFBcAEBDAAAEQGS/21hczo6c2NoAWVtYTo6c29pAWwAAAEMAAARAYL/bWFzLnNjaGUBbWEuc29pbAAAAAEMAAARASoPc29pbAAAAQwAADEBsgH/Z2l0aHViLmMFb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nbx8vc29pbAAA",  # soil/soil.capnp
    "EBpQBgb/CrRh/8ij5MIAERAC/1EZiREPNT//AAABMyUCkQIRFbIRHQcAABEZNwAB/3NvaWwvc29pAWwuY2FwbnA6H1NUeXBlUAEBUQgBAgAAERFCAAABAREJIgAAf3Vua25vd24Ha2E1",  # soil/soil.capnp:SType
    "EHVQBgb/ZyXNxuEaOZ4AERAC/1EZiREPNT//AAABM5MCyQcRFeoRIQcAADEd5wEAAf9zb2lsL3NvaQJsLmNhcG5wOlByb3BlcnR5D05hbWVQAQFRUAECAAAR6UoAAAEBEeUqAAABAhHdKgAAAQMR1SoAAAEEEc0aAAABBRHFSgAAAQYRwXIAAAEHEb1yAAABCBG5YgAAAQkRtVoAAAEKEbFyAAABCxGtsgAAAQwRrVoAAAENEalqAAABDjGlCgEAAAEPEa1KAAABEBGpQgAAARERoUIAAAESEZlyAAABExGVagAA/3NvaWxUeXBlAAAAD3NhbmQPY2xheQ9zaWx0A3BI/3NjZWxldG9uAAAA/29yZ2FuaWNDAB9hcmJvbv9vcmdhbmljTQAfYXR0ZXL/YnVsa0RlbnMAB2l0ef9yYXdEZW5zaQADdHn/ZmllbGRDYXAAH2FjaXR5/3Blcm1hbmVuAXRXaWx0aW5nH1BvaW50/3NhdHVyYXRpAANvbv9zb2lsTW9pcwAPdHVyZf9zb2lsV2F0ZQNyQ29uZHVjdGl2aXR5Q29lZmZpY2llbnQAAP9hbW1vbml1bQAAAH9uaXRyYXRlf2NuUmF0aW//aW5Hcm91bmQAH3dhdGVy/2ltcGVuZXRyAA9hYmxl",  # soil/soil.capnp:PropertyName
    "EElQBgb/T9o6W/BARpgAURABAf9RGYkRDzU//wAFAgcAADPLB5YJERWyER0XAAARKa8AAf9zb2lsL3NvaQFsLmNhcG5wOh9MYXllclEEAQH/sHHbzxu49JIAEQFK/1Byb3BlcnR5AAAAUQwDBAAABAEAABFFWgAAUUQDAVFgAgEBARQBAQAAEV0qAABRWAMBUWQCARECARQBAgAAEWFiAABRYAMBUWwCAf9wcm9wZXJ0aQADZXMBDgABUAMBARD/sHHbzxu49JIAAAEBDgABD3NpemUBCgACAQoAAf9kZXNjcmlwdAAHaW9uAQwAAgEMAAE=",  # soil/soil.capnp:Layer
    "EF9QBgb/sHHbzxu49JIAURYBAf9P2jpb8EBGmABFAQcEAQEz/wfJCBEV+hEhBwAAMR0fAQAB/3NvaWwvc29pAmwuY2FwbnA6TGF5ZXIuUHI/b3BlcnR5UAEBURQDBAAABAEAABF9KgAAUXgDAVGEAgEdAf//ARQBAQAAEYFKAABRgAMBUYwCAR0C/v8gFAECAAARiToAAFGEAwFRkAIBDQP9/xQBAwAAEY0qAABRiAMBUZQCAQ0E/P8UAQQAABGRMgAAUYwDAVGYAgEPbmFtZQEP/2clzcbhGjmeAAABAQ8AAf9mMzJWYWx1ZQAAAAEKAAIBCgABP2JWYWx1ZQEBAAIBAQABD3R5cGUBDAACAQwAAR91bnNldAAG",  # soil/soil.capnp:Layer.Property
    "EE1QBgb/DcoifghlQL0AURABAf9RGYkRDzU//wAFAgcAADOYCfkMERWyER0XAAARJa8AAf9zb2lsL3NvaQFsLmNhcG5wOh9RdWVyeVEEAQH/P5SIrQcbTr8AEQE6P1Jlc3VsdFEMAwQAAAQBAAARRVIAAFFEAwFRYAIBEQEBFAEBAAARXUoAAFFcAwFReAIBAQIUAQIBARF1YgAAUXQDAVGAAgH/bWFuZGF0b3IAAXkBDgABUAMBAQ//ZyXNxuEaOZ4AAAEBDgAB/29wdGlvbmFsAAAAAQ4AAVADAQEP/2clzcbhGjmeAAABAQ4AAf9vbmx5UmF3RAAHYXRhAQEAAgUBAQAB",  # soil/soil.capnp:Query
    "EEpQBgb/P5SIrQcbTr8AURYBAf8NyiJ+CGVAvQAFAgcAADM4CoYLERXqESEHAAARHa8AAf9zb2lsL3NvaQJsLmNhcG5wOlF1ZXJ5LlJlD3N1bHRQAQFRDAMEAAAEAQAAEUU6AABRQAMBUUwCAQEBFAEBAAARSVIAAFFIAwFRZAIBEQIBFAECAAARYUoAAFFgAwFRfAIBP2ZhaWxlZAEBAAIBAQAB/21hbmRhdG9yAAF5AQ4AAVADAQEP/2clzcbhGjmeAAABAQ4AAf9vcHRpb25hbAAAAAEOAAFQAwEBD/9nJc3G4Ro5ngAAAQEOAAE=",  # soil/soil.capnp:Query.Result
    "EDdQBgb/kIc6iBy/S98AURABAf9RGYkRDzU//wAFAQcAADP7DM4NERXiESEHAAARHXcAAf9zb2lsL3NvaQJsLmNhcG5wOlByb2ZpbGVEB2F0YVABAVEIAwQAAAQBAAARKToAAFEkAwFRQAIBAQEUAQEBARE9igAAUUADAVFMAgE/bGF5ZXJzAQ4AAVADAQEQ/0/aOlvwQEaYAAABAQ4AAf9wZXJjZW50YQFnZU9mQXJlYQAAAQoAAsEKyEIAAQ==",  # soil/soil.capnp:ProfileData
    "ECxQBgb/KZxBk6XCZ/8AERAD/1EZiREPNT//AAABM9ANuQ4RFcIRHQcAABEZhxFtJwAA/3NvaWwvc29pAmwuY2FwbnA6UHJvZmlsZQBQAQFRCAMFAAD/4nRjdJW2BOcBkIc6iBy/S98RMSoAAhElBwEB/1GRG/34IyqNAfuPzDkw/PHsERliAAIREQcPZGF0YUAB/2dlb0xvY2F0AAdpb25AAVEIAQH/1UicWcvRr7IAAAD/Zcs23KDap8EAAAA=",  # soil/soil.capnp:Profile
    "EBJQBgb/4nRjdJW2BOcAERgBAAAEBwABMRUiAQAE/3NvaWwvc29pA2wuY2FwbnA6UHJvZmlsZS5kYXRhJFBhcgdhbXM=",  # soil/soil.capnp:Profile.data$Params
    "EBNQBgb/UZEb/fgjKo0AERgBAAAEBwABMRVaAQAE/3NvaWwvc29pBGwuY2FwbnA6UHJvZmlsZS5nZW9Mb2NhdGlvbiRQYXJhA21z",  # soil/soil.capnp:Profile.geoLocation$Params
    "EDFQBgb/+4/MOTD88ewAUQ4BAv8k/Md5IFSQkAAEBwAAMxADfwMRFdIRIQcAABEddwAB/2dlby9nZW8uAmNhcG5wOkxhdExvbkNvb3IBZFABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBB2xhdAELAAIBCwABB2xvbgELAAIBCwAB",  # geo/geo.capnp:LatLonCoord
    "EExQBgb/4WTcJxSnmqAAERAD/1EZiREPNT//AAABM7sOMBIRFcIRHRcAADElBwER7ScAAP9zb2lsL3NvaQJsLmNhcG5wOlNlcnZpY2UAUQQBAf85yfuPVqv49AARATo/U3RyZWFtURADBQAA/w3KIn4IZUC9AT+UiK0HG06/EXHKAAIRcQcBAf8nfD7r2F/sjQHjftlqjr+imBFl0gACEWUHAQL/wZOWvznnl9sBrReTjGZekaARWZIAAhFVBwED/w3KIn4IZUC9AVd5K8lHQafREUmSAAIRRQf/Y2hlY2tBdmECaWxhYmxlUGFyYW1ldGVycwAAQAH/Z2V0QWxsQXYCYWlsYWJsZVBhcmFtZXRlcgFzQAH/Y2xvc2VzdFABcm9maWxlc0EBdEAB/3N0cmVhbUFsAWxQcm9maWxlAXNAAVEIAQH/1UicWcvRr7IAAAD/Zcs23KDap8EAAAA=",  # soil/soil.capnp:Service
    "EB9QBgb/Ocn7j1ar+PQAERgD/+Fk3CcUp5qgAAABMwsRyRERFfoRIQcAABEdRxFJBwAA/3NvaWwvc29pAmwuY2FwbnA6U2VydmljZS4/U3RyZWFtUAEBUQQDBQAA/wW8E/aNJNqBAfjdi3TC5HqfERFqAAIRCQf/bmV4dFByb2YAD2lsZXNAAVABAQ==",  # soil/soil.capnp:Service.Stream
    "ECVQBgb/BbwT9o0k2oEAUR8BAQAABAcAATEVmgEAARElPwAB/3NvaWwvc29pBWwuY2FwbnA6U2VydmljZS5TdHJlYW0ubmV4dFByb2ZpbGVzJFBhcmEDbXNRBAMEAAAEAQEBEQ1KAABRDAMBURgCAf9tYXhDb3VudAAAAAEFAAIBBQFkAAA=",  # soil/soil.capnp:Service.Stream.nextProfiles$Params
    "EClQBgb/+N2LdMLkep8AER8BAAAFAQcAATEVogEAARElPwAB/3NvaWwvc29pBWwuY2FwbnA6U2VydmljZS5TdHJlYW0ubmV4dFByb2ZpbGVzJFJlc3UHbHRzUQQDBAAABAEAABENSgAAUQwDAVEoAgH/cHJvZmlsZXMAAAABDgABUAMBARH/KZxBk6XCZ/8AAAEBDgAB",  # soil/soil.capnp:Service.Stream.nextProfiles$Results
    "ECZQBgb/J3w+69hf7I0AURgBAQAABAcAATEVygEAAREpPwAB/3NvaWwvc29pBmwuY2FwbnA6U2VydmljZS5nZXRBbGxBdmFpbGFibGVQYXJhbWV0ZXJzJFBhcmFtcwAAUQQDBAAABAEAABENYgAAUQwDAVEYAgH/b25seVJhd0QAB2F0YQEBAAIBAQAB",  # soil/soil.capnp:Service.getAllAvailableParameters$Params
    "ED5QBgb/437Zao6/opgAERgBAAAFAgcAATEV0gEAAREpdwAB/3NvaWwvc29pBmwuY2FwbnA6U2VydmljZS5nZXRBbGxBdmFpbGFibGVQYXJhbWV0ZXJzJFJlc3VsdAFzUQgDBAAABAEAABEpUgAAUSgDAVFEAgERAQEUAQEAABFBSgAAUUADAVFcAgH/bWFuZGF0b3IAAXkBDgABUAMBAQ//ZyXNxuEaOZ4AAAEBDgAB/29wdGlvbmFsAAAAAQ4AAVADAQEP/2clzcbhGjmeAAABAQ4AAQ==",  # soil/soil.capnp:Service.getAllAvailableParameters$Results
    "EDNQBgb/wZOWvznnl9sAERgBAAAFAgcAATEVigEAAREldwAB/3NvaWwvc29pBWwuY2FwbnA6U2VydmljZS5jbG9zZXN0UHJvZmlsZXNBdCRQYXJhbXMAAFEIAwQAAAQBAAARKTIAAFEkAwFRMAIBEQEBFAEBAAARLTIAAFEoAwFRNAIBH2Nvb3JkARD/+4/MOTD88ewAAAEBEAABH3F1ZXJ5ARD/DcoifghlQL0AAAEBEAAB",  # soil/soil.capnp:Service.closestProfilesAt$Params
    "EClQBgb/rReTjGZekaAAERgBAAAFAQcAATEVkgEAARElPwAB/3NvaWwvc29pBWwuY2FwbnA6U2VydmljZS5jbG9zZXN0UHJvZmlsZXNBdCRSZXN1bHQBc1EEAwQAAAQBAAARDUoAAFEMAwFRKAIB/3Byb2ZpbGVzAAAAAQ4AAVADAQER/ymcQZOlwmf/AAABAQ4AAQ==",  # soil/soil.capnp:Service.closestProfilesAt$Results
    "ECVQBgb/V3kryUdBp9EAERgBAAAFAQcAATEVkgEAARElPwAB/3NvaWwvc29pBWwuY2FwbnA6U2VydmljZS5zdHJlYW1BbGxQcm9maWxlcyRSZXN1bHQBc1EEAwQAAAQBAAARDWIAAFEMAwFRGAIB/2FsbFByb2ZpAAdsZXMBEf85yfuPVqv49AAAAQERAAE=",  # soil/soil.capnp:Service.streamAllProfiles$Results
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
SType = _EnumModule(_loader.get(0xC2E4A3C8FF61B40A).as_enum(), "SType")
PropertyName = _EnumModule(_loader.get(0x9E391AE1C6CD2567).as_enum(), "PropertyName")
Layer = _StructModule(_loader.get(0x984640F05B3ADA4F).as_struct(), "Layer")
Layer.Property = _StructModule(_loader.get(0x92F4B81BCFDB71B0).as_struct(), "Property")
Query = _StructModule(_loader.get(0xBD4065087E22CA0D).as_struct(), "Query")
Query.Result = _StructModule(_loader.get(0xBF4E1B07AD88943F).as_struct(), "Result")
ProfileData = _StructModule(_loader.get(0xDF4BBF1C883A8790).as_struct(), "ProfileData")
Profile = _InterfaceModule(_loader.get(0xFF67C2A593419C29).as_interface(), "Profile")
Service = _InterfaceModule(_loader.get(0xA09AA71427DC64E1).as_interface(), "Service")
Service.Stream = _InterfaceModule(
    _loader.get(0xF4F8AB568FFBC939).as_interface(),
    "Stream",
)

Profile.Server.DataResultTuple = NamedTuple(
    "DataResultTuple",
    [("layers", object), ("percentageOfArea", object)],
)
Profile.Server.GeolocationResultTuple = NamedTuple(
    "GeolocationResultTuple",
    [("lat", object), ("lon", object)],
)
Service.Server.CheckavailableparametersResultTuple = NamedTuple(
    "CheckavailableparametersResultTuple",
    [("failed", object), ("mandatory", object), ("optional", object)],
)
Service.Server.ClosestprofilesatResultTuple = NamedTuple(
    "ClosestprofilesatResultTuple",
    [("profiles", object)],
)
Service.Server.GetallavailableparametersResultTuple = NamedTuple(
    "GetallavailableparametersResultTuple",
    [("mandatory", object), ("optional", object)],
)
Service.Server.StreamallprofilesResultTuple = NamedTuple(
    "StreamallprofilesResultTuple",
    [("allProfiles", object)],
)
Service.Stream.Server.NextprofilesResultTuple = NamedTuple(
    "NextprofilesResultTuple",
    [("profiles", object)],
)
