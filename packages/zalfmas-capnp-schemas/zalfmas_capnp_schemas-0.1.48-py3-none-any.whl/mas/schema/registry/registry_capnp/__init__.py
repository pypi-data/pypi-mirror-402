"""This is an automatically generated stub for `registry.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EElQBgb/aYJ+nMPgG/4AARIAAxEVwhEdNxFJZwAC/3JlZ2lzdHJ5Ai9yZWdpc3RyeS5jYXBucABRDAEB/05XZnYj8wP1ABERMv+4MwZg0Ut7ygARDUr/6tHyNjz5rqsAEQ1SH0FkbWlu/1JlZ2lzdHJ5AAAA/1JlZ2lzdHJhAAFyURABAv8sX4C/nvnGuQBRKAIBQTwB/2z5sOP+o16MAFE4AgFBTAH/4Ct5IxB/qb4AUUgCAUFYAf+1RA4mAbYw4QBRVAIBQXwBAQwAABEBsv9tYXM6OnNjaAFlbWE6OnJlZx9pc3RyeQAAAQwAABEBov9tYXMuc2NoZQFtYS5yZWdpcwd0cnkAAAEMAAARAUr/cmVnaXN0cnkAAAEBDAAAMQHSAf9naXRodWIuYwZvbS96YWxmLXJwbS9tYXNfY2FwbnByb3RvX3NjaGVtYXMvZ2VuL2dvL3JlZ2lzdHIBeQAA",  # registry/registry.capnp
    "EE1QBgb/TldmdiPzA/UAERgD/2mCfpzD4Bv+AAABMz0C/wYRFfIRIQcAADEdRwER+RcAAP9yZWdpc3RyeQIvcmVnaXN0cnkuY2FwbnA6H0FkbWluUAEBURQDBQAA//aGhLH71BbbAbU1cnovgz29EZFiAAIRiQcBAf/W3oABjhu+1QEFj2wQA6GsqRF9egACEXUHAQL/w9tagAzVv44BX/TTfprXh9gRaWIAAhFhBwED/6Phfu5+saWWAbQNu1YG9pKgEVVyAAIRTQcBBP+1IYkUz/gs7gGt/X2r78pi/hFBSgACETkH/2FkZENhdGVnAAdvcnlAAf9yZW1vdmVDYQA/dGVnb3J5QAH/bW92ZU9iamUAB2N0c0AB/3JlbW92ZU9iAB9qZWN0c0AB/3JlZ2lzdHJ5AAAAQAFRBAEB/9VInFnL0a+yAAAA",  # registry/registry.capnp:Admin
    "EDRQBgb/9oaEsfvUFtsAUR4BAQAABQEHAAExFYoBAAERJXcAAf9yZWdpc3RyeQUvcmVnaXN0cnkuY2FwbnA6QWRtaW4uYWRkQ2F0ZWdvcnkkUGFyYW1zAABRCAMEAAAEAQAAESlKAABRKAMBUTQCAQEBFAEBAQERMToAAFEsAwFROAIB/2NhdGVnb3J5AAAAARD/09oD/st+y9QAAAEBEAABP3Vwc2VydAEBAAIBAQAB",  # registry/registry.capnp:Admin.addCategory$Params
    "EEJQBgb/09oD/st+y9QAERQB/8mKqHWnyfGZAAUDBwAAMzwBnwExFRIBESUHAAARIa8AAf9jb21tb24vYwNvbW1vbi5jYXBucDpJZEluZm9ybWF0aW8BblABAVEMAwQAAAQBAAARRRoAAFFAAwFRTAIBEQEBFAEBAAARSSoAAFFEAwFRUAIBEQICFAECAAARTWIAAFFMAwFRWAIBA2lkAQwAAgEMAAEPbmFtZQEMAAIBDAAB/2Rlc2NyaXB0AAdpb24BDAACAQwAAQ==",  # common/common.capnp:IdInformation
    "ECRQBgb/tTVyei+DPb0AUR4BAQAABAcAATEVkgEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5hZGRDYXRlZ29yeSRSZXN1bHQBc1EEAwQAAAQBAAARDUIAAFEIAwFRFAIBf3N1Y2Nlc3MBAQACAQEAAQ==",  # registry/registry.capnp:Admin.addCategory$Results
    "EDZQBgb/1t6AAY4bvtUAER4BAAAFAgcAATEVogEAAREldwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5yZW1vdmVDYXRlZ29yeSRQYXIHYW1zUQgDBAAABAEAABEpWgAAUSgDAVE0AgERAQEUAQEAABExwgAAUTQDAVFAAgH/Y2F0ZWdvcnkAA0lkAQwAAgEMAAH/bW92ZU9iamUCY3RzVG9DYXRlZ29yeUlkAAEMAAIBDAAB",  # registry/registry.capnp:Admin.removeCategory$Params
    "EClQBgb/BY9sEAOhrKkAER4BAAAFAQcAATEVqgEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5yZW1vdmVDYXRlZ29yeSRSZXMPdWx0c1EEAwQAAAQBAAARDXoAAFEMAwFRKAIB/3JlbW92ZWRPAD9iamVjdHMBDgABUAMBARH/1UicWcvRr7IAAAEBDgAB",  # registry/registry.capnp:Admin.removeCategory$Results
    "EB9QBgb/1UicWcvRr7IAERQD/8mKqHWnyfGZAAABM6EBEgIxFQoBESUHAAARIUcRSQcAAP9jb21tb24vYwNvbW1vbi5jYXBucDpJZGVudGlmaWFibGUAAFABAVEEAwUAAP+x3kkez6GKnQHT2gP+y37L1BERKgACEQUHD2luZm9AAVABAQ==",  # common/common.capnp:Identifiable
    "EBNQBgb/sd5JHs+hip0AESEBAAAEBwABMRVqAQAE/2NvbW1vbi9jBG9tbW9uLmNhcG5wOklkZW50aWZpYWJsZS5pbmZvJFBhD3JhbXM=",  # common/common.capnp:Identifiable.info$Params
    "EDhQBgb/w9tagAzVv44AER4BAAAFAgcAATEVigEAAREldwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5tb3ZlT2JqZWN0cyRQYXJhbXMAAFEIAwQAAAQBAAARKVIAAFEoAwFRRAIBEQEBFAEBAAARQUIAAFE8AwFRSAIB/29iamVjdElkAAFzAQ4AAVADAQEMAAIBDgABf3RvQ2F0SWQBDAACAQwAAQ==",  # registry/registry.capnp:Admin.moveObjects$Params
    "EClQBgb/X/TTfprXh9gAER4BAAAFAQcAATEVkgEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5tb3ZlT2JqZWN0cyRSZXN1bHQBc1EEAwQAAAQBAAARDXoAAFEMAwFRKAIB/21vdmVkT2JqAD9lY3RJZHMBDgABUAMBAQwAAgEOAAE=",  # registry/registry.capnp:Admin.moveObjects$Results
    "EClQBgb/o+F+7n6xpZYAER4BAAAFAQcAATEVmgEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5yZW1vdmVPYmplY3RzJFBhcmEDbXNRBAMEAAAEAQAAEQ1SAABRDAMBUSgCAf9vYmplY3RJZAABcwEOAAFQAwEBDAACAQ4AAQ==",  # registry/registry.capnp:Admin.removeObjects$Params
    "EClQBgb/tA27Vgb2kqAAER4BAAAFAQcAATEVogEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpBZG1pbi5yZW1vdmVPYmplY3RzJFJlc3UHbHRzUQQDBAAABAEAABENegAAUQwDAVEoAgH/cmVtb3ZlZE8AP2JqZWN0cwEOAAFQAwEBEf/VSJxZy9GvsgAAAQEOAAE=",  # registry/registry.capnp:Admin.removeObjects$Results
    "EBNQBgb/tSGJFM/4LO4AER4BAAAEBwABMRVyAQAE/3JlZ2lzdHJ5BC9yZWdpc3RyeS5jYXBucDpBZG1pbi5yZWdpc3RyeSRQH2FyYW1z",  # registry/registry.capnp:Admin.registry$Params
    "ECRQBgb/rf19q+/KYv4AER4BAAAFAQcAATEVegEAAREhPwAB/3JlZ2lzdHJ5BC9yZWdpc3RyeS5jYXBucDpBZG1pbi5yZWdpc3RyeSRSP2VzdWx0c1EEAwQAAAQBAAARDUoAAFEMAwFRGAIB/3JlZ2lzdHJ5AAAAARH/uDMGYNFLe8oAAAEBEQAB",  # registry/registry.capnp:Admin.registry$Results
    "EDtQBgb/uDMGYNFLe8oAERgD/2mCfpzD4Bv+AAABMwEHtAoxFQoBESUXAAARLccRsRcAAP9yZWdpc3RyeQMvcmVnaXN0cnkuY2FwbnA6UmVnaXN0cnkAAFEEAQH/E6z3DFGHecEAEQEyH0VudHJ5UQwDBQAA/5vCNF7m5kmcAbAwc4G1YL+yEVGiAAIRTQcBAf+dvEiy4YMSiQHT2gP+y37L1BFBagACETkHAQL/+sVRYXFT/J8BTQaGtG716uQRLUIAAhEhB/9zdXBwb3J0ZQFkQ2F0ZWdvcgdpZXNAAf9jYXRlZ29yeQAPSW5mb0ABf2VudHJpZXNAAVEEAQH/1UicWcvRr7IAAAA=",  # registry/registry.capnp:Registry
    "EFFQBgb/E6z3DFGHecEAESEB/7gzBmDRS3vKAAUEBwAAM8sIBAoxFToBESUHAAARIecAAf9yZWdpc3RyeQMvcmVnaXN0cnkuY2FwbnA6UmVnaXN0cnk/LkVudHJ5UAEBURADBAAABAEAABFhWgAAUWADAVFsAgERAQEUAQEAABFpIgAAUWQDAVFwAgERAgIUAQIAABFtKgAAUWgDAVF0AgERAwMUAQMAABFxGgAAUWwDAVF4AgH/Y2F0ZWdvcnkAA0lkAQwAAgEMAAEHcmVmARH/1UicWcvRr7IAAAEBEQABD25hbWUBDAACAQwAAQNpZAEMAAIBDAAB",  # registry/registry.capnp:Registry.Entry
    "EBVQBgb/m8I0XubmSZwAESEBAAAEBwABMRXiAQAE/3JlZ2lzdHJ5Bi9yZWdpc3RyeS5jYXBucDpSZWdpc3RyeS5zdXBwb3J0ZWRDYXRlZ29yaWVzJFBhcgdhbXM=",  # registry/registry.capnp:Registry.supportedCategories$Params
    "EClQBgb/sDBzgbVgv7IAESEBAAAFAQcAATEV6gEAAREpPwAB/3JlZ2lzdHJ5Bi9yZWdpc3RyeS5jYXBucDpSZWdpc3RyeS5zdXBwb3J0ZWRDYXRlZ29yaWVzJFJlcw91bHRzUQQDBAAABAEAABENKgAAUQgDAVEkAgEPY2F0cwEOAAFQAwEBEP/T2gP+y37L1AAAAQEOAAE=",  # registry/registry.capnp:Registry.supportedCategories$Results
    "ECVQBgb/nbxIsuGDEokAESEBAAAFAQcAATEVqgEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpSZWdpc3RyeS5jYXRlZ29yeUluZm8kUGEPcmFtc1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/2NhdGVnb3J5AANJZAEMAAIBDAAB",  # registry/registry.capnp:Registry.categoryInfo$Params
    "ECRQBgb/+sVRYXFT/J8AESEBAAAFAQcAATEVggEAAREhPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpSZWdpc3RyeS5lbnRyaWVzJFBhcmFtcwBRBAMEAAAEAQAAEQ1aAABRDAMBURgCAf9jYXRlZ29yeQADSWQBDAACAQwAAQ==",  # registry/registry.capnp:Registry.entries$Params
    "EChQBgb/TQaGtG716uQAESEBAAAFAQcAATEVigEAARElPwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpSZWdpc3RyeS5lbnRyaWVzJFJlc3VsdHMAAFEEAwQAAAQBAAARDUIAAFEIAwFRJAIBf2VudHJpZXMBDgABUAMBARD/E6z3DFGHecEAAAEBDgAB",  # registry/registry.capnp:Registry.entries$Results
    "EC9QBgb/6tHyNjz5rqsAERgD/2mCfpzD4Bv+AAABM7YKXg8xFRIBESU3AAARVUcRgRcAAP9yZWdpc3RyeQMvcmVnaXN0cnkuY2FwbnA6UmVnaXN0cmEBclEMAQH/DrJxft2YEaoAERGa/w37deoXR6jlABEVUv+JhFJiRH5ZxwARFVr/Q3Jvc3NEb20BYWluUmVzdG8DcmX/UmVnUGFyYW0AAXP/VW5yZWdpc3QAA2VyUQQDBQAA/w37deoXR6jlATwBxPCAsKmyERFKAAIRCQf/cmVnaXN0ZXIAAABAAVEEAQH/1UicWcvRr7IAAAA=",  # registry/registry.capnp:Registrar
    "EDVQBgb/DrJxft2YEaoAESIB/+rR8jY8+a6rAAUCBwAAM54LjQwxFaoBES0HAAARKXcAAf9yZWdpc3RyeQUvcmVnaXN0cnkuY2FwbnA6UmVnaXN0cmFyLkNyb3NzRG9tYWluUmVzD3RvcmVQAQFRCAMEAAAEAQAAESkyAABRJAMBUTACAREBARQBAQAAES1KAABRLAMBUTgCAR92YXRJZAEQ/43Ri9V0XQrhAAABARAAAf9yZXN0b3JlcgAAAAER/zwu2SeEIbafAAABAREAAQ==",  # registry/registry.capnp:Registrar.CrossDomainRestore
    "EFRQBgb/jdGL1XRdCuEAUR4BBP8ma19H0/5ehQAEBwAAM9QBDwMxFSIBESUHAAARIecAAf9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6VmEHdElkUAEBURADBAAABAEAABFhWgAAUWADAVFsAgERAQEUAQEAABFpWgAAUWgDAVF0AgERAgIUAQIAABFxWgAAUXADAVF8AgERAwMUAQMAABF5WgAAUXgDAVGEAgH/cHVibGljS2UAA3kwAQkAAgEJAAH/cHVibGljS2UAA3kxAQkAAgEJAAH/cHVibGljS2UAA3kyAQkAAgEJAAH/cHVibGljS2UAA3kzAQkAAgEJAAE=",  # persistence/persistence.capnp:VatId
    "ECNQBgb/PC7ZJ4Qhtp8AER4D/yZrX0fT/l6FAAABMyUR3BMxFToBESUXAAARMUcRWQcAAP9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UmU/c3RvcmVyUQQBAf861zdKduVBxQARAXL/UmVzdG9yZVAAH2FyYW1zUQQDBQAA/zrXN0p25UHFASVNLiUdbZbaERFCAAIRBQd/cmVzdG9yZUABUAEB",  # persistence/persistence.capnp:Restorer
    "EDZQBgb/Otc3SnblQcUAEScB/zwu2SeEIbafAAUCBwAAM2gRXRMxFaoBES0HAAARKXcAAf9wZXJzaXN0ZQVuY2UvcGVyc2lzdGVuY2UuY2FwbnA6UmVzdG9yZXIuUmVzdG9yZVBhD3JhbXNQAQFRCAMEAAAEAQAAESlKAABRKAMBUTQCAREBARQBAQAAETFKAABRMAMBUTwCAf9sb2NhbFJlZgAAAAEQ/4i0EX+0K0H6AAABARAAAf9zZWFsZWRCeQAAAAEQ/yN3yGDtmdf9AAABARAAAQ==",  # persistence/persistence.capnp:Restorer.RestoreParams
    "EDNQBgb/iLQRf7QrQfoAUSgBAf9N3oMdJ2htiABFAQcCAAAzuwpaCzEVcgERKQcAABEldwAB/3BlcnNpc3RlBG5jZS9wZXJzaXN0ZW5jZS5jYXBucDpTdHVyZHlSZWYuH1Rva2VuUAEBUQgDBAz//wQBAAARKSoAAFEkAwFRMAIBDQH+/xQBAQAAES0qAABRKAMBUTQCAQ90ZXh0AQwAAgEMAAEPZGF0YQENAAIBDQAB",  # persistence/persistence.capnp:SturdyRef.Token
    "ECRQBgb/I3fIYO2Z1/0AESgB/03egx0naG2IAAUBBwAAM0EJMQoxFXIBESkHAAARJT8AAf9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6U3R1cmR5UmVmLh9Pd25lclABAVEEAwQAAAQBAAARDSoAAFEIAwFRFAIBD2d1aWQBDAACAQwAAQ==",  # persistence/persistence.capnp:SturdyRef.Owner
    "ECRQBgb/JU0uJR1tltoAEScBAAAFAQcAATEVugEAARElPwAB/3BlcnNpc3RlBW5jZS9wZXJzaXN0ZW5jZS5jYXBucDpSZXN0b3Jlci5yZXN0b3JlJFI/ZXN1bHRzUQQDBAAABAEAABENIgAAUQgDAVEUAgEHY2FwARIEAwABARIAAQ==",  # persistence/persistence.capnp:Restorer.restore$Results
    "EFJQBgb/Dft16hdHqOUAESIB/+rR8jY8+a6rAAUEBwAAM5EMJQ0xFWIBESkHAAARJecAAf9yZWdpc3RyeQQvcmVnaXN0cnkuY2FwbnA6UmVnaXN0cmFyLlJlZ1BhcgdhbXNQAQFREAMEAAAEAQAAEWEiAABRXAMBUWgCAREBARQBAQAAEWVCAABRYAMBUWwCARECAhQBAgAAEWlaAABRaAMBUXQCAREDAxQBAwAAEXFCAABRbAMBUXgCAQdjYXABEf/VSJxZy9GvsgAAAQERAAF/cmVnTmFtZQEMAAIBDAAB/2NhdGVnb3J5AANJZAEMAAIBDAABf3hEb21haW4BEP8OsnF+3ZgRqgAAAQEQAAE=",  # registry/registry.capnp:Registrar.RegParams
    "ECFQBgb/iYRSYkR+WccAESID/+rR8jY8+a6rAAABMykNbA0xFWoBESkHAAARJUcRUQcAAP9yZWdpc3RyeQQvcmVnaXN0cnkuY2FwbnA6UmVnaXN0cmFyLlVucmVnaQ9zdGVyUAEBUQQDBQAA/34qN17foSPQAVQIG5i5ZpGhERFaAAIRCQf/dW5yZWdpc3QAA2VyQAFQAQE=",  # registry/registry.capnp:Registrar.Unregister
    "EBVQBgb/fio3Xt+hI9AAES0BAAAEBwABMRX6AQAE/3JlZ2lzdHJ5Bi9yZWdpc3RyeS5jYXBucDpSZWdpc3RyYXIuVW5yZWdpc3Rlci51bnJlZ2lzdGVyJD9QYXJhbXM=",  # registry/registry.capnp:Registrar.Unregister.unregister$Params
    "ECVQBgb/VAgbmLlmkaEAUS0BAQAABAcAATEVAgIAAREpPwAB/3JlZ2lzdHJ5By9yZWdpc3RyeS5jYXBucDpSZWdpc3RyYXIuVW5yZWdpc3Rlci51bnJlZ2lzdGVyJFJlc3VsdHMAUQQDBAAABAEAABENQgAAUQgDAVEUAgF/c3VjY2VzcwEBAAIBAQAB",  # registry/registry.capnp:Registrar.Unregister.unregister$Results
    "EDNQBgb/PAHE8ICwqbIAESIBAAAFAgcAATEVmgEAAREldwAB/3JlZ2lzdHJ5BS9yZWdpc3RyeS5jYXBucDpSZWdpc3RyYXIucmVnaXN0ZXIkUmVzdWwDdHNRCAMEAAAEAQAAESkyAABRJAMBUTACAREBARQBAQAAES1CAABRKAMBUTQCAR91bnJlZwER/4mEUmJEflnHAAABAREAAX9yZXJlZ1NSARD/Td6DHSdobYgAAAEBEAAB",  # registry/registry.capnp:Registrar.register$Results
    "EDlQBgb/Td6DHSdobYgAER4B/yZrX0fT/l6FAAUCBwAAM54IXAsxFUIBESUnAAAROXcAAf9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6U3R1cmR5UmVmAFEIAQH/I3fIYO2Z1/0AEQky/4i0EX+0K0H6ABEFMh9Pd25lch9Ub2tlblEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLUoAAFEsAwFROAIBB3ZhdAEQ/4eAxNvyzezZAAABARAAAf9sb2NhbFJlZgAAAAEQ/4i0EX+0K0H6AAABARAAAQ==",  # persistence/persistence.capnp:SturdyRef
    "EDJQBgb/h4DE2/LN7NkAER4B/yZrX0fT/l6FAAUCBwAAM78HnAgxFTIBESUHAAARIXcAAf9wZXJzaXN0ZQNuY2UvcGVyc2lzdGVuY2UuY2FwbnA6VmEfdFBhdGhQAQFRCAMEAAAEAQAAESkaAABRJAMBUTACAREBARQBAQAAES1CAABRKAMBUTQCAQNpZAEQ/43Ri9V0XQrhAAABARAAAX9hZGRyZXNzARD/DVugcQaBR/sAAAEBEAAB",  # persistence/persistence.capnp:VatPath
    "EDpQBgb/DVugcQaBR/sAUR4BA/8ma19H0/5ehQBFAQcCAQkzEQO9BzEVMgERJQcAABEhrwAB/3BlcnNpc3RlA25jZS9wZXJzaXN0ZW5jZS5jYXBucDpBZB9kcmVzc1ABAVEMAwQM//8BAf9piokoBF2yjwARRSIAAhECCBQBAgAAES0qAABRKAMBUTQCAQ0B/v8UAQMAABExKgAAUSwDAVE4AgEHaXA2D3BvcnQBBwACAQcAAQ9ob3N0AQwAAgEMAAE=",  # persistence/persistence.capnp:Address
    "EDJQBgb/aYqJKARdso8AUSYBA/8NW6BxBoFH+wAVAQcBAAExFVIBAAERIXcAAf9wZXJzaXN0ZQRuY2UvcGVyc2lzdGVuY2UuY2FwbnA6QWRkcmVzcy5pcAE2UQgDBAAABAEAABEpQgAAUSQDAVEwAgERAQEUAQEAABEtQgAAUSgDAVE0AgF/bG93ZXI2NAEJAAIBCQABf3VwcGVyNjQBCQACAQkAAQ==",  # persistence/persistence.capnp:Address.ip6
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
Admin = _InterfaceModule(_loader.get(0xF503F3237666574E).as_interface(), "Admin")
Registry = _InterfaceModule(_loader.get(0xCA7B4BD1600633B8).as_interface(), "Registry")
Registry.Entry = _StructModule(_loader.get(0xC17987510CF7AC13).as_struct(), "Entry")
Registrar = _InterfaceModule(
    _loader.get(0xABAEF93C36F2D1EA).as_interface(),
    "Registrar",
)
Registrar.CrossDomainRestore = _StructModule(
    _loader.get(0xAA1198DD7E71B20E).as_struct(),
    "CrossDomainRestore",
)
Registrar.RegParams = _StructModule(
    _loader.get(0xE5A84717EA75FB0D).as_struct(),
    "RegParams",
)
Registrar.Unregister = _InterfaceModule(
    _loader.get(0xC7597E4462528489).as_interface(),
    "Unregister",
)

Admin.Server.AddcategoryResultTuple = NamedTuple(
    "AddcategoryResultTuple",
    [("success", object)],
)
Admin.Server.MoveobjectsResultTuple = NamedTuple(
    "MoveobjectsResultTuple",
    [("movedObjectIds", object)],
)
Admin.Server.RegistryResultTuple = NamedTuple(
    "RegistryResultTuple",
    [("registry", object)],
)
Admin.Server.RemovecategoryResultTuple = NamedTuple(
    "RemovecategoryResultTuple",
    [("removedObjects", object)],
)
Admin.Server.RemoveobjectsResultTuple = NamedTuple(
    "RemoveobjectsResultTuple",
    [("removedObjects", object)],
)
Registrar.Server.RegisterResultTuple = NamedTuple(
    "RegisterResultTuple",
    [("unreg", object), ("reregSR", object)],
)
Registrar.Unregister.Server.UnregisterResultTuple = NamedTuple(
    "UnregisterResultTuple",
    [("success", object)],
)
Registry.Server.CategoryinfoResultTuple = NamedTuple(
    "CategoryinfoResultTuple",
    [("id", object), ("name", object), ("description", object)],
)
Registry.Server.EntriesResultTuple = NamedTuple(
    "EntriesResultTuple",
    [("entries", object)],
)
Registry.Server.SupportedcategoriesResultTuple = NamedTuple(
    "SupportedcategoriesResultTuple",
    [("cats", object)],
)
