"""This is an automatically generated stub for `service.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EEtQBgb/wMa70pjfKvUAARAAAxEVshEdRxFVZwAC/3NlcnZpY2UvAXNlcnZpY2UuH2NhcG5wURABAf9J9o0Zi/jB/gARGTL/yxPCIpKCpasAERVy/3+cJpy57LCKABEVQv92ki4jWGRfzQAREVIfQWRtaW7/U2ltcGxlRmEAH2N0b3J5f0ZhY3Rvcnn/U3RvcHBhYmwAAWVREAEC/yxfgL+e+ca5AFEoAgFBPAH/bPmw4/6jXowAUTgCAUFMAf/gK3kjEH+pvgBRSAIBQVQB/7VEDiYBtjDhAFFQAgFBeAEBDAAAEQGq/21hczo6c2NoAWVtYTo6c2VyD3ZpY2UAAAEMAAARAZr/bWFzLnNjaGUBbWEuc2VydmkDY2UAAAEMAAARAUJ/c2VydmljZQAAAQwAADEBygH/Z2l0aHViLmMGb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nby9zZXJ2aWNlAAE=",  # service/service.capnp
    "EExQBgb/SfaNGYv4wf4AERYD/8DGu9KY3yr1AAABM7IBEwQRFeIRIQcAADEdRwER9RcAAP9zZXJ2aWNlLwJzZXJ2aWNlLmNhcG5wOkFkB21pblABAVEUAwUAAP808ufaG/Mn1gFZl1SukCIc4BGRUgACEYkHAQH//RARaYo1v5oBwUvHGkoZ/dYRfVoAAhF1BwEC/3hb7zfN08PdAYeXdT4GGirOEWkqAAIRXQcBA/+WWCmNYnFC/wGYs9t4hT1C9RFRWgACEUkHAQT/g7potvlyhNwBLKviCNt5XrERPXoAAhE1B/9oZWFydGJlYQABdEAB/3NldFRpbWVvAAN1dEABD3N0b3BAAf9pZGVudGl0aQADZXNAAf91cGRhdGVJZAA/ZW50aXR5QAFRBAEB/9VInFnL0a+yAAAA",  # service/service.capnp:Admin
    "EBNQBgb/NPLn2hvzJ9YAERwBAAAEBwABMRVqAQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uaGVhcnRiZWF0JFBhD3JhbXM=",  # service/service.capnp:Admin.heartbeat$Params
    "EBNQBgb/WZdUrpAiHOAAERwBAAAEBwABMRVyAQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uaGVhcnRiZWF0JFJlH3N1bHRz",  # service/service.capnp:Admin.heartbeat$Results
    "ECNQBgb//RARaYo1v5oAURwBAQAABAcAATEVcgEAAREhPwAB/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uc2V0VGltZW91dCRQH2FyYW1zUQQDBAAABAEAABENQgAAUQgDAVEUAgF/c2Vjb25kcwEJAAIBCQAB",  # service/service.capnp:Admin.setTimeout$Params
    "EBNQBgb/wUvHGkoZ/dYAERwBAAAEBwABMRV6AQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uc2V0VGltZW91dCRSP2VzdWx0cw==",  # service/service.capnp:Admin.setTimeout$Results
    "EBJQBgb/eFvvN83Tw90AERwBAAAEBwABMRVCAQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uc3RvcCRQYXJhbXMA",  # service/service.capnp:Admin.stop$Params
    "EBNQBgb/h5d1PgYaKs4AERwBAAAEBwABMRVKAQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uc3RvcCRSZXN1bHRzAAA=",  # service/service.capnp:Admin.stop$Results
    "EBNQBgb/llgpjWJxQv8AERwBAAAEBwABMRVyAQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uaWRlbnRpdGllcyRQH2FyYW1z",  # service/service.capnp:Admin.identities$Params
    "ECdQBgb/mLPbeIU9QvUAERwBAAAFAQcAATEVegEAAREhPwAB/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6QWRtaW4uaWRlbnRpdGllcyRSP2VzdWx0c1EEAwQAAAQBAAARDTIAAFEIAwFRJAIBH2luZm9zAQ4AAVADAQEQ/9PaA/7LfsvUAAABAQ4AAQ==",  # service/service.capnp:Admin.identities$Results
    "EEJQBgb/09oD/st+y9QAERQB/8mKqHWnyfGZAAUDBwAAMzwBnwExFRIBESUHAAARIa8AAf9jb21tb24vYwNvbW1vbi5jYXBucDpJZEluZm9ybWF0aW8BblABAVEMAwQAAAQBAAARRRoAAFFAAwFRTAIBEQEBFAEBAAARSSoAAFFEAwFRUAIBEQICFAECAAARTWIAAFFMAwFRWAIBA2lkAQwAAgEMAAEPbmFtZQEMAAIBDAAB/2Rlc2NyaXB0AAdpb24BDAACAQwAAQ==",  # common/common.capnp:IdInformation
    "EDNQBgb/g7potvlyhNwAERwBAAAFAgcAATEVkgEAAREldwAB/3NlcnZpY2UvBXNlcnZpY2UuY2FwbnA6QWRtaW4udXBkYXRlSWRlbnRpdHkkUGFyYW0Bc1EIAwQAAAQBAAARKTIAAFEkAwFRMAIBEQEBFAEBAAARLUIAAFEoAwFRNAIBH29sZElkAQwAAgEMAAF/bmV3SW5mbwEQ/9PaA/7LfsvUAAABARAAAQ==",  # service/service.capnp:Admin.updateIdentity$Params
    "EBRQBgb/LKviCNt5XrEAERwBAAAEBwABMRWaAQAE/3NlcnZpY2UvBXNlcnZpY2UuY2FwbnA6QWRtaW4udXBkYXRlSWRlbnRpdHkkUmVzdWwDdHM=",  # service/service.capnp:Admin.updateIdentity$Results
    "ECFQBgb/yxPCIpKCpasAERYD/8DGu9KY3yr1AAABMxUEMwUxFSIBESUHAAARIUcRSRcAAP9zZXJ2aWNlLwNzZXJ2aWNlLmNhcG5wOlNpbXBsZUZhY3QHb3J5UAEBUQQDBQAA/9223GDcbymoAaoe3uAoOKOJERE6AAIRBQc/Y3JlYXRlQAFRBAEB/9VInFnL0a+yAAAA",  # service/service.capnp:SimpleFactory
    "EBRQBgb/3bbcYNxvKagAESQBAAAEBwABMRWSAQAE/3NlcnZpY2UvBXNlcnZpY2UuY2FwbnA6U2ltcGxlRmFjdG9yeS5jcmVhdGUkUGFyYW0Bcw==",  # service/service.capnp:SimpleFactory.create$Params
    "EChQBgb/qh7e4Cg4o4kAESQBAAAFAQcAATEVmgEAARElPwAB/3NlcnZpY2UvBXNlcnZpY2UuY2FwbnA6U2ltcGxlRmFjdG9yeS5jcmVhdGUkUmVzdWwDdHNRBAMEAAAEAQAAEQ0qAABRCAMBUSQCAQ9jYXBzAQ4AAVADAQER/9VInFnL0a+yAAABAQ4AAQ==",  # service/service.capnp:SimpleFactory.create$Results
    "EB9QBgb/1UicWcvRr7IAERQD/8mKqHWnyfGZAAABM6EBEgIxFQoBESUHAAARIUcRSQcAAP9jb21tb24vYwNvbW1vbi5jYXBucDpJZGVudGlmaWFibGUAAFABAVEEAwUAAP+x3kkez6GKnQHT2gP+y37L1BERKgACEQUHD2luZm9AAVABAQ==",  # common/common.capnp:Identifiable
    "EBNQBgb/sd5JHs+hip0AESEBAAAEBwABMRVqAQAE/2NvbW1vbi9jBG9tbW9uLmNhcG5wOklkZW50aWZpYWJsZS5pbmZvJFBhD3JhbXM=",  # common/common.capnp:Identifiable.info$Params
    "EEtQBgb/f5wmnLnssIoAERYD/8DGu9KY3yr1AAAAEAEzNQWzCREV8hEhJwAAET2HEeUXEe0P/3NlcnZpY2UvAnNlcnZpY2UuY2FwbnA6RmEfY3RvcnlRCAEB/5eRqswXhbjCABEJav8utnzfU2qBuQARCVr/Q3JlYXRlUGEAD3JhbXP/QWNjZXNzSW4AA2ZvUQgDBQAA/5eRqswXhbjCAS62fN9TaoG5ETE6AABBLAFBPAERTQcBAf8qiLMqNWfV1AEFz9y1J8FiqRFBsgAAQUQBQVQBEWUHP2NyZWF0ZREBH1EEAgH/f5wmnLnssIoAAQEAABEBH1EEAgH/f5wmnLnssIoAAQEAAEAB/3NlcnZpY2VJAW50ZXJmYWNlH05hbWVzEQEfUQQCAf9/nCacueywigABAQAAEQEfUQQCAf9/nCacueywigABAQAAQAFRBAEB/9VInFnL0a+yAAAAQQQBEQFCf1BheWxvYWQ=",  # service/service.capnp:Factory
    "EF1QBgb/l5GqzBeFuMIAUR4BAf9/nCacueywigAFAgcQATPhBTIHMRVaAREpBwAAESWvAAH/c2VydmljZS8Ec2VydmljZS5jYXBucDpGYWN0b3J5LkNyZWF0ZVBhcmEDbXNQAQFRDAMEAAAEAQEBEUV6AABRRAMBUVACAQEBFAEBAAARTdIAAFFUAwFRuAIBEQIBFAECAAARtVoAAFG0AwFRwAIB/3RpbWVvdXRTAD9lY29uZHMBCQACAQkDEA4AAP9pbnRlcmZhYwJlTmFtZVRvUmVnaXN0cnlTAVIBDgABUAMBARD/M0cXJUeG1LkAAABAAREBH1EEAgH/M0cXJUeG1LkAAAARASdRCAEBAQFRCAMBAQFREAMBAQwAAgEMAAIBDgAB/21zZ1BheWxvAANhZAESAQH/f5wmnLnssIoAAAABEgAB",  # service/service.capnp:Factory.CreateParams
    "EDZQBgb/M0cXJUeG1LkAERQB/8mKqHWnyfGZAAUCBxABM5MIwggRFcoRIQcAABEddwAAEZEX/2NvbW1vbi9jAm9tbW9uLmNhcG5wOlBhaXIAAFABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBB2ZzdAESAQH/M0cXJUeG1LkAAAABEgABB3NuZAESBQEB/zNHFyVHhtS5AAAAARIAAUEIAREFEhEFEgFGAVM=",  # common/common.capnp:Pair
    "EEhQBgb/LrZ831NqgbkAER4B/3+cJpy57LCKAAUDBxABMzYHRwgxFUoBESkHAAARJa8AAf9zZXJ2aWNlLwRzZXJ2aWNlLmNhcG5wOkZhY3RvcnkuQWNjZXNzSW5mbwAAUAEBUQwDBAAABAEAABFFSgAAUUQDAVFQAgERAQEUAQEAABFNYgAAUUwDAVFoAgERAgIUAQIAABFlMgAAUWADAVFsAgH/YWRtaW5DYXAAAAABEgQDAAEBEgAB/3NlcnZpY2VDAAdhcHMBDgABUAMBARH/1UicWcvRr7IAAAEBDgABH2Vycm9yAQwAAgEMAAE=",  # service/service.capnp:Factory.AccessInfo
    "EBVQBgb/KoizKjVn1dQAER4BAAAEBxABAAAxFdoBAAT/c2VydmljZS8Gc2VydmljZS5jYXBucDpGYWN0b3J5LnNlcnZpY2VJbnRlcmZhY2VOYW1lcyRQYXJhA21z",  # service/service.capnp:Factory.serviceInterfaceNames$Params
    "EClQBgb/Bc/ctSfBYqkAER4BAAAFAQcQAQAAMRXiAQABESk/AAH/c2VydmljZS8Gc2VydmljZS5jYXBucDpGYWN0b3J5LnNlcnZpY2VJbnRlcmZhY2VOYW1lcyRSZXN1B2x0c1EEAwQAAAQBAAARDTIAAFEIAwFRJAIBH25hbWVzAQ4AAVADAQEMAAIBDgAB",  # service/service.capnp:Factory.serviceInterfaceNames$Results
    "EB5QBgb/dpIuI1hkX80AERYD/8DGu9KY3yr1AAABM7UJEAoxFQIBESEHAAARHUcRRQcAAP9zZXJ2aWNlLwNzZXJ2aWNlLmNhcG5wOlN0b3BwYWJsZQBQAQFRBAMFAAD/korUFs6Pr5QB2M+UwoRlxNIRESoAAhEFBw9zdG9wQAFQAQE=",  # service/service.capnp:Stoppable
    "EBNQBgb/korUFs6Pr5QAESABAAAEBwABMRViAQAE/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6U3RvcHBhYmxlLnN0b3AkUGFyB2Ftcw==",  # service/service.capnp:Stoppable.stop$Params
    "ECNQBgb/2M+UwoRlxNIAUSABAQAABAcAATEVagEAAREhPwAB/3NlcnZpY2UvBHNlcnZpY2UuY2FwbnA6U3RvcHBhYmxlLnN0b3AkUmVzD3VsdHNRBAMEAAAEAQAAEQ1CAABRCAMBURQCAX9zdWNjZXNzAQEAAgEBAAE=",  # service/service.capnp:Stoppable.stop$Results
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
Admin = _InterfaceModule(_loader.get(0xFEC1F88B198DF649).as_interface(), "Admin")
SimpleFactory = _InterfaceModule(
    _loader.get(0xABA5829222C213CB).as_interface(),
    "SimpleFactory",
)
Factory = _InterfaceModule(_loader.get(0x8AB0ECB99C269C7F).as_interface(), "Factory")
Factory.CreateParams = _StructModule(
    _loader.get(0xC2B88517CCAA9197).as_struct(),
    "CreateParams",
)
Factory.AccessInfo = _StructModule(
    _loader.get(0xB9816A53DF7CB62E).as_struct(),
    "AccessInfo",
)
Stoppable = _InterfaceModule(
    _loader.get(0xCD5F6458232E9276).as_interface(),
    "Stoppable",
)

Admin.Server.IdentitiesResultTuple = NamedTuple(
    "IdentitiesResultTuple",
    [("infos", object)],
)
Factory.Server.CreateResultTuple = NamedTuple(
    "CreateResultTuple",
    [("adminCap", object), ("serviceCaps", object), ("error", object)],
)
Factory.Server.ServiceinterfacenamesResultTuple = NamedTuple(
    "ServiceinterfacenamesResultTuple",
    [("names", object)],
)
SimpleFactory.Server.CreateResultTuple = NamedTuple(
    "CreateResultTuple",
    [("caps", object)],
)
Stoppable.Server.StopResultTuple = NamedTuple("StopResultTuple", [("success", object)])
