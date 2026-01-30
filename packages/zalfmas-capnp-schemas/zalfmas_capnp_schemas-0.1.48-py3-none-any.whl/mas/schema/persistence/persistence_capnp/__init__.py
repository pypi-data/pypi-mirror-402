"""This is an automatically generated stub for `persistence.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EGZQBgb/JmtfR9P+XoUAARgAAxEV8hEhpxG5ZwAC/3BlcnNpc3RlAm5jZS9wZXJzaXN0ZW5jZS4fY2FwbnBRKAEB/43Ri9V0XQrhABFJMv8NW6BxBoFH+wARRUL/h4DE2/LN7NkAEUFC/03egx0naG2IABE9Uv86ykfR+r2znwARPVL/Zcs23KDap8EAET1a/zwu2SeEIbafABE9Sv+fHdC2+pGNqgARPYr/7ScvYAosnI8AEUFC/41gN98vIlOCABE9mh9WYXRJZH9BZGRyZXNzf1ZhdFBhdGj/U3R1cmR5UmUAAWb/SGVhcnRiZWEAAXT/UGVyc2lzdGUAA250/1Jlc3RvcmVyAAAA/0hvc3RQb3J0AVJlc29sdmVyAAB/R2F0ZXdhef9HYXRld2F5UgFlZ2lzdHJhYgNsZVEQAQL/LF+Av575xrkAUSgCAUFAAf9s+bDj/qNejABRPAIBQVAB/+AreSMQf6m+AFFMAgFBXAH/tUQOJgG2MOEAUVgCAUGAAQEMAAARAcr/bWFzOjpzY2gCZW1hOjpwZXJzaXN0ZW5jZQABAQwAABEBuv9tYXMuc2NoZQFtYS5wZXJzaT9zdGVuY2UAAAEMAAARAWL/cGVyc2lzdGUAB25jZQAAAQwAADEB6gH/Z2l0aHViLmMGb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nby9wZXJzaXN0D2VuY2UAAA==",  # persistence/persistence.capnp
    "EFRQBgb/jdGL1XRdCuEAUR4BBP8ma19H0/5ehQAEBwAAM9QBDwMxFSIBESUHAAARIecAAf9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6VmEHdElkUAEBURADBAAABAEAABFhWgAAUWADAVFsAgERAQEUAQEAABFpWgAAUWgDAVF0AgERAgIUAQIAABFxWgAAUXADAVF8AgERAwMUAQMAABF5WgAAUXgDAVGEAgH/cHVibGljS2UAA3kwAQkAAgEJAAH/cHVibGljS2UAA3kxAQkAAgEJAAH/cHVibGljS2UAA3kyAQkAAgEJAAH/cHVibGljS2UAA3kzAQkAAgEJAAE=",  # persistence/persistence.capnp:VatId
    "EDpQBgb/DVugcQaBR/sAUR4BA/8ma19H0/5ehQBFAQcCAQkzEQO9BzEVMgERJQcAABEhrwAB/3BlcnNpc3RlA25jZS9wZXJzaXN0ZW5jZS5jYXBucDpBZB9kcmVzc1ABAVEMAwQM//8BAf9piokoBF2yjwARRSIAAhECCBQBAgAAES0qAABRKAMBUTQCAQ0B/v8UAQMAABExKgAAUSwDAVE4AgEHaXA2D3BvcnQBBwACAQcAAQ9ob3N0AQwAAgEMAAE=",  # persistence/persistence.capnp:Address
    "EDJQBgb/aYqJKARdso8AUSYBA/8NW6BxBoFH+wAVAQcBAAExFVIBAAERIXcAAf9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6QWRkcmVzcy5pcAE2UQgDBAAABAEAABEpQgAAUSQDAVEwAgERAQEUAQEAABEtQgAAUSgDAVE0AgF/bG93ZXI2NAEJAAIBCQABf3VwcGVyNjQBCQACAQkAAQ==",  # persistence/persistence.capnp:Address.ip6
    "EDJQBgb/h4DE2/LN7NkAER4B/yZrX0fT/l6FAAUCBwAAM78HnAgxFTIBESUHAAARIXcAAf9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6VmEfdFBhdGhQAQFRCAMEAAAEAQAAESkaAABRJAMBUTACAREBARQBAQAAES1CAABRKAMBUTQCAQNpZAEQ/43Ri9V0XQrhAAABARAAAX9hZGRyZXNzARD/DVugcQaBR/sAAAEBEAAB",  # persistence/persistence.capnp:VatPath
    "EDlQBgb/Td6DHSdobYgAER4B/yZrX0fT/l6FAAUCBwAAM54IXAsxFUIBESUnAAAROXcAAf9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6U3R1cmR5UmVmAFEIAQH/I3fIYO2Z1/0AEQky/4i0EX+0K0H6ABEFMh9Pd25lch9Ub2tlblEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLUoAAFEsAwFROAIBB3ZhdAEQ/4eAxNvyzezZAAABARAAAf9sb2NhbFJlZgAAAAEQ/4i0EX+0K0H6AAABARAAAQ==",  # persistence/persistence.capnp:SturdyRef
    "ECRQBgb/I3fIYO2Z1/0AESgB/03egx0naG2IAAUBBwAAM0EJMQoxFXIBESkHAAARJT8AAf9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6U3R1cmR5UmVmLh9Pd25lclABAVEEAwQAAAQBAAARDSoAAFEIAwFRFAIBD2d1aWQBDAACAQwAAQ==",  # persistence/persistence.capnp:SturdyRef.Owner
    "EDNQBgb/iLQRf7QrQfoAUSgBAf9N3oMdJ2htiABFAQcCAAAzuwpaCzEVcgERKQcAABEldwAB/3BlcnNpc3RlBG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpTdHVyZHlSZWYuH1Rva2VuUAEBUQgDBAz//wQBAAARKSoAAFEkAwFRMAIBDQH+/xQBAQAAES0qAABRKAMBUTQCAQ90ZXh0AQwAAgEMAAEPZGF0YQENAAIBDQAB",  # persistence/persistence.capnp:SturdyRef.Token
    "EB9QBgb/OspH0fq9s58AER4D/yZrX0fT/l6FAAABM14LiQsxFUIBESUHAAARIUcRSQcAAP9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6SGVhcnRiZWF0AFABAVEEAwUAAP/KNKG/2oq2igH4FeimwoI29BERKgACEQUHD2JlYXRAAVABAQ==",  # persistence/persistence.capnp:Heartbeat
    "EBRQBgb/yjShv9qKtooAESgBAAAEBwABMRWiAQAE/3BlcnNpc3RlBW5jZS9wZXJzaXN0ZW5jZS5jYXBucDpIZWFydGJlYXQuYmVhdCRQYXIHYW1z",  # persistence/persistence.capnp:Heartbeat.beat$Params
    "EBRQBgb/+BXopsKCNvQAESgBAAAEBwABMRWqAQAE/3BlcnNpc3RlBW5jZS9wZXJzaXN0ZW5jZS5jYXBucDpIZWFydGJlYXQuYmVhdCRSZXMPdWx0cw==",  # persistence/persistence.capnp:Heartbeat.beat$Results
    "EC1QBgb/Zcs23KDap8EAER4D/yZrX0fT/l6FAAABM4sLIxExFUoBESk3AAARWUcRgQcAAP9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UGVyc2lzdGVudAAAUQwBAf9DA14ixKrg1QAREVr/E+wsmO/RW9wAERFi/1IunxaBD3CPABERiv9TYXZlUGFyYQADbXP/U2F2ZVJlc3UAB2x0c/9SZWxlYXNlUwF0dXJkeVJlZgAAUQQDBQAA/0MDXiLEquDVARPsLJjv0VvcEREqAAIRBQcPc2F2ZUABUAEB",  # persistence/persistence.capnp:Persistent
    "ECVQBgb/QwNeIsSq4NUAESkB/2XLNtyg2qfBAAUBBwAAM+UMlQ4xFaIBES0HAAARKT8AAf9wZXJzaXN0ZQVuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UGVyc2lzdGVudC5TYXZlUGFyB2Ftc1ABAVEEAwQAAAQBAAARDUIAAFEIAwFRFAIBf3NlYWxGb3IBEP8jd8hg7ZnX/QAAAQEQAAE=",  # persistence/persistence.capnp:Persistent.SaveParams
    "EDZQBgb/E+wsmO/RW9wAESkB/2XLNtyg2qfBAAUCBwAAM5gOwRAxFaoBES0HAAARKXcAAf9wZXJzaXN0ZQVuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UGVyc2lzdGVudC5TYXZlUmVzD3VsdHNQAQFRCAMEAAAEAQAAESlSAABRKAMBUTQCAREBARQBAQAAETFKAABRMAMBUTwCAf9zdHVyZHlSZQABZgEQ/03egx0naG2IAAABARAAAf91bnNhdmVTUgAAAAEQ/03egx0naG2IAAABARAAAQ==",  # persistence/persistence.capnp:Persistent.SaveResults
    "ECxQBgb/Ui6fFoEPcI8AESkD/2XLNtyg2qfBAAABM8UQIRExFdIBETEHAAARLUcRfQcAAP9wZXJzaXN0ZQZuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UGVyc2lzdGVudC5SZWxlYXNlU3R1cmR5UmUBZlABAVEEAwUAAP8VfIDZIIzbpAFT6BAk424tkxERQhERHwABES0Hf3JlbGVhc2VRBAEC//GNLxcSYLnCAFEEAgFBFAEBDAAAEQFS/3JlbGVhc2VTAAFSAABAAVABAQ==",  # persistence/persistence.capnp:Persistent.ReleaseSturdyRef
    "EBdQBgb/FXyA2SCM26QAEToBAAAEBwABMRVKAgAE/3BlcnNpc3RlCG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpQZXJzaXN0ZW50LlJlbGVhc2VTdHVyZHlSZWYucmVsZWFzZSRQYXJhbXMAAA==",  # persistence/persistence.capnp:Persistent.ReleaseSturdyRef.release$Params
    "ECdQBgb/U+gQJONuLZMAUToBAQAABAcAATEVUgIAARExPwAB/3BlcnNpc3RlCG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpQZXJzaXN0ZW50LlJlbGVhc2VTdHVyZHlSZWYucmVsZWFzZSRSZXN1bHQBc1EEAwQAAAQBAAARDUIAAFEIAwFRFAIBf3N1Y2Nlc3MBAQACAQEAAQ==",  # persistence/persistence.capnp:Persistent.ReleaseSturdyRef.release$Results
    "ECNQBgb/PC7ZJ4Qhtp8AER4D/yZrX0fT/l6FAAABMyUR3BMxFToBESUXAAARMUcRWQcAAP9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UmU/c3RvcmVyUQQBAf861zdKduVBxQARAXL/UmVzdG9yZVAAH2FyYW1zUQQDBQAA/zrXN0p25UHFASVNLiUdbZbaERFCAAIRBQd/cmVzdG9yZUABUAEB",  # persistence/persistence.capnp:Restorer
    "EDZQBgb/Otc3SnblQcUAEScB/zwu2SeEIbafAAUCBwAAM2gRXRMxFaoBES0HAAARKXcAAf9wZXJzaXN0ZQVuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UmVzdG9yZXIuUmVzdG9yZVBhD3JhbXNQAQFRCAMEAAAEAQAAESlKAABRKAMBUTQCAREBARQBAQAAETFKAABRMAMBUTwCAf9sb2NhbFJlZgAAAAEQ/4i0EX+0K0H6AAABARAAAf9zZWFsZWRCeQAAAAEQ/yN3yGDtmdf9AAABARAAAQ==",  # persistence/persistence.capnp:Restorer.RestoreParams
    "ECRQBgb/JU0uJR1tltoAEScBAAAFAQcAATEVugEAARElPwAB/3BlcnNpc3RlBW5jZS9wZXJzaXN0ZW5jZS5jYXBucDpSZXN0b3Jlci5yZXN0b3JlJFI/ZXN1bHRzUQQDBAAABAEAABENIgAAUQgDAVEUAgEHY2FwARIEAwABARIAAQ==",  # persistence/persistence.capnp:Restorer.restore$Results
    "EDJQBgb/nx3QtvqRjaoAER4D/yZrX0fT/l6FAAABM94TCBoxFXoBESkXAAARNUcRhScAAP9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6SG9zdFBvcnRSZT9zb2x2ZXJRBAEB/7KQRnB198qwABEBUv9SZWdpc3RyYQABclEEAwUAAP8zuywPb5b45gGMCyKNUV8Y/BERQhERHwABES0Hf3Jlc29sdmVRBAEC//GNLxcSYLnCAFEEAgFBFAEBDAAAEQFq/1Jlc29sdmVJAA9kZW50AABAAVEIAQH/1UicWcvRr7IAAAD/PC7ZJ4Qhtp8AAAA=",  # persistence/persistence.capnp:HostPortResolver
    "ECdQBgb/spBGcHX3yrAAES8D/58d0Lb6kY2qAAABM6oUXRkxFcoBETEXAAARPUcRaQcAAP9wZXJzaXN0ZQZuY2UvcGVyc2lzdGVuY2UuY2FwbnA6SG9zdFBvcnRSZXNvbHZlci5SZWdpc3RyYXIAAFEEAQH/Dw1G/2KPAb8AEQF6/1JlZ2lzdGVyAD9QYXJhbXNRBAMFAAD/Dw1G/2KPAb8BuYv5M2aB/PoREUoAAhEJB/9yZWdpc3RlcgAAAEABUAEB",  # persistence/persistence.capnp:HostPortResolver.Registrar
    "EGVQBgb/Dw1G/2KPAb8AUTkBAf+ykEZwdffKsAAFBAcAADMrFZMXMRVCAhE1BwAAMTEfAQAB/3BlcnNpc3RlCG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpIb3N0UG9ydFJlc29sdmVyLlJlZ2lzdHJhci5SZWdpc3RlclBhcmFtcwBQAQFRFAMEAAAEAQAAEX1iAABRfAMBUYgCAREBARQBAQAAEYUqAABRgAMBUYwCAQECFAECAAARiSoAAFGEAwFRkAIBEQMCFAEDAAARjTIAAFGIAwFRlAIBEQQDFAEEAAARkXIAAFGQAwFRnAIB/2Jhc2U2NFZhAAd0SWQBDAACAQwAAQ9ob3N0AQwAAgEMAAEPcG9ydAEHAAIBBwABH2FsaWFzAQwAAgEMAAH/aWRlbnRpdHkAH1Byb29mAQ0AAgENAAE=",  # persistence/persistence.capnp:HostPortResolver.Registrar.RegisterParams
    "EDlQBgb/uYv5M2aB/PoAUTkBAQAABQEHAAExFVICAAERMXcAAf9wZXJzaXN0ZQhuY2UvcGVyc2lzdGVuY2UuY2FwbnA6SG9zdFBvcnRSZXNvbHZlci5SZWdpc3RyYXIucmVnaXN0ZXIkUmVzdWx0AXNRCAMEAAAEAQAAESlSAABRKAMBUTQCAQEBFAEBAAARMbIAAFE0AwFRQAIB/2hlYXJ0YmVhAAF0ARH/OspH0fq9s58AAAEBEQAB/3NlY3NIZWFyAXRiZWF0SW50H2VydmFsAQgAAgEIAAE=",  # persistence/persistence.capnp:HostPortResolver.Registrar.register$Results
    "ECVQBgb/M7ssD2+W+OYAES8BAAAFAQcAATEV8gEAAREpPwAB/3BlcnNpc3RlBm5jZS9wZXJzaXN0ZW5jZS5jYXBucDpIb3N0UG9ydFJlc29sdmVyLnJlc29sdmUkUB9hcmFtc1EEAwQAAAQBAAARDRoAAFEIAwFRFAIBA2lkAQwAAgEMAAE=",  # persistence/persistence.capnp:HostPortResolver.resolve$Params
    "EDRQBgb/jAsijVFfGPwAUS8BAQAABQEHAAExFfoBAAERKXcAAf9wZXJzaXN0ZQZuY2UvcGVyc2lzdGVuY2UuY2FwbnA6SG9zdFBvcnRSZXNvbHZlci5yZXNvbHZlJFI/ZXN1bHRzUQgDBAAABAEAABEpKgAAUSQDAVEwAgEBARQBAQAAES0qAABRKAMBUTQCAQ9ob3N0AQwAAgEMAAEPcG9ydAEHAAIBBwAB",  # persistence/persistence.capnp:HostPortResolver.resolve$Results
    "EChQBgb/7ScvYAosnI8AER4D/yZrX0fT/l6FAAABMwoanh4xFTIBESUXAAARMUcRXScAAP9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6R2EfdGV3YXlRBAEB/6p/6XldxjKiABEBWv9SZWdSZXN1bAADdHNRBAMFAAD/q6tErykVjMcBqn/peV3GMqIREUoAAhEJB/9yZWdpc3RlcgAAAEABUQgBAf/VSJxZy9GvsgAAAP88LtknhCG2nwAAAA==",  # persistence/persistence.capnp:Gateway
    "EEdQBgb/qn/peV3GMqIAUSYBAf/tJy9gCiycjwAFAgcAADNDHJweMRWKAREtBwAAESmvAAH/cGVyc2lzdGUFbmNlL3BlcnNpc3RlbmNlLmNhcG5wOkdhdGV3YXkuUmVnUmVzdWx0cwAAUAEBUQwDBAAABAEAABFFUgAAUUQDAVFQAgERAQEUAQEAABFNUgAAUUwDAVFYAgEBAhQBAgAAEVWyAABRWAMBUWQCAf9zdHVyZHlSZQABZgEQ/03egx0naG2IAAABARAAAf9oZWFydGJlYQABdAER/zrKR9H6vbOfAAABAREAAf9zZWNzSGVhcgF0YmVhdEludB9lcnZhbAEIAAIBCAAB",  # persistence/persistence.capnp:Gateway.RegResults
    "EDRQBgb/q6tErykVjMcAESYBAAAFAgcAATEVsgEAAREldwAB/3BlcnNpc3RlBW5jZS9wZXJzaXN0ZW5jZS5jYXBucDpHYXRld2F5LnJlZ2lzdGVyJFAfYXJhbXNRCAMEAAAEAQAAESkiAABRJAMBUTACAREBARQBAQAAES1aAABRLAMBUTgCAQdjYXABEgQDAAEBEgAB/3NlY3JldFNlAANlZAEMAAIBDAAB",  # persistence/persistence.capnp:Gateway.register$Params
    "ECNQBgb/jWA33y8iU4IAER4D/yZrX0fT/l6FAAABM6Ae6R8xFYoBES0HAAARKUcRWQcAAP9wZXJzaXN0ZQVuY2UvcGVyc2lzdGVuY2UuY2FwbnA6R2F0ZXdheVJlZ2lzdHJhYmxlAABQAQFRBAMFAAD/RJ230nhdTLYBtvDueoawuPcREZoAAhENB/9zdHVyZHlSZQFmQXRHYXRldwNheUABUAEB",  # persistence/persistence.capnp:GatewayRegistrable
    "EDhQBgb/RJ230nhdTLYAETEBAAAFAgcAATEVWgIAARExdwAB/3BlcnNpc3RlCG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpHYXRld2F5UmVnaXN0cmFibGUuc3R1cmR5UmVmQXRHYXRld2F5JFBhcmEDbXNRCAMEAAAEAQAAESlSAABRKAMBUTQCAREBARQBAQAAETFSAABRMAMBUTwCAf9nYXRld2F5UwABUgEQ/03egx0naG2IAAABARAAAf9nYXRld2F5SQABZAEMAAIBDAAB",  # persistence/persistence.capnp:GatewayRegistrable.sturdyRefAtGateway$Params
    "EChQBgb/tvDueoawuPcAETEBAAAFAQcAATEVYgIAARExPwAB/3BlcnNpc3RlCG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpHYXRld2F5UmVnaXN0cmFibGUuc3R1cmR5UmVmQXRHYXRld2F5JFJlc3UHbHRzUQQDBAAABAEAABENggAAUQwDAVEYAgH/c2VsZkF0R2EBdGV3YXlTUgABEP9N3oMdJ2htiAAAAQEQAAE=",  # persistence/persistence.capnp:GatewayRegistrable.sturdyRefAtGateway$Results
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
VatId = _StructModule(_loader.get(0xE10A5D74D58BD18D).as_struct(), "VatId")
Address = _StructModule(_loader.get(0xFB47810671A05B0D).as_struct(), "Address")
VatPath = _StructModule(_loader.get(0xD9ECCDF2DBC48087).as_struct(), "VatPath")
SturdyRef = _StructModule(_loader.get(0x886D68271D83DE4D).as_struct(), "SturdyRef")
SturdyRef.Owner = _StructModule(_loader.get(0xFDD799ED60C87723).as_struct(), "Owner")
SturdyRef.Token = _StructModule(_loader.get(0xFA412BB47F11B488).as_struct(), "Token")
Heartbeat = _InterfaceModule(
    _loader.get(0x9FB3BDFAD147CA3A).as_interface(),
    "Heartbeat",
)
Persistent = _InterfaceModule(
    _loader.get(0xC1A7DAA0DC36CB65).as_interface(),
    "Persistent",
)
Persistent.SaveParams = _StructModule(
    _loader.get(0xD5E0AAC4225E0343).as_struct(),
    "SaveParams",
)
Persistent.SaveResults = _StructModule(
    _loader.get(0xDC5BD1EF982CEC13).as_struct(),
    "SaveResults",
)
Persistent.ReleaseSturdyRef = _InterfaceModule(
    _loader.get(0x8F700F81169F2E52).as_interface(),
    "ReleaseSturdyRef",
)
Restorer = _InterfaceModule(_loader.get(0x9FB6218427D92E3C).as_interface(), "Restorer")
Restorer.RestoreParams = _StructModule(
    _loader.get(0xC541E5764A37D73A).as_struct(),
    "RestoreParams",
)
HostPortResolver = _InterfaceModule(
    _loader.get(0xAA8D91FAB6D01D9F).as_interface(),
    "HostPortResolver",
)
HostPortResolver.Registrar = _InterfaceModule(
    _loader.get(0xB0CAF775704690B2).as_interface(),
    "Registrar",
)
HostPortResolver.Registrar.RegisterParams = _StructModule(
    _loader.get(0xBF018F62FF460D0F).as_struct(),
    "RegisterParams",
)
Gateway = _InterfaceModule(_loader.get(0x8F9C2C0A602F27ED).as_interface(), "Gateway")
Gateway.RegResults = _StructModule(
    _loader.get(0xA232C65D79E97FAA).as_struct(),
    "RegResults",
)
GatewayRegistrable = _InterfaceModule(
    _loader.get(0x8253222FDF37608D).as_interface(),
    "GatewayRegistrable",
)

Gateway.Server.RegisterResultTuple = NamedTuple(
    "RegisterResultTuple",
    [("sturdyRef", object), ("heartbeat", object), ("secsHeartbeatInterval", object)],
)
GatewayRegistrable.Server.SturdyrefatgatewayResultTuple = NamedTuple(
    "SturdyrefatgatewayResultTuple",
    [("selfAtGatewaySR", object)],
)
HostPortResolver.Server.ResolveResultTuple = NamedTuple(
    "ResolveResultTuple",
    [("host", object), ("port", object)],
)
HostPortResolver.Registrar.Server.RegisterResultTuple = NamedTuple(
    "RegisterResultTuple",
    [("heartbeat", object), ("secsHeartbeatInterval", object)],
)
Persistent.Server.SaveResultTuple = NamedTuple(
    "SaveResultTuple",
    [("sturdyRef", object), ("unsaveSR", object)],
)
Persistent.ReleaseSturdyRef.Server.ReleaseResultTuple = NamedTuple(
    "ReleaseResultTuple",
    [("success", object)],
)
Restorer.Server.RestoreResultTuple = NamedTuple("RestoreResultTuple", [("cap", object)])
