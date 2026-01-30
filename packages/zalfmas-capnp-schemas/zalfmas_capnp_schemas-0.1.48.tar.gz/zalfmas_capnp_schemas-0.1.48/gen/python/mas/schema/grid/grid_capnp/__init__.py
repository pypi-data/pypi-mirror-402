"""This is an automatically generated stub for `grid.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EEFQBgb/I6pglHPpc9MAAQoAAxEVghEZJxE1ZwAC/2dyaWQvZ3JpAWQuY2FwbnAAUQgBAf8Bs6Znd9zspQARCWL/xuNhlrJzKeQAEQkq/0FnZ3JlZ2F0AAdpb24PR3JpZFEQAQL/LF+Av575xrkAUSgCAUE8Af9s+bDj/qNejABROAIBQUgB/+AreSMQf6m+AFFEAgFBUAH/tUQOJgG2MOEAUUwCAUFwAQEMAAARAZL/bWFzOjpzY2gBZW1hOjpncmkBZAAAAQwAABEBgv9tYXMuc2NoZQFtYS5ncmlkAAAAAQwAABEBKg9ncmlkAAABDAAAMQGyAf9naXRodWIuYwVvbS96YWxmLXJwbS9tYXNfY2FwbnByb3RvX3NjaGVtYXMvZ2VuL2dvHy9ncmlkAAA=",  # grid/grid.capnp
    "EFNQBgb/AbOmZ3fc7KUAERAC/yOqYJRz6XPTAAABM88BfgURFeIRIQcAADEdhwEAAf9ncmlkL2dyaQJkLmNhcG5wOkFnZ3JlZ2F0B2lvblABAVFAAQIAABG5KgAAAQIRsSoAAAEFEalCAAABBxGhIgAAAQoRmSIAAAENEZEiAAABAxGJKgAAAQYRgUIAAAEBEXkiAAABBBFxOgAAAQ4RaSoAAAEPEWEqAAABCBFZKgAAAQkRUSoAAAELEUkqAAABDBFBKgAAD25vbmUPd0F2Z393TWVkaWFuB21pbgdtYXgHc3VtD2lBdmd/aU1lZGlhbgdhdmc/bWVkaWFuD3dTdW0PaVN1bQ93TWluD2lNaW4Pd01heA9pTWF4",  # grid/grid.capnp:Aggregation
    "EINQBgb/xuNhlrJzKeQAERAD/yOqYJRz6XPTAAABM4AFYhERFaoRHWcAADFxBwITyQEnAAD/Z3JpZC9ncmkBZC5jYXBucDoPR3JpZFEYAQH/0Nlz5foNLv4AESky/3tX5yfd+7apABElWv//BmIIXdjiuQARJTr/HToz7xdGRKwAESGC/2SN8Z4bz1y1ABEhSv/TVcuAglE51gARIUofVmFsdWX/UmVzb2x1dGkAA29uP1Jvd0NvbP9BZ2dyZWdhdAJpb25QYXJ0AExvY2F0aW9uAAD/Q2FsbGJhY2sAAABRIAMFAAD/mgcMYRxvfusBsEA1g2MCvagR8XoAAhHpBwEC/+stHn653J73AZrHeAdJuteMEd1aAAIR1QcBA7++jcAM8lqm/28lEBZrb6TnABHJUgACEcEHAQT/tlTaKm+nBPgBzx8bKr0ywZsRtWIAAhGtBwEB/y+X5ta98o+UAZRZcfw+8x6iEaFCAAIRlQcBBf+XvWYkmThz8wF3M0TTV85/5RGJagACEYEHAQb/utvP/bPRrdkB0uuneCvVjZsRdWIAAhFtBwEH/0hnartoQ067AfvEn71t53DREWEqAAIRVQf/Y2xvc2VzdFYAP2FsdWVBdEAB/3Jlc29sdXRpAANvbkAB/2RpbWVuc2lvAAFuQAH/bm9EYXRhVmEAB2x1ZUABf3ZhbHVlQXRAAf9sYXRMb25CbwAPdW5kc0AB/3N0cmVhbUNlAAdsbHNAAQ91bml0QAFRCAEB/9VInFnL0a+yAAAA/2XLNtyg2qfBAAAA",  # grid/grid.capnp:Grid
    "EE9QBgb/0Nlz5foNLv4AURUBAv/G42GWsnMp5ABEBwQBBDPdBV0GERXaESEHAAARHecAAf9ncmlkL2dyaQJkLmNhcG5wOkdyaWQuVmFsA3VlUAEBURADBAz//wQBAAARYRIAAFFcAwFRaAIBDQH+/xQBAQAAEWUSAABRYAMBUWwCAQ0C/f8UAQIAABFpGgAAUWQDAVFwAgENA/z/FAEDAAARbRoAAFFoAwFRdAIBAWYBCwACAQsAAQFpAQUAAgEFAAEDdWkBCQACAQkAAQNubwEBAAIBAQAB",  # grid/grid.capnp:Grid.Value
    "EDFQBgb/e1fnJ937tqkAURUBAv/G42GWsnMp5ABEBwIBBDNgBroGMRUCAREhBwAAER13AAH/Z3JpZC9ncmkDZC5jYXBucDpHcmlkLlJlc29sdXRpb24AUAEBUQgDBAz//wQBAAARKTIAAFEkAwFRMAIBDQH+/xQBAQAAES06AABRKAMBUTQCAR9tZXRlcgEFAAIBBQABP2RlZ3JlZQELAAIBCwAB",  # grid/grid.capnp:Grid.Resolution
    "EDFQBgb//wZiCF3Y4rkAURUBAv/G42GWsnMp5AAEBwAAM74G+QYRFeIRIQcAABEddwAB/2dyaWQvZ3JpAmQuY2FwbnA6R3JpZC5Sb3cHQ29sUAEBUQgDBAAABAEAABEpIgAAUSQDAVEwAgERAQEUAQEAABEtIgAAUSgDAVE0AgEHcm93AQkAAgEJAAEHY29sAQkAAgEJAAE=",  # grid/grid.capnp:Grid.RowCol
    "EFFQBgb/HToz7xdGRKwAURUBAv/G42GWsnMp5AAFAgcAADP9Br0HMRUqARElBwAAESHnAAH/Z3JpZC9ncmkDZC5jYXBucDpHcmlkLkFnZ3JlZ2F0aW9uD1BhcnRQAQFREAMEAAAEAQAAEWEyAABRXAMBUWgCAREBARQBAQAAEWU6AABRYAMBUWwCAQECFAECAAARaUoAAFFoAwFRdAIBEQMBFAEDAAARcToAAFFsAwFReAIBH3ZhbHVlARD/0Nlz5foNLv4AAAEBEAABP3Jvd0NvbAEQ//8GYghd2OK5AAABARAAAf9hcmVhRnJhYwAAAAELAAIBCwABP2lWYWx1ZQELAAIBCwAB",  # grid/grid.capnp:Grid.AggregationPart
    "EEFQBgb/ZI3xnhvPXLUAERUB/8bjYZaycynkAAUDBwAAM8EHMggRFfIRIQcAABEdrwAB/2dyaWQvZ3JpAmQuY2FwbnA6R3JpZC5Mb2MfYXRpb25QAQFRDAMEAAAEAQAAEUViAABRRAMBUVACAREBARQBAQAAEU06AABRSAMBUVQCARECAhQBAgAAEVEyAABRTAMBUVgCAf9sYXRMb25DbwAHb3JkARD/+4/MOTD88ewAAAEBEAABP3Jvd0NvbAEQ//8GYghd2OK5AAABARAAAR92YWx1ZQEQ/9DZc+X6DS7+AAABARAAAQ==",  # grid/grid.capnp:Grid.Location
    "EDFQBgb/+4/MOTD88ewAUQ4BAv8k/Md5IFSQkAAEBwAAMxADfwMRFdIRIQcAABEddwAB/2dlby9nZW8uAmNhcG5wOkxhdExvbkNvb3IBZFABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBB2xhdAELAAIBCwABB2xvbgELAAIBCwAB",  # geo/geo.capnp:LatLonCoord
    "EB9QBgb/01XLgIJROdYAERUD/8bjYZaycynkAAABM7cPZxARFfIRIQcAABEdRxFJBwAA/2dyaWQvZ3JpAmQuY2FwbnA6R3JpZC5DYWwfbGJhY2tQAQFRBAMFAAD/u/Zoj3HHsOkBeSWLWW5vU44REVIAAhEJB/9zZW5kQ2VsbAABc0ABUAEB",  # grid/grid.capnp:Grid.Callback
    "ECRQBgb/u/Zoj3HHsOkAUR4BAQAABAcAATEVegEAAREhPwAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5DYWxsYmFjay5zZW5kQ2VsbHMkP1BhcmFtc1EEAwQAAAQBAAARDUoAAFEMAwFRGAIB/21heENvdW50AAAAAQUAAgEFAAE=",  # grid/grid.capnp:Grid.Callback.sendCells$Params
    "EChQBgb/eSWLWW5vU44AER4BAAAFAQcAATEVggEAAREhPwAB/2dyaWQvZ3JpBWQuY2FwbnA6R3JpZC5DYWxsYmFjay5zZW5kQ2VsbHMkUmVzdWx0cwBRBAMEAAAEAQAAEQ1SAABRDAMBUSgCAf9sb2NhdGlvbgABcwEOAAFQAwEBEP9kjfGeG89ctQAAAQEOAAE=",  # grid/grid.capnp:Grid.Callback.sendCells$Results
    "EHNQBgb/mgcMYRxvfusAURUBAQAABQIHAAExFVoBAAExIVcBAAH/Z3JpZC9ncmkEZC5jYXBucDpHcmlkLmNsb3Nlc3RWYWx1ZUF0JFBhcmEDbXNRGAMEAAAEAQAAEZliAABRmAMBUaQCAQEBFAEBAQERoWoAAFGgAwFRrAIBEQIBFAECAAARqVoAAFGoAwFRtAIBEQMBFAEDAQERsSIAAFGsAwFRuAIBEQQBFAEEAQERtXIAAFG0AwFRwAIBEQUCFAEFAQERvYIAAFG8AwFRyAIB/2xhdGxvbkNvAAdvcmQBEP/7j8w5MPzx7AAAAQEQAAH/aWdub3JlTm8AD0RhdGEBAQACBQEBAAH/cmVzb2x1dGkAA29uARD/e1fnJ937tqkAAAEBEAABB2FnZwEP/wGzpmd33OylAAABAQ8AAf9yZXR1cm5SbwAfd0NvbHMBAQACAQEAAf9pbmNsdWRlQQFnZ1BhcnRzAAEBAAIBAQAB",  # grid/grid.capnp:Grid.closestValueAt$Params
    "EFVQBgb/sEA1g2MCvagAERUBAAAFBAcAATEVYgEAAREh5wAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5jbG9zZXN0VmFsdWVBdCRSZXN1B2x0c1EQAwQAAAQBAAARYSIAAFFcAwFRaAIBEQEBFAEBAAARZRoAAFFgAwFRbAIBEQICFAECAAARaRoAAFFkAwFRcAIBEQMDFAEDAAARbUoAAFFsAwFRiAIBB3ZhbAEQ/9DZc+X6DS7+AAABARAAAQN0bAEQ//8GYghd2OK5AAABARAAAQNicgEQ//8GYghd2OK5AAABARAAAf9hZ2dQYXJ0cwAAAAEOAAFQAwEBEP8dOjPvF0ZErAAAAQEOAAE=",  # grid/grid.capnp:Grid.closestValueAt$Results
    "EBJQBgb/6y0efrncnvcAERUBAAAEBwABMRU6AQAE/2dyaWQvZ3JpA2QuY2FwbnA6R3JpZC5yZXNvbHV0aW9uJD9QYXJhbXM=",  # grid/grid.capnp:Grid.resolution$Params
    "ECJQBgb/msd4B0m614wAERUBAAAFAQcAATEVQgEAAREdPwAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5yZXNvbHV0aW9uJFJlc3VsdHMAUQQDBAAABAEAABENIgAAUQgDAVEUAgEHcmVzARD/e1fnJ937tqkAAAEBEAAB",  # grid/grid.capnp:Grid.resolution$Results
    "EBJQBga/vo3ADPJaphEVAQAABAcAATEVMgEABP9ncmlkL2dyaQNkLmNhcG5wOkdyaWQuZGltZW5zaW9uJFAfYXJhbXM=",  # grid/grid.capnp:Grid.dimension$Params
    "EDFQBgb/byUQFmtvpOcAURUBAgAABAcAATEVOgEAAREddwAB/2dyaWQvZ3JpA2QuY2FwbnA6R3JpZC5kaW1lbnNpb24kUj9lc3VsdHNRCAMEAAAEAQAAESkqAABRJAMBUTACAREBARQBAQAAES0qAABRKAMBUTQCAQ9yb3dzAQkAAgEJAAEPY29scwEJAAIBCQAB",  # grid/grid.capnp:Grid.dimension$Results
    "EBJQBgb/tlTaKm+nBPgAERUBAAAEBwABMRVCAQAE/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5ub0RhdGFWYWx1ZSRQYXJhbXMA",  # grid/grid.capnp:Grid.noDataValue$Params
    "ECNQBgb/zx8bKr0ywZsAERUBAAAFAQcAATEVSgEAAREhPwAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5ub0RhdGFWYWx1ZSRSZXN1bHRzAABRBAMEAAAEAQAAEQ06AABRCAMBURQCAT9ub2RhdGEBEP/Q2XPl+g0u/gAAAQEQAAE=",  # grid/grid.capnp:Grid.noDataValue$Results
    "EGBQBgb/L5fm1r3yj5QAURUBAwAABQEHAAExFSIBAAExHR8BAAH/Z3JpZC9ncmkDZC5jYXBucDpHcmlkLnZhbHVlQXQkUGFyB2Ftc1EUAwQAAAQBAAARfSIAAFF4AwFRhAIBEQEBFAEBAAARgSIAAFF8AwFRiAIBAQIUAQIAABGFWgAAUYQDAVGQAgERAwgUAQMBARGNIgAAUYgDAVGUAgERBJAUAQQBARGRggAAUZADAVGcAgEHcm93AQkAAgEJAAEHY29sAQkAAgEJAAH/cmVzb2x1dGkAA29uARD/e1fnJ937tqkAAAEBEAABB2FnZwEP/wGzpmd33OylAAABAQ8AAf9pbmNsdWRlQQFnZ1BhcnRzAAEBAAIBAQAB",  # grid/grid.capnp:Grid.valueAt$Params
    "EDZQBgb/lFlx/D7zHqIAERUBAAAFAgcAATEVKgEAAREddwAB/2dyaWQvZ3JpA2QuY2FwbnA6R3JpZC52YWx1ZUF0JFJlcw91bHRzUQgDBAAABAEAABEpIgAAUSQDAVEwAgERAQEUAQEAABEtSgAAUSwDAVFIAgEHdmFsARD/0Nlz5foNLv4AAAEBEAAB/2FnZ1BhcnRzAAAAAQ4AAVADAQEQ/x06M+8XRkSsAAABAQ4AAQ==",  # grid/grid.capnp:Grid.valueAt$Results
    "ECRQBgb/l71mJJk4c/MAURUBAQAABAcAATEVSgEAAREhPwAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5sYXRMb25Cb3VuZHMkUGFyYW1zAABRBAMEAAAEAQEBEQ1yAABRDAMBURgCAf91c2VDZWxsQwAfZW50ZXIBAQACAQEAAQ==",  # grid/grid.capnp:Grid.latLonBounds$Params
    "EFBQBgb/dzNE01fOf+UAERUBAAAFBAcAATEVUgEAAREh5wAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5sYXRMb25Cb3VuZHMkUmVzdWx0AXNREAMEAAAEAQAAEWEaAABRXAMBUWgCAREBARQBAQAAEWUaAABRYAMBUWwCARECAhQBAgAAEWkaAABRZAMBUXACAREDAxQBAwAAEW0aAABRaAMBUXQCAQN0bAEQ//uPzDkw/PHsAAABARAAAQN0cgEQ//uPzDkw/PHsAAABARAAAQNicgEQ//uPzDkw/PHsAAABARAAAQNibAEQ//uPzDkw/PHsAAABARAAAQ==",  # grid/grid.capnp:Grid.latLonBounds$Results
    "EDJQBgb/utvP/bPRrdkAERUBAAAFAgcAATEVQgEAAREddwAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5zdHJlYW1DZWxscyRQYXJhbXMAUQgDBAAABAEAABEpQgAAUSQDAVEwAgERAQEUAQEAABEtYgAAUSwDAVE4AgF/dG9wTGVmdAEQ//8GYghd2OK5AAABARAAAf9ib3R0b21SaQAHZ2h0ARD//wZiCF3Y4rkAAAEBEAAB",  # grid/grid.capnp:Grid.streamCells$Params
    "ECRQBgb/0uuneCvVjZsAERUBAAAFAQcAATEVSgEAAREhPwAB/2dyaWQvZ3JpBGQuY2FwbnA6R3JpZC5zdHJlYW1DZWxscyRSZXN1bHRzAABRBAMEAAAEAQAAEQ1KAABRDAMBURgCAf9jYWxsYmFjawAAAAER/9NVy4CCUTnWAAABAREAAQ==",  # grid/grid.capnp:Grid.streamCells$Results
    "EBJQBgb/SGdqu2hDTrsAERUBAAAEBwABMRUKAQAE/2dyaWQvZ3JpA2QuY2FwbnA6R3JpZC51bml0JFBhcmFtcwAA",  # grid/grid.capnp:Grid.unit$Params
    "ECJQBgb/+8SfvW3ncNEAERUBAAAFAQcAATEVEgEAAREdPwAB/2dyaWQvZ3JpA2QuY2FwbnA6R3JpZC51bml0JFJlc3VsdAFzUQQDBAAABAEAABENKgAAUQgDAVEUAgEPdW5pdAEMAAIBDAAB",  # grid/grid.capnp:Grid.unit$Results
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
Aggregation = _EnumModule(_loader.get(0xA5ECDC7767A6B301).as_enum(), "Aggregation")
Grid = _InterfaceModule(_loader.get(0xE42973B29661E3C6).as_interface(), "Grid")
Grid.Value = _StructModule(_loader.get(0xFE2E0DFAE573D9D0).as_struct(), "Value")
Grid.Resolution = _StructModule(
    _loader.get(0xA9B6FBDD27E7577B).as_struct(),
    "Resolution",
)
Grid.RowCol = _StructModule(_loader.get(0xB9E2D85D086206FF).as_struct(), "RowCol")
Grid.AggregationPart = _StructModule(
    _loader.get(0xAC444617EF333A1D).as_struct(),
    "AggregationPart",
)
Grid.Location = _StructModule(_loader.get(0xB55CCF1B9EF18D64).as_struct(), "Location")
Grid.Callback = _InterfaceModule(
    _loader.get(0xD639518280CB55D3).as_interface(),
    "Callback",
)

Grid.Server.ClosestvalueatResultTuple = NamedTuple(
    "ClosestvalueatResultTuple",
    [("val", object), ("tl", object), ("br", object), ("aggParts", object)],
)
Grid.Server.DimensionResultTuple = NamedTuple(
    "DimensionResultTuple",
    [("rows", object), ("cols", object)],
)
Grid.Server.LatlonboundsResultTuple = NamedTuple(
    "LatlonboundsResultTuple",
    [("tl", object), ("tr", object), ("br", object), ("bl", object)],
)
Grid.Server.NodatavalueResultTuple = NamedTuple(
    "NodatavalueResultTuple",
    [("nodata", object)],
)
Grid.Server.ResolutionResultTuple = NamedTuple(
    "ResolutionResultTuple",
    [("res", object)],
)
Grid.Server.StreamcellsResultTuple = NamedTuple(
    "StreamcellsResultTuple",
    [("callback", object)],
)
Grid.Server.UnitResultTuple = NamedTuple("UnitResultTuple", [("unit", object)])
Grid.Server.ValueatResultTuple = NamedTuple(
    "ValueatResultTuple",
    [("val", object), ("aggParts", object)],
)
Grid.Callback.Server.SendcellsResultTuple = NamedTuple(
    "SendcellsResultTuple",
    [("locations", object)],
)
