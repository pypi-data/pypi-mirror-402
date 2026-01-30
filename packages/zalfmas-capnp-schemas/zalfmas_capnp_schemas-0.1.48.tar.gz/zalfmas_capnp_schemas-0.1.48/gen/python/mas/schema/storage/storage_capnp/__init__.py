"""This is an automatically generated stub for `storage.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EEBQBgb/nbOdS7PQVZcAARAAAxEVshEdFxEpZwAC/3N0b3JhZ2UvAXN0b3JhZ2UuH2NhcG5wUQQBAf8GbziiipWf5gARATIfU3RvcmVREAEC/yxfgL+e+ca5AFEoAgFBPAH/bPmw4/6jXowAUTgCAUFMAf/gK3kjEH+pvgBRSAIBQVQB/7VEDiYBtjDhAFFQAgFBeAEBDAAAEQGq/21hczo6c2NoAWVtYTo6c3RvD3JhZ2UAAAEMAAARAZr/bWFzLnNjaGUBbWEuc3RvcmEDZ2UAAAEMAAARAUJ/c3RvcmFnZQAAAQwAADEBygH/Z2l0aHViLmMGb20vemFsZi1ycG0vbWFzX2NhcG5wcm90b19zY2hlbWFzL2dlbi9nby9zdG9yYWdlAAE=",  # storage/storage.capnp
    "EF1QBgb/Bm84ooqVn+YAERYD/52znUuz0FWXAAABM7YBSRARFeIRITcAADFVRwETMQEnAAD/c3RvcmFnZS8Cc3RvcmFnZS5jYXBucDpTdAdvcmVRDAEB/2KuZ1X0MYGHABERUv7CPvB+IuzqERGK/0Lx0u8sJn2EABEViv9Db250YWluZQABcv9JbmZvQW5kQwFvbnRhaW5lcgAA/0ltcG9ydEV4AXBvcnREYXRhAABRFAMFAAD/9psrZ024TLwBrJeZOr9JI/MRkWoAAhGJBwEB/0QnjZ/Hvhf1AeVFVNquJq+yEX2CAAIRdQcBAv9uzvxmIelmpAH5VqJdaCYk+BFpegACEWEHAQP/UiS2f55Pvr8BDgCFJjhgBKoRVYIAAhFNBwEE/zKrFwLEXj66Ac+JrHUmGo+JEUGCAAIROQf/bmV3Q29udGEAD2luZXJAAf9jb250YWluZQFyV2l0aElkAEAB/2xpc3RDb250AD9haW5lcnNAAf9yZW1vdmVDbwFudGFpbmVyAEAB/2ltcG9ydENvAW50YWluZXIAQAFRCAEB/9VInFnL0a+yAAAA/2XLNtyg2qfBAAAA",  # storage/storage.capnp:Store
    "EGtQBgb/Yq5nVfQxgYcAERwD/wZvOKKKlZ/mAAABMxkCWgwxFTIBESUnAAAxPccBE2kBJwAA/3N0b3JhZ2UvA3N0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udB9haW5lclEIAQH/wHj0ez4kGvoAEQky/zDC//KmWefvABEFYh9FbnRyef9LZXlBbmRFbgAHdHJ5URwDBQAA/17MIr6JiBOeAe7JUXNNhBSpEdE6AAIRxQcBAf+UCWOOFxT8kwFm0QHEmjHk/xG5ggACEbEHAQL/sTNpjCgK99sBcjgIA7rTKKARpWIAAhGdBwED/2nWOrRdHRbEAUa4cKlk18GbEZFKAAIRiQcBBf/OxXqycJHp/QG/t2RfyTjZ+xF9YgACEXUHAQb/e4J71vhxHMMBrf+bwt8nb+sRaTIAAhFdBwEE3xKDnO397/v/VJ66f3NXO4gAEVFKAAIRSQc/ZXhwb3J0QAH/ZG93bmxvYWQBRW50cmllcwBAAf9saXN0RW50cgAHaWVzQAH/Z2V0RW50cnkAAABAAf9yZW1vdmVFbgAHdHJ5QAEfY2xlYXJAAf9hZGRFbnRyeQAAAEABUQgBAf/VSJxZy9GvsgAAAP9lyzbcoNqnwQAAAA==",  # storage/storage.capnp:Store.Container
    "EDlQBgb/wHj0ez4kGvoAESYD/2KuZ1X0MYGHAAABM4MCZAgxFWIBESkXAAARMccRsQcAAP9zdG9yYWdlLwRzdG9yYWdlLmNhcG5wOlN0b3JlLkNvbnRhaW5lci5Fbgd0cnlRBAEB/1yPkknEXBjiABEBMh9WYWx1ZVEMAwUAAP8K0EKp/n9k4AGHP2SQmX772xFROgACEUUHAQH/kLI4gtUGPJIBDlYFn0sC5sUROUoAAhExBwEC/6/rDX+qJP+kAQGumwh+uWfWESVKAAIRHQc/Z2V0S2V5QAH/Z2V0VmFsdWUAAABAAf9zZXRWYWx1ZQAAAEABUAEB",  # storage/storage.capnp:Store.Container.Entry
    "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",  # storage/storage.capnp:Store.Container.Entry.Value
    "EBVQBgb/CtBCqf5/ZOAAESwBAAAEBwABMRXSAQAE/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLkVudHJ5LmdldEtleSRQYXJhbQFz",  # storage/storage.capnp:Store.Container.Entry.getKey$Params
    "ECVQBgb/hz9kkJl++9sAESwBAAAFAQcAATEV2gEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLkVudHJ5LmdldEtleSRSZXN1bAN0c1EEAwQAAAQBAAARDSIAAFEIAwFRFAIBB2tleQEMAAIBDAAB",  # storage/storage.capnp:Store.Container.Entry.getKey$Results
    "EBVQBgb/kLI4gtUGPJIAESwBAAAEBwABMRXiAQAE/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLkVudHJ5LmdldFZhbHVlJFBhcgdhbXM=",  # storage/storage.capnp:Store.Container.Entry.getValue$Params
    "EDRQBgb/DlYFn0sC5sUAUSwBAQAABQEHAAExFeoBAAERKXcAAf9zdG9yYWdlLwZzdG9yYWdlLmNhcG5wOlN0b3JlLkNvbnRhaW5lci5FbnRyeS5nZXRWYWx1ZSRSZXMPdWx0c1EIAwQAAAQBAAARKTIAAFEkAwFRMAIBAQEUAQEAABEtQgAAUSgDAVE0AgEfdmFsdWUBEP9cj5JJxFwY4gAAAQEQAAF/aXNVbnNldAEBAAIBAQAB",  # storage/storage.capnp:Store.Container.Entry.getValue$Results
    "ECVQBgb/r+sNf6ok/6QAESwBAAAFAQcAATEV4gEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLkVudHJ5LnNldFZhbHVlJFBhcgdhbXNRBAMEAAAEAQAAEQ0yAABRCAMBURQCAR92YWx1ZQEQ/1yPkknEXBjiAAABARAAAQ==",  # storage/storage.capnp:Store.Container.Entry.setValue$Params
    "ECVQBgb/Aa6bCH65Z9YAUSwBAQAABAcAATEV6gEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLkVudHJ5LnNldFZhbHVlJFJlcw91bHRzUQQDBAAABAEAABENQgAAUQgDAVEUAgF/c3VjY2VzcwEBAAIBAQAB",  # storage/storage.capnp:Store.Container.Entry.setValue$Results
    "EDRQBgb/MML/8qZZ5+8AESYB/2KuZ1X0MYGHAAUCBwAAM2YJtQkxFZIBES0HAAARKXcAAf9zdG9yYWdlLwVzdG9yYWdlLmNhcG5wOlN0b3JlLkNvbnRhaW5lci5LZXlBbmRFbnRyAXlQAQFRCAMEAAAEAQAAESkiAABRJAMBUTACAREBARQBAQAAES0yAABRKAMBUTQCAQdrZXkBDAACAQwAAR9lbnRyeQER/8B49Hs+JBr6AAABAREAAQ==",  # storage/storage.capnp:Store.Container.KeyAndEntry
    "EBRQBgb/XswivomIE54AESYBAAAEBwABMRWiAQAE/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmV4cG9ydCRQYXIHYW1z",  # storage/storage.capnp:Store.Container.export$Params
    "ECRQBgb/7slRc02EFKkAESYBAAAFAQcAATEVqgEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmV4cG9ydCRSZXMPdWx0c1EEAwQAAAQBAAARDSoAAFEIAwFRFAIBD2pzb24BDAACAQwAAQ==",  # storage/storage.capnp:Store.Container.export$Results
    "EBVQBgb/lAljjhcU/JMAESYBAAAEBwABMRXqAQAE/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmRvd25sb2FkRW50cmllcyRQYQ9yYW1z",  # storage/storage.capnp:Store.Container.downloadEntries$Params
    "EDtQBgb/ZtEBxJox5P8AESYBAAAFAQcAATEV8gEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmRvd25sb2FkRW50cmllcyRSZR9zdWx0c1EEAwQAAAQBAAARDUIAAFEIAwFRbAIBf2VudHJpZXMBDgABUAMBARD/M0cXJUeG1LkAAABAAREBH1EEAgH/M0cXJUeG1LkAAAARASdRCAEBAQFRCAMBAQFREAMBAQwAAgEQ/1yPkknEXBjiAAABAQ4AAQ==",  # storage/storage.capnp:Store.Container.downloadEntries$Results
    "EDZQBgb/M0cXJUeG1LkAERQB/8mKqHWnyfGZAAUCBxABM5MIwggRFcoRIQcAABEddwAAEZEX/2NvbW1vbi9jAm9tbW9uLmNhcG5wOlBhaXIAAFABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBB2ZzdAESAQH/M0cXJUeG1LkAAAABEgABB3NuZAESBQEB/zNHFyVHhtS5AAAAARIAAUEIAREFEhEFEgFGAVM=",  # common/common.capnp:Pair
    "EBVQBgb/sTNpjCgK99sAESYBAAAEBwABMRXKAQAE/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmxpc3RFbnRyaWVzJFBhcmFtcwAA",  # storage/storage.capnp:Store.Container.listEntries$Params
    "EClQBgb/cjgIA7rTKKAAESYBAAAFAQcAATEV0gEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmxpc3RFbnRyaWVzJFJlc3VsdAFzUQQDBAAABAEAABENQgAAUQgDAVEkAgF/ZW50cmllcwEOAAFQAwEBEP8wwv/yplnn7wAAAQEOAAE=",  # storage/storage.capnp:Store.Container.listEntries$Results
    "ECRQBgb/adY6tF0dFsQAESYBAAAFAQcAATEVsgEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmdldEVudHJ5JFAfYXJhbXNRBAMEAAAEAQAAEQ0iAABRCAMBURQCAQdrZXkBDAACAQwAAQ==",  # storage/storage.capnp:Store.Container.getEntry$Params
    "ECRQBgb/RrhwqWTXwZsAESYBAAAFAQcAATEVugEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmdldEVudHJ5JFI/ZXN1bHRzUQQDBAAABAEAABENMgAAUQgDAVEUAgEfZW50cnkBEf/AePR7PiQa+gAAAQERAAE=",  # storage/storage.capnp:Store.Container.getEntry$Results
    "ECVQBgb/zsV6snCR6f0AESYBAAAFAQcAATEVygEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLnJlbW92ZUVudHJ5JFBhcmFtcwAAUQQDBAAABAEAABENIgAAUQgDAVEUAgEHa2V5AQwAAgEMAAE=",  # storage/storage.capnp:Store.Container.removeEntry$Params
    "ECVQBgb/v7dkX8k42fsAUSYBAQAABAcAATEV0gEAAREpPwAB/3N0b3JhZ2UvBnN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLnJlbW92ZUVudHJ5JFJlc3VsdAFzUQQDBAAABAEAABENQgAAUQgDAVEUAgF/c3VjY2VzcwEBAAIBAQAB",  # storage/storage.capnp:Store.Container.removeEntry$Results
    "EBRQBgb/e4J71vhxHMMAESYBAAAEBwABMRWaAQAE/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmNsZWFyJFBhcmEDbXM=",  # storage/storage.capnp:Store.Container.clear$Params
    "ECRQBgb/rf+bwt8nb+sAUSYBAQAABAcAATEVogEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuQ29udGFpbmVyLmNsZWFyJFJlc3UHbHRzUQQDBAAABAEAABENQgAAUQgDAVEUAgF/c3VjY2VzcwEBAAIBAQAB",  # storage/storage.capnp:Store.Container.clear$Results
    "EENQBgbfEoOc7f3v+1EmAQEAAAUCBwABMRWyAQABESWvAAH/c3RvcmFnZS8Fc3RvcmFnZS5jYXBucDpTdG9yZS5Db250YWluZXIuYWRkRW50cnkkUB9hcmFtc1EMAwQAAAQBAAARRSIAAFFAAwFRTAIBEQEBFAEBAAARSTIAAFFEAwFRUAIBAQIUAQIBARFNggAAUUwDAVFYAgEHa2V5AQwAAgEMAAEfdmFsdWUBEP9cj5JJxFwY4gAAAQEQAAH/cmVwbGFjZUUBeGlzdGluZwABAQACAQEAAQ==",  # storage/storage.capnp:Store.Container.addEntry$Params
    "EDNQBgb/VJ66f3NXO4gAUSYBAQAABQEHAAExFboBAAERJXcAAf9zdG9yYWdlLwVzdG9yYWdlLmNhcG5wOlN0b3JlLkNvbnRhaW5lci5hZGRFbnRyeSRSP2VzdWx0c1EIAwQAAAQBAAARKTIAAFEkAwFRMAIBAQEUAQEAABEtQgAAUSgDAVE0AgEfZW50cnkBEf/AePR7PiQa+gAAAQERAAF/c3VjY2VzcwEBAAIBAQAB",  # storage/storage.capnp:Store.Container.addEntry$Results
    "EENQBgb+wj7wfiLs6hEcAf8GbziiipWf5gAFAwcAADM6DaQNMRVqAREpBwAAESWvAAH/c3RvcmFnZS8Ec3RvcmFnZS5jYXBucDpTdG9yZS5JbmZvQW5kQ29udGEPaW5lclABAVEMAwQAAAQBAAARRRoAAFFAAwFRTAIBEQEBFAEBAAARSSoAAFFEAwFRUAIBEQICFAECAAARTVIAAFFMAwFRWAIBA2lkAQwAAgEMAAEPbmFtZQEMAAIBDAAB/2NvbnRhaW5lAAFyARH/Yq5nVfQxgYcAAAEBEQAB",  # storage/storage.capnp:Store.InfoAndContainer
    "EF1QBgb/QvHS7ywmfYQAERwB/wZvOKKKlZ/mAAUDBwAAM80ORxAxFWoBESkHAAARJa8AAf9zdG9yYWdlLwRzdG9yYWdlLmNhcG5wOlN0b3JlLkltcG9ydEV4cG9ydA9EYXRhUAEBUQwDBAAABAEAABFFKgAAUUADAVFMAgERAQEUAQEAABFJQgAAUUQDAVGoAgERAgIUAQIAABGlWgAAUaQDAVHAAgEPaW5mbwEQ/9PaA/7LfsvUAAABARAAAX9lbnRyaWVzAQ4AAVADAQEQ/zNHFyVHhtS5AAAAQAERAR9RBAIB/zNHFyVHhtS5AAAAEQEnUQgBAQEBUQgDAQEBURADAQEMAAIBEP9cj5JJxFwY4gAAAQEOAAH/aXNBbnlWYWwAA3VlAQ4AAVADAQEBAAIBDgAB",  # storage/storage.capnp:Store.ImportExportData
    "EEJQBgb/09oD/st+y9QAERQB/8mKqHWnyfGZAAUDBwAAMzwBnwExFRIBESUHAAARIa8AAf9jb21tb24vYwNvbW1vbi5jYXBucDpJZEluZm9ybWF0aW8BblABAVEMAwQAAAQBAAARRRoAAFFAAwFRTAIBEQEBFAEBAAARSSoAAFFEAwFRUAIBEQICFAECAAARTWIAAFFMAwFRWAIBA2lkAQwAAgEMAAEPbmFtZQEMAAIBDAAB/2Rlc2NyaXB0AAdpb24BDAACAQwAAQ==",  # common/common.capnp:IdInformation
    "EDNQBgb/9psrZ024TLwAERwBAAAFAgcAATEVggEAAREhdwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUubmV3Q29udGFpbmVyJFBhcmFtcwBRCAMEAAAEAQAAESkqAABRJAMBUTACAREBARQBAQAAES1iAABRLAMBUTgCAQ9uYW1lAQwAAgEMAAH/ZGVzY3JpcHQAB2lvbgEMAAIBDAAB",  # storage/storage.capnp:Store.newContainer$Params
    "ECVQBgb/rJeZOr9JI/MAERwBAAAFAQcAATEVigEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUubmV3Q29udGFpbmVyJFJlc3VsdHMAAFEEAwQAAAQBAAARDVIAAFEMAwFRGAIB/2NvbnRhaW5lAAFyARH/Yq5nVfQxgYcAAAEBEQAB",  # storage/storage.capnp:Store.newContainer$Results
    "ECRQBgb/RCeNn8e+F/UAERwBAAAFAQcAATEVmgEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuY29udGFpbmVyV2l0aElkJFBhcmEDbXNRBAMEAAAEAQAAEQ0aAABRCAMBURQCAQNpZAEMAAIBDAAB",  # storage/storage.capnp:Store.containerWithId$Params
    "ECVQBgb/5UVU2q4mr7IAERwBAAAFAQcAATEVogEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuY29udGFpbmVyV2l0aElkJFJlc3UHbHRzUQQDBAAABAEAABENUgAAUQwDAVEYAgH/Y29udGFpbmUAAXIBEf9irmdV9DGBhwAAAQERAAE=",  # storage/storage.capnp:Store.containerWithId$Results
    "EBRQBgb/bs78ZiHpZqQAERwBAAAEBwABMRWSAQAE/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUubGlzdENvbnRhaW5lcnMkUGFyYW0Bcw==",  # storage/storage.capnp:Store.listContainers$Params
    "EClQBgb/+VaiXWgmJPgAERwBAAAFAQcAATEVmgEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUubGlzdENvbnRhaW5lcnMkUmVzdWwDdHNRBAMEAAAEAQAAEQ1aAABRDAMBUSgCAf9jb250YWluZQADcnMBDgABUAMBARD+wj7wfiLs6gABAQ4AAQ==",  # storage/storage.capnp:Store.listContainers$Results
    "ECRQBgb/UiS2f55Pvr8AERwBAAAFAQcAATEVmgEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUucmVtb3ZlQ29udGFpbmVyJFBhcmEDbXNRBAMEAAAEAQAAEQ0aAABRCAMBURQCAQNpZAEMAAIBDAAB",  # storage/storage.capnp:Store.removeContainer$Params
    "ECRQBgb9DoUmOGAEqlEcAQEAAAQHAAExFaIBAAERJT8AAf9zdG9yYWdlLwVzdG9yYWdlLmNhcG5wOlN0b3JlLnJlbW92ZUNvbnRhaW5lciRSZXN1B2x0c1EEAwQAAAQBAAARDUIAAFEIAwFRFAIBf3N1Y2Nlc3MBAQACAQEAAQ==",  # storage/storage.capnp:Store.removeContainer$Results
    "ECRQBgb/MqsXAsReProAERwBAAAFAQcAATEVmgEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuaW1wb3J0Q29udGFpbmVyJFBhcmEDbXNRBAMEAAAEAQAAEQ0qAABRCAMBURQCAQ9qc29uAQwAAgEMAAE=",  # storage/storage.capnp:Store.importContainer$Params
    "ECVQBgb/z4msdSYaj4kAERwBAAAFAQcAATEVogEAARElPwAB/3N0b3JhZ2UvBXN0b3JhZ2UuY2FwbnA6U3RvcmUuaW1wb3J0Q29udGFpbmVyJFJlc3UHbHRzUQQDBAAABAEAABENUgAAUQwDAVEYAgH/Y29udGFpbmUAAXIBEf9irmdV9DGBhwAAAQERAAE=",  # storage/storage.capnp:Store.importContainer$Results
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
Store = _InterfaceModule(_loader.get(0xE69F958AA2386F06).as_interface(), "Store")
Store.Container = _InterfaceModule(
    _loader.get(0x878131F45567AE62).as_interface(),
    "Container",
)
Store.Container.Entry = _InterfaceModule(
    _loader.get(0xFA1A243E7BF478C0).as_interface(),
    "Entry",
)
Store.Container.Entry.Value = _StructModule(
    _loader.get(0xE2185CC449928F5C).as_struct(),
    "Value",
)
Store.Container.KeyAndEntry = _StructModule(
    _loader.get(0xEFE759A6F2FFC230).as_struct(),
    "KeyAndEntry",
)
Store.InfoAndContainer = _StructModule(
    _loader.get(0xEAEC227EF03EC200).as_struct(),
    "InfoAndContainer",
)
Store.ImportExportData = _StructModule(
    _loader.get(0x847D262CEFD2F142).as_struct(),
    "ImportExportData",
)

Store.Server.ContainerwithidResultTuple = NamedTuple(
    "ContainerwithidResultTuple",
    [("container", object)],
)
Store.Server.ImportcontainerResultTuple = NamedTuple(
    "ImportcontainerResultTuple",
    [("container", object)],
)
Store.Server.ListcontainersResultTuple = NamedTuple(
    "ListcontainersResultTuple",
    [("containers", object)],
)
Store.Server.NewcontainerResultTuple = NamedTuple(
    "NewcontainerResultTuple",
    [("container", object)],
)
Store.Server.RemovecontainerResultTuple = NamedTuple(
    "RemovecontainerResultTuple",
    [("success", object)],
)
Store.Container.Server.AddentryResultTuple = NamedTuple(
    "AddentryResultTuple",
    [("entry", object), ("success", object)],
)
Store.Container.Server.ClearResultTuple = NamedTuple(
    "ClearResultTuple",
    [("success", object)],
)
Store.Container.Server.DownloadentriesResultTuple = NamedTuple(
    "DownloadentriesResultTuple",
    [("entries", object)],
)
Store.Container.Server.ExportResultTuple = NamedTuple(
    "ExportResultTuple",
    [("json", object)],
)
Store.Container.Server.GetentryResultTuple = NamedTuple(
    "GetentryResultTuple",
    [("entry", object)],
)
Store.Container.Server.ListentriesResultTuple = NamedTuple(
    "ListentriesResultTuple",
    [("entries", object)],
)
Store.Container.Server.RemoveentryResultTuple = NamedTuple(
    "RemoveentryResultTuple",
    [("success", object)],
)
Store.Container.Entry.Server.GetkeyResultTuple = NamedTuple(
    "GetkeyResultTuple",
    [("key", object)],
)
Store.Container.Entry.Server.GetvalueResultTuple = NamedTuple(
    "GetvalueResultTuple",
    [("value", object), ("isUnset", object)],
)
Store.Container.Entry.Server.SetvalueResultTuple = NamedTuple(
    "SetvalueResultTuple",
    [("success", object)],
)
