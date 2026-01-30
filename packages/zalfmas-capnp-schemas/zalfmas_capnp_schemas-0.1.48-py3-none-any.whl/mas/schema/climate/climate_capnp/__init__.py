"""This is an automatically generated stub for `climate.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EHpQBgb/GEXrEOQ6HaAAARAAAxEVsjEdBwETEQFnAAL/Y2xpbWF0ZS8BY2xpbWF0ZS4fY2FwbnBRQAEB/xCf3u5paDnOABF5Iv9R44Mwxd5xhgARdSL/7no0FuQKeNMAEXEi/8yUDDF4B/OOABFtIv80pF3N0azKyAARaXr/sG1VZunSNvsAEWlK//BgWfDR/TX2ABFpQv+g5SJf7H+m1wARZWr/ZLVa27RgV+MAEWVC/xn+E/OFc7qFABFhSv/obW7+QJ92pwARYVr/T5bGm/XMwfEAEWF6/18MKzXUCH3+ABFhQv/ZKZnFbMIYpAARXar/soSXl++A9OEAEWG6/0QnpaLwLfHFABFl8gdHQ00HUkNNB1NTUAdSQ1D/RW5zZW1ibGUAP01lbWJlcv9NZXRhZGF0YQAAAH9EYXRhc2V0/01ldGFQbHVzAA9EYXRhf0VsZW1lbnT/TG9jYXRpb24AAAD/VGltZVNlcmkAA2Vz/1RpbWVTZXJpAD9lc0RhdGF/U2VydmljZf9DU1ZUaW1lUwFlcmllc0ZhYw90b3J5/0FsdGVyVGltAWVTZXJpZXNXP3JhcHBlcv9BbHRlclRpbQJlU2VyaWVzV3JhcHBlckZhH2N0b3J5URABAv8sX4C/nvnGuQBRKAIBQTwB/2z5sOP+o16MAFE4AgFBTAH/4Ct5IxB/qb4AUUgCAUFUAf+1RA4mAbYw4QBRUAIBQXgBAQwAABEBqv9tYXM6OnNjaAFlbWE6OmNsaQ9tYXRlAAABDAAAEQGa/21hcy5zY2hlAW1hLmNsaW1hA3RlAAABDAAAEQFCf2NsaW1hdGUAAAEMAAAxAcoB/2dpdGh1Yi5jBm9tL3phbGYtcnBtL21hc19jYXBucHJvdG9fc2NoZW1hcy9nZW4vZ28vY2xpbWF0ZQAB",  # climate/climate.capnp
    "EE9QBgb/EJ/e7mloOc4AERYC/xhF6xDkOh2gAAABM3gCmAQRFdIRIQcAADEdJwEAAf9jbGltYXRlLwJjbGltYXRlLmNhcG5wOkdDAU1QAQFRMAECAAARiWoAAAEBEYVqAAABAhGBegAAAQMRfWIAAAEEEXlqAAABBRF1SgAAAQYRcVoAAAEHEW1aAAABCBFpSgAAAQkRZVIAAAEKEWFSAAABCxFdcgAA/2NjY21hQ2FuAA9Fc20y/2ljaGVjRWNFAA9hcnRo/2lwc2xJcHNsAD9DbTVBTXL/bWlyb2NNaXIAB29jNf9tcGlNTXBpRQAPc21Mcv9nZmRsRXNtNAAAAP9pcHNsQ202YQADTHL/bXBpRXNtMTIAA0hy/21yaUVzbTIwAAAA/3VrZXNtMTBMAAFs/2dzd3AzVzVFAAE1/21vaGNIYWRHAB9lbTJFcw==",  # climate/climate.capnp:GCM
    "EDdQBgb/UeODMMXecYYAERYC/xhF6xDkOh2gAAABM5oE6wURFdIRIQcAABEdrwAB/2NsaW1hdGUvAmNsaW1hdGUuY2FwbnA6UkMBTVABAVEcAQIAABFNegAAAQERSXoAAAECEUVqAAABAxFBSgAAAQQRPZIAAAEFET16AAABBhE5YgAA/2NsbWNvbUNjAD9sbTQ4MTf/Z2VyaWNzUmUAP21vMjAxNf9rbm1pUmFjbQAPbzIyRf9zbWhpUmNhNAAAAP9jbG1jb21CdAF1Q2NsbTQ4MQE3/21waUNzY1JlAD9tbzIwMDn/dWhvaFdyZjMABzYxSA==",  # climate/climate.capnp:RCM
    "ECdQBgb/7no0FuQKeNMAERYC/xhF6xDkOh2gAAABM+0FSAcRFdIRIQcAABEdfwAB/2NsaW1hdGUvAmNsaW1hdGUuY2FwbnA6U1MBUFABAVEUAQIAABE1KgAAAQERLSoAAAECESUqAAABAxEdKgAAAQQRFSoAAA9zc3AxD3NzcDIPc3NwMw9zc3A0D3NzcDU=",  # climate/climate.capnp:SSP
    "EC9QBgb/zJQMMXgH844AERYC/xhF6xDkOh2gAAABM0oHLQoRFdIRIQcAABEdrwAB/2NsaW1hdGUvAmNsaW1hdGUuY2FwbnA6UkMBUFABAVEcAQIAABFNMgAAAQERRTIAAAECET0yAAABAxE1MgAAAQQRLTIAAAEFESUyAAABBhEdMgAAH3JjcDE5H3JjcDI2H3JjcDM0H3JjcDQ1H3JjcDYwH3JjcDcwH3JjcDg1",  # climate/climate.capnp:RCP
    "EFBQBgb/NKRdzdGsysgAURYBAf8YResQ5DodoAAEBwAAMy8KAQsxFSoBESUHAAARIecAAf9jbGltYXRlLwNjbGltYXRlLmNhcG5wOkVuc2VtYmxlTWUPbWJlclABAVEQAwQAAAQBAAARYRIAAFFcAwFRaAIBEQEBFAEBAAARZRIAAFFgAwFRbAIBEQICFAECAAARaRIAAFFkAwFRcAIBEQMDFAEDAAARbRIAAFFoAwFRdAIBAXIBBwACAQcAAQFpAQcAAgEHAAEBcAEHAAIBBwABAWYBBwACAQcAAQ==",  # climate/climate.capnp:EnsembleMember
    "EENQBgb/sG1VZunSNvsAERYB/xhF6xDkOh2gAAUCBwAAMwMLqhARFfoRIUcAABFVdwAB/2NsaW1hdGUvAmNsaW1hdGUuY2FwbnA6TWU/dGFkYXRhURABAf8BLnIwS0QGqwARGVL/2zSiaMkkjsQAERky/wyC0Abqf6+FABEVMv+3DBa46u2BxwAREWL/U3VwcG9ydGUAAWQfVmFsdWUfRW50cnn/SW5mb3JtYXQAB2lvblEIAwQAAAQBAAARKUIAAFEkAwFRQAIBEQEBFAEBAAARPSoAAFE4AwFRRAIBf2VudHJpZXMBDgABUAMBARD/DILQBup/r4UAAAEBDgABD2luZm8BEf+3DBa46u2BxwAAAQERAAE=",  # climate/climate.capnp:Metadata
    "ECxQBgb/AS5yMEtEBqsAER8D/7BtVWbp0jb7AAABM0YLzgwxFUoBESkHAAARJYcRfQcAAP9jbGltYXRlLwRjbGltYXRlLmNhcG5wOk1ldGFkYXRhLlN1cHBvcnRlZAAAUAEBUQgDBQAA/4JWOyl3doiVAUBLw6mOg57kETFaAAIRKQcBAf8I4vcFnDLSxgEV93Bm8x+n4BEdggACERUH/2NhdGVnb3JpAANlc0AB/3N1cHBvcnRlAWRWYWx1ZXMAQAFQAQE=",  # climate/climate.capnp:Metadata.Supported
    "EBVQBgb/glY7KXd2iJUAESkBAAAEBwABMRXaAQAE/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6TWV0YWRhdGEuU3VwcG9ydGVkLmNhdGVnb3JpZXMkUGFyYQNtcw==",  # climate/climate.capnp:Metadata.Supported.categories$Params
    "EClQBgb/QEvDqY6DnuQAESkBAAAFAQcAATEV4gEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6TWV0YWRhdGEuU3VwcG9ydGVkLmNhdGVnb3JpZXMkUmVzdQdsdHNRBAMEAAAEAQAAEQ0yAABRCAMBUSQCAR90eXBlcwEOAAFQAwEBEP/T2gP+y37L1AAAAQEOAAE=",  # climate/climate.capnp:Metadata.Supported.categories$Results
    "EEJQBgb/09oD/st+y9QAERQB/8mKqHWnyfGZAAUDBwAAMzwBnwExFRIBESUHAAARIa8AAf9jb21tb24vYwNvbW1vbi5jYXBucDpJZEluZm9ybWF0aW8BblABAVEMAwQAAAQBAAARRRoAAFFAAwFRTAIBEQEBFAEBAAARSSoAAFFEAwFRUAIBEQICFAECAAARTWIAAFFMAwFRWAIBA2lkAQwAAgEMAAEPbmFtZQEMAAIBDAAB/2Rlc2NyaXB0AAdpb24BDAACAQwAAQ==",  # common/common.capnp:IdInformation
    "ECVQBgb/COL3BZwy0sYAESkBAAAFAQcAATEVAgIAAREpPwAB/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6TWV0YWRhdGEuU3VwcG9ydGVkLnN1cHBvcnRlZFZhbHVlcyRQYXJhbXMAUQQDBAAABAEAABENOgAAUQgDAVEUAgE/dHlwZUlkAQwAAgEMAAE=",  # climate/climate.capnp:Metadata.Supported.supportedValues$Params
    "ECpQBgb/FfdwZvMfp+AAESkBAAAFAQcAATEVCgIAAREtPwAB/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6TWV0YWRhdGEuU3VwcG9ydGVkLnN1cHBvcnRlZFZhbHVlcyRSZXN1bHRzAABRBAMEAAAEAQAAEQ06AABRCAMBUSQCAT92YWx1ZXMBDgABUAMBARD/09oD/st+y9QAAAEBDgAB",  # climate/climate.capnp:Metadata.Supported.supportedValues$Results
    "EF9QBgb/2zSiaMkkjsQAUR8BAv+wbVVm6dI2+wBFAQcFAAAz0gxjDTEVKgERJQcAADEhHwEAAf9jbGltYXRlLwNjbGltYXRlLmNhcG5wOk1ldGFkYXRhLlYPYWx1ZVABAVEUAwQM//8EAQAAEX0qAABReAMBUYQCAR0B/v8BFAEBAAARgTIAAFF8AwFRiAIBHQL9/wEUAQIAABGFIgAAUYADAVGMAgEdA/z/QBQBAwAAEYkqAABRhAMBUZACAQ0E+/8UAQQAABGNKgAAUYgDAVGUAgEPdGV4dAEMAAIBDAABH2Zsb2F0AQsAAgELAAEHaW50AQUAAgEFAAEPYm9vbAEBAAIBAQABD2RhdGUBEP+NESIDrP7mlwAAAQEQAAE=",  # climate/climate.capnp:Metadata.Value
    "ED9QBgb/jREiA6z+5pcAURIBAf8q9geLwyvq6AAEBwAAMzwBJAIRFboRHQcAABEZrwAB/2NvbW1vbi9kAWF0ZS5jYXBuP3A6RGF0ZVABAVEMAwQAAAQBAAARRSoAAFFAAwFRTAIBEQECFAEBAAARSTIAAFFEAwFRUAIBEQIDFAECAAARTSIAAFFIAwFRVAIBD3llYXIBAwACAQMAAR9tb250aAEGAAIBBgABB2RheQEGAAIBBgAB",  # common/date.capnp:Date
    "EMtQBgb/DILQBup/r4UAUR8BAf+wbVVm6dI2+wBFAQcMAQEzQw6ADzEVKgERJQcAADEhpwIAAf9jbGltYXRlLwNjbGltYXRlLmNhcG5wOk1ldGFkYXRhLkUPbnRyeVABAVEwAwQM//8EAQAAE0EBIgAAUzwBAwFTSAECAQ0B/v8UAQEAABNFASIAAFNAAQMBU0wBAgENAv3/FAECAAATSQFaAABTSAEDAVNUAQIBDQP8/xQBAwAAE1EBIgAAU0wBAwFTWAECAQ0E+/8UAQQAABNVASIAAFNQAQMBU1wBAgENBfr/FAEFAAATWQE6AABTVAEDAVNgAQIBDQb5/xQBBgAAE10BQgAAU1gBAwFTZAECAQ0H+P8UAQcAABNhATIAAFNcAQMBU2gBAgENCPf/FAEIAAATZQEiAABTYAEDAVNsAQIBHQn2/wEUAQkAABNpASIAAFNkAQMBU3ABAgENCvX/FAEKAAATbQFSAABTbAEDAVN4AQIBDQv0/xQBCwAAE3UBYgAAU3QBAwFTgAECAQdnY20BD/8Qn97uaWg5zgAAAQEPAAEHcmNtAQ//UeODMMXecYYAAAEBDwAB/2hpc3RvcmljAANhbAAGB3JjcAEP/8yUDDF4B/OOAAABAQ8AAQdzc3ABD//uejQW5Ap40wAAAQEPAAE/ZW5zTWVtARD/NKRdzdGsysgAAAEBEAABf3ZlcnNpb24BDAACAQwAAR9zdGFydAEQ/40RIgOs/uaXAAABARAAAQdlbmQBEP+NESIDrP7mlwAAAQEQAAEHY28yAQoAAgEKAAH/cGljb250cm8AAWwABv9kZXNjcmlwdAAHaW9uAQwAAgEMAAE=",  # climate/climate.capnp:Metadata.Entry
    "ECpQBgb/twwWuOrtgccAER8D/7BtVWbp0jb7AAABM8APXBAxFVoBESkHAAARJYcRdQcAAP9jbGltYXRlLwRjbGltYXRlLmNhcG5wOk1ldGFkYXRhLkluZm9ybWF0aQNvblABAVEIAwUAAP8G1bfg8V5w3wHT2gP+y37L1BExOgACESUHAQH/CjP6kZzURuIBeO1fpQsDNZ8RGToAAhENBz9mb3JPbmVAAT9mb3JBbGxAAVABAQ==",  # climate/climate.capnp:Metadata.Information
    "ECVQBgb/BtW34PFecN8AESsBAAAFAQcAATEVygEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6TWV0YWRhdGEuSW5mb3JtYXRpb24uZm9yT25lJFBhcmFtcwAAUQQDBAAABAEAABENMgAAUQgDAVEUAgEfZW50cnkBEP8MgtAG6n+vhQAAAQEQAAE=",  # climate/climate.capnp:Metadata.Information.forOne$Params
    "EBVQBgb/CjP6kZzURuIAESsBAAAEBwABMRXKAQAE/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6TWV0YWRhdGEuSW5mb3JtYXRpb24uZm9yQWxsJFBhcmFtcwAA",  # climate/climate.capnp:Metadata.Information.forAll$Params
    "EDtQBgb/eO1fpQsDNZ8AESsBAAAFAQcAATEV0gEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6TWV0YWRhdGEuSW5mb3JtYXRpb24uZm9yQWxsJFJlc3VsdAFzUQQDBAAABAEAABENIgAAUQgDAVFsAgEHYWxsAQ4AAVADAQEQ/zNHFyVHhtS5AAAAQAERAR9RBAIB/zNHFyVHhtS5AAAAEQEnUQgBAQEBUQgDAQEBURADAQEQ/wyC0Abqf6+FAAABARD/09oD/st+y9QAAAEBDgAB",  # climate/climate.capnp:Metadata.Information.forAll$Results
    "EDZQBgb/M0cXJUeG1LkAERQB/8mKqHWnyfGZAAUCBxABM5MIwggRFcoRIQcAABEddwAAEZEX/2NvbW1vbi9jAm9tbW9uLmNhcG5wOlBhaXIAAFABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBB2ZzdAESAQH/M0cXJUeG1LkAAAABEgABB3NuZAESBQEB/zNHFyVHhtS5AAAAARIAAUEIAREFEhEFEgFGAVM=",  # common/common.capnp:Pair
    "EFVQBgb/8GBZ8NH9NfYAERYD/xhF6xDkOh2gAAABM6wQARURFfIRIRcAADExRwETEQEnAAD/Y2xpbWF0ZS8CY2xpbWF0ZS5jYXBucDpEYR90YXNldFEEAQH/deFP8UOgG9YAEQGq/0dldExvY2F0AWlvbnNDYWxsD2JhY2tRFAMFAAD/FUjobpBGw7QBsG1VZunSNvsRkUoAAhGJBwEB/xNKTyg9b0mwAR5qrwOqX+7tEX2iAAIReQcBAv9/XaGisGf42QFcc8JbbkYM4xFtagACEWUHAQP/utQobIUuoNIB3V8dQNz8jKoRWVIAAhFRBwEE/wZFtjH08KP8AQb6eYtX27qeEUWCAAIRPQf/bWV0YWRhdGEAAABAAf9jbG9zZXN0VAFpbWVTZXJpZQdzQXRAAf90aW1lU2VyaQAPZXNBdEAB/2xvY2F0aW9uAAFzQAH/c3RyZWFtTG8BY2F0aW9ucwBAAVEIAQH/1UicWcvRr7IAAAD/Zcs23KDap8EAAAA=",  # climate/climate.capnp:Dataset
    "ECJQBgb/deFP8UOgG9YAER4D//BgWfDR/TX2AAABMwUTxxMxFZoBES0HAAARKUcRVQcAAP9jbGltYXRlLwVjbGltYXRlLmNhcG5wOkRhdGFzZXQuR2V0TG9jYXRpb25zQ2FsbGJhA2NrUAEBUQQDBQAA/+DUxD2ZEkHmAfFdBtjVQIX6ERFyAAIRCQf/bmV4dExvY2EAH3Rpb25zQAFQAQE=",  # climate/climate.capnp:Dataset.GetLocationsCallback
    "ECdQBgb/4NTEPZkSQeYAUTMBAQAABAcAATEVQgIAAREtPwAB/2NsaW1hdGUvCGNsaW1hdGUuY2FwbnA6RGF0YXNldC5HZXRMb2NhdGlvbnNDYWxsYmFjay5uZXh0TG9jYXRpb25zJFBhcmFtcwBRBAMEAAAEAQAAEQ1KAABRDAMBURgCAf9tYXhDb3VudAAAAAEFAAIBBQAB",  # climate/climate.capnp:Dataset.GetLocationsCallback.nextLocations$Params
    "ECxQBgb/8V0G2NVAhfoAETMBAAAFAQcAATEVSgIAARExPwAB/2NsaW1hdGUvCGNsaW1hdGUuY2FwbnA6RGF0YXNldC5HZXRMb2NhdGlvbnNDYWxsYmFjay5uZXh0TG9jYXRpb25zJFJlc3VsdHMAAFEEAwQAAAQBAAARDVIAAFEMAwFRKAIB/2xvY2F0aW9uAAFzAQ4AAVADAQEQ/xn+E/OFc7qFAAABAQ4AAQ==",  # climate/climate.capnp:Dataset.GetLocationsCallback.nextLocations$Results
    "EGhQBgb/Gf4T84VzuoUAURYBAf8YResQ5DodoAAFBAcAADPBGtQcERX6ESEXAAAxKR8BAAH/Y2xpbWF0ZS8CY2xpbWF0ZS5jYXBucDpMbz9jYXRpb25RBAEB/2rU5jqlE/3FABEBGgNLVlEUAwQAAAQBAAARfRoAAFF4AwFRhAIBAQEUAQEAABGBSgAAUYADAVGMAgERAgEUAQIAABGJOgAAUYQDAVGQAgERAwIUAQMAABGNWgAAUYwDAVGYAgERBAMUAQQAABGVWgAAUZQDAVGwAgEDaWQBEP/T2gP+y37L1AAAAQEQAAH/aGVpZ2h0Tk4AAAABCgACAQoAAT9sYXRsb24BEP/7j8w5MPzx7AAAAQEQAAH/dGltZVNlcmkAA2VzARH/6G1u/kCfdqcAAAEBEQAB/2N1c3RvbURhAAN0YQEOAAFQAwEBEP9q1OY6pRP9xQAAAQEOAAE=",  # climate/climate.capnp:Location
    "EDJQBgb/atTmOqUT/cUAER8B/xn+E/OFc7qFAAUCBwAAMzccdBwxFRIBESUHAAARIXcAAf9jbGltYXRlLwNjbGltYXRlLmNhcG5wOkxvY2F0aW9uLksBVlABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLTIAAFEoAwFRNAIBB2tleQEMAAIBDAABH3ZhbHVlARIAAgESAAE=",  # climate/climate.capnp:Location.KV
    "EDFQBgb/+4/MOTD88ewAUQ4BAv8k/Md5IFSQkAAEBwAAMxADfwMRFdIRIQcAABEddwAB/2dlby9nZW8uAmNhcG5wOkxhdExvbkNvb3IBZFABAVEIAwQAAAQBAAARKSIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBB2xhdAELAAIBCwABB2xvbgELAAIBCwAB",  # geo/geo.capnp:LatLonCoord
    "EHxQBgb/6G1u/kCfdqcAERYD/xhF6xDkOh2gAAABM9Yc2yIxFQoBESUXAAAxMUcCE60BJwAA/2NsaW1hdGUvA2NsaW1hdGUuY2FwbnA6VGltZVNlcmllcwAAUQQBAf/CA+xjz8pmtAARAVr/UmVzb2x1dGkAA29uUSQDBQAA/9H9ctIZBT/qAdZupqHZrQ7NExEBWgACEwkBBwEB/xbJI2sMz2v/ARssAnb0J+y5Ef0yAAIR8QcBAv+hl4quAnDXjwFQoE8UbxR2iRHlOgACEdkHAQP/zX1dxGuYeI4B6eo+10g0PZwRzSoAAhHBBwEE/yU1hbEj+fjvAfuU6qbA3uDCEbUyAAIRqQcBBf/ub0nib1uq+AEytwl9FOff9xGdSgACEZUHAQb/uJP26N5kw4wB34DoymOBI8MRiVIAAhGBBwEH/zRmlVwixCzOAbBtVWbp0jb7EXVKAAIRbQcBCP8Tow8bsJ4yywEZ/hPzhXO6hRFhSgACEVkH/3Jlc29sdXRpAANvbkABH3JhbmdlQAE/aGVhZGVyQAEPZGF0YUABH2RhdGFUQAH/c3VicmFuZ2UAAABAAf9zdWJoZWFkZQABckAB/21ldGFkYXRhAAAAQAH/bG9jYXRpb24AAABAAVEIAQH/1UicWcvRr7IAAAD/Zcs23KDap8EAAAA=",  # climate/climate.capnp:TimeSeries
    "EB1QBgb/wgPsY8/KZrQAESEC/+htbv5An3anAAABM1EdrR0xFWIBESkHAAARJTcAAf9jbGltYXRlLwRjbGltYXRlLmNhcG5wOlRpbWVTZXJpZXMuUmVzb2x1dAdpb25QAQFRCAECAAARETIAAAEBEQk6AAAfZGFpbHk/aG91cmx5",  # climate/climate.capnp:TimeSeries.Resolution
    "EBRQBgb/0f1y0hkFP+oAESEBAAAEBwABMRWaAQAE/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5yZXNvbHV0aW9uJFBhcmEDbXM=",  # climate/climate.capnp:TimeSeries.resolution$Params
    "ECVQBgb/1m6modmtDs0AUSEBAQAABAcAATEVogEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5yZXNvbHV0aW9uJFJlc3UHbHRzUQQDBAAABAEAABENWgAAUQwDAVEYAgH/cmVzb2x1dGkAA29uAQ//wgPsY8/KZrQAAAEBDwAB",  # climate/climate.capnp:TimeSeries.resolution$Results
    "EBNQBgb/FskjawzPa/8AESEBAAAEBwABMRVyAQAE/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5yYW5nZSRQH2FyYW1z",  # climate/climate.capnp:TimeSeries.range$Params
    "EDNQBgb/GywCdvQn7LkAESEBAAAFAgcAATEVegEAAREhdwAB/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5yYW5nZSRSP2VzdWx0c1EIAwQAAAQBAAARKVIAAFEoAwFRNAIBEQEBFAEBAAARMUIAAFEsAwFROAIB/3N0YXJ0RGF0AAFlARD/jREiA6z+5pcAAAEBEAABf2VuZERhdGUBEP+NESIDrP7mlwAAAQEQAAE=",  # climate/climate.capnp:TimeSeries.range$Results
    "EBNQBgb/oZeKrgJw148AESEBAAAEBwABMRV6AQAE/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5oZWFkZXIkP1BhcmFtcw==",  # climate/climate.capnp:TimeSeries.header$Params
    "ECdQBgb/UKBPFG8UdokAESEBAAAFAQcAATEVggEAAREhPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5oZWFkZXIkUmVzdWx0cwBRBAMEAAAEAQAAEQ06AABRCAMBUSQCAT9oZWFkZXIBDgABUAMBAQ//ZLVa27RgV+MAAAEBDgAB",  # climate/climate.capnp:TimeSeries.header$Results
    "EGxQBgb/ZLVa27RgV+MAERYC/xhF6xDkOh2gAAABM0UVvxoRFfIRIQcAADEdzwEAAf9jbGltYXRlLwJjbGltYXRlLmNhcG5wOkVsH2VtZW50UAEBUUwBAgAAEd0qAAABARHVKgAAAQIRzSoAAAEDEcU6AAABBBG9QgAAAQURtSoAAAEGEa1KAAABBxGpYgAAAQgRpUoAAAEJEaFKAAABChGdWgAAAQsRmSIAAAEMEZEaAAABDRGJIgAAAQ4RgWoAAAEPEX2KAAABEBF9agAAARExeSIBAAABEhGBMgAAD3RtaW4PdGF2Zw90bWF4P3ByZWNpcH9nbG9icmFkD3dpbmT/c3VuaG91cnMAAAD/Y2xvdWRhbW8AB3VudP9yZWxodW1pZAAAAP9haXJwcmVzcwAAAP92YXBvcnByZQADc3MHY28yA28zB2V0MP9kZXdwb2ludAAPVGVtcP9zcGVjaWZpYwFIdW1pZGl0eQAA/3Nub3dmYWxsAA9GbHV4/3N1cmZhY2VEA293bndlbGxpbmdMb25nd2F2ZVJhZGlhdAdpb24fcG90RVQ=",  # climate/climate.capnp:Element
    "EBNQBgb/zX1dxGuYeI4AESEBAAAEBwABMRVqAQAE/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5kYXRhJFBhD3JhbXM=",  # climate/climate.capnp:TimeSeries.data$Params
    "ECtQBgb/6eo+10g0PZwAESEBAAAFAQcAATEVcgEAAREhPwAB/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5kYXRhJFJlH3N1bHRzUQQDBAAABAEAABENKgAAUQgDAVE0AgEPZGF0YQEOAAFQAwEBDgABUAMBAQoAAgEOAAE=",  # climate/climate.capnp:TimeSeries.data$Results
    "EBNQBgb/JTWFsSP5+O8AESEBAAAEBwABMRVyAQAE/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5kYXRhVCRQH2FyYW1z",  # climate/climate.capnp:TimeSeries.dataT$Params
    "ECtQBgb/+5TqpsDe4MIAESEBAAAFAQcAATEVegEAAREhPwAB/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5kYXRhVCRSP2VzdWx0c1EEAwQAAAQBAAARDSoAAFEIAwFRNAIBD2RhdGEBDgABUAMBAQ4AAVADAQEKAAIBDgAB",  # climate/climate.capnp:TimeSeries.dataT$Results
    "EDNQBgb/7m9J4m9bqvgAESEBAAAFAgcAATEVigEAAREldwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5zdWJyYW5nZSRQYXJhbXMAAFEIAwQAAAQBAAARKTIAAFEkAwFRMAIBEQEBFAEBAAARLSIAAFEoAwFRNAIBH3N0YXJ0ARD/jREiA6z+5pcAAAEBEAABB2VuZAEQ/40RIgOs/uaXAAABARAAAQ==",  # climate/climate.capnp:TimeSeries.subrange$Params
    "ECVQBgb/MrcJfRTn3/cAESEBAAAFAQcAATEVkgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5zdWJyYW5nZSRSZXN1bHQBc1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/3RpbWVTZXJpAANlcwER/+htbv5An3anAAABAREAAQ==",  # climate/climate.capnp:TimeSeries.subrange$Results
    "EClQBgb/uJP26N5kw4wAESEBAAAFAQcAATEVkgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5zdWJoZWFkZXIkUGFyYW0Bc1EEAwQAAAQBAAARDUoAAFEMAwFRKAIB/2VsZW1lbnRzAAAAAQ4AAVADAQEP/2S1Wtu0YFfjAAABAQ4AAQ==",  # climate/climate.capnp:TimeSeries.subheader$Params
    "ECVQBgb/34DoymOBI8MAESEBAAAFAQcAATEVmgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5zdWJoZWFkZXIkUmVzdWwDdHNRBAMEAAAEAQAAEQ1aAABRDAMBURgCAf90aW1lU2VyaQADZXMBEf/obW7+QJ92pwAAAQERAAE=",  # climate/climate.capnp:TimeSeries.subheader$Results
    "EBRQBgb/NGaVXCLELM4AESEBAAAEBwABMRWKAQAE/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5tZXRhZGF0YSRQYXJhbXMAAA==",  # climate/climate.capnp:TimeSeries.metadata$Params
    "EBRQBgb/E6MPG7CeMssAESEBAAAEBwABMRWKAQAE/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6VGltZVNlcmllcy5sb2NhdGlvbiRQYXJhbXMAAA==",  # climate/climate.capnp:TimeSeries.location$Params
    "EBNQBgb/FUjobpBGw7QAER4BAAAEBwABMRVyAQAE/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6RGF0YXNldC5tZXRhZGF0YSRQH2FyYW1z",  # climate/climate.capnp:Dataset.metadata$Params
    "ECVQBgb/E0pPKD1vSbAAER4BAAAFAQcAATEVygEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6RGF0YXNldC5jbG9zZXN0VGltZVNlcmllc0F0JFBhcmFtcwAAUQQDBAAABAEAABENOgAAUQgDAVEUAgE/bGF0bG9uARD/+4/MOTD88ewAAAEBEAAB",  # climate/climate.capnp:Dataset.closestTimeSeriesAt$Params
    "ECZQBgb/HmqvA6pf7u0AER4BAAAFAQcAATEV0gEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6RGF0YXNldC5jbG9zZXN0VGltZVNlcmllc0F0JFJlc3VsdAFzUQQDBAAABAEAABENWgAAUQwDAVEYAgH/dGltZVNlcmkAA2VzARH/6G1u/kCfdqcAAAEBEQAB",  # climate/climate.capnp:Dataset.closestTimeSeriesAt$Results
    "ECVQBgb/f12horBn+NkAER4BAAAFAQcAATEVkgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6RGF0YXNldC50aW1lU2VyaWVzQXQkUGFyYW0Bc1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/2xvY2F0aW9uAANJZAEMAAIBDAAB",  # climate/climate.capnp:Dataset.timeSeriesAt$Params
    "ECVQBgb/XHPCW25GDOMAER4BAAAFAQcAATEVmgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6RGF0YXNldC50aW1lU2VyaWVzQXQkUmVzdWwDdHNRBAMEAAAEAQAAEQ1aAABRDAMBURgCAf90aW1lU2VyaQADZXMBEf/obW7+QJ92pwAAAQERAAE=",  # climate/climate.capnp:Dataset.timeSeriesAt$Results
    "EBNQBgb/utQobIUuoNIAER4BAAAEBwABMRV6AQAE/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6RGF0YXNldC5sb2NhdGlvbnMkP1BhcmFtcw==",  # climate/climate.capnp:Dataset.locations$Params
    "EChQBgb/3V8dQNz8jKoAER4BAAAFAQcAATEVggEAAREhPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6RGF0YXNldC5sb2NhdGlvbnMkUmVzdWx0cwBRBAMEAAAEAQAAEQ1SAABRDAMBUSgCAf9sb2NhdGlvbgABcwEOAAFQAwEBEP8Z/hPzhXO6hQAAAQEOAAE=",  # climate/climate.capnp:Dataset.locations$Results
    "ECZQBgb/BkW2MfTwo/wAER4BAAAFAQcAATEVqgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6RGF0YXNldC5zdHJlYW1Mb2NhdGlvbnMkUGEPcmFtc1EEAwQAAAQBAAARDaoAAFEQAwFRHAIB/3N0YXJ0QWZ0AWVyTG9jYXRpD29uSWQBDAACAQwAAQ==",  # climate/climate.capnp:Dataset.streamLocations$Params
    "ECZQBgb/Bvp5i1fbup4AER4BAAAFAQcAATEVsgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6RGF0YXNldC5zdHJlYW1Mb2NhdGlvbnMkUmUfc3VsdHNRBAMEAAAEAQAAEQ2SAABREAMBURwCAf9sb2NhdGlvbgFzQ2FsbGJhYwFrARH/deFP8UOgG9YAAAEBEQAB",  # climate/climate.capnp:Dataset.streamLocations$Results
    "EDJQBgb/oOUiX+x/ptcAERYB/xhF6xDkOh2gAAUCBwAAMwMVQxUxFRoBESUHAAARIXcAAf9jbGltYXRlLwNjbGltYXRlLmNhcG5wOk1ldGFQbHVzRGEDdGFQAQFRCAMEAAAEAQAAESkqAABRJAMBUTACAREBARQBAQAAES0qAABRKAMBUTQCAQ9tZXRhARD/sG1VZunSNvsAAAEBEAABD2RhdGEBEf/wYFnw0f019gAAAQERAAE=",  # climate/climate.capnp:MetaPlusData
    "EH1QBgb/T5bGm/XMwfEAURYBAf8YResQ5DodoAAFBAcAADPdItAkMRUqARElBwAAMSFXAQAB/2NsaW1hdGUvA2NsaW1hdGUuY2FwbnA6VGltZVNlcmllcw9EYXRhUAEBURgDBAAABAEAABGZKgAAUZQDAVHAAgEBARQBAQAAEb1qAABRvAMBUcgCARECARQBAgAAEcU6AABRwAMBUdwCAREDAhQBAwAAEdlSAABR2AMBUeQCAREEAxQBBAAAEeFCAABR3AMBUegCAREFARQBBQEBEeVaAABR5AMBUfACAQ9kYXRhAQ4AAVADAQEOAAFQAwEBCgACAQ4AAf9pc1RyYW5zcAAPb3NlZAEBAAIBAQABP2hlYWRlcgEOAAFQAwEBD/9ktVrbtGBX4wAAAQEOAAH/c3RhcnREYXQAAWUBEP+NESIDrP7mlwAAAQEQAAF/ZW5kRGF0ZQEQ/40RIgOs/uaXAAABARAAAf9yZXNvbHV0aQADb24BD//CA+xjz8pmtAAAAQEPAAE=",  # climate/climate.capnp:TimeSeriesData
    "EC9QBgb/XwwrNdQIff4AERYD/xhF6xDkOh2gAAABM9IkoyYRFfIRIQcAABEdhxF5JwAA/2NsaW1hdGUvAmNsaW1hdGUuY2FwbnA6U2UfcnZpY2VQAQFRCAMFAAD/UdQFlEjKTIAB6MY1lIWAaJERMaoAAhEtBwEB/9vmo92DH32dAbDqsHSR95XNESF6AAIRGQf/Z2V0QXZhaWwBYWJsZURhdGEPc2V0c0AB/2dldERhdGFzAD9ldHNGb3JAAVEIAQH/1UicWcvRr7IAAAD/Zcs23KDap8EAAAA=",  # climate/climate.capnp:Service
    "EBVQBgb/UdQFlEjKTIAAER4BAAAEBwABMRXSAQAE/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6U2VydmljZS5nZXRBdmFpbGFibGVEYXRhc2V0cyRQYXJhbQFz",  # climate/climate.capnp:Service.getAvailableDatasets$Params
    "ECpQBgb/6MY1lIWAaJEAER4BAAAFAQcAATEV2gEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6U2VydmljZS5nZXRBdmFpbGFibGVEYXRhc2V0cyRSZXN1bAN0c1EEAwQAAAQBAAARDUoAAFEMAwFRKAIB/2RhdGFzZXRzAAAAAQ4AAVADAQEQ/6DlIl/sf6bXAAABAQ4AAQ==",  # climate/climate.capnp:Service.getAvailableDatasets$Results
    "ECVQBgb/2+aj3YMffZ0AER4BAAAFAQcAATEVogEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6U2VydmljZS5nZXREYXRhc2V0c0ZvciRQYXIHYW1zUQQDBAAABAEAABENSgAAUQwDAVEYAgH/dGVtcGxhdGUAAAABEP+wbVVm6dI2+wAAAQEQAAE=",  # climate/climate.capnp:Service.getDatasetsFor$Params
    "EClQBgb/sOqwdJH3lc0AER4BAAAFAQcAATEVqgEAARElPwAB/2NsaW1hdGUvBWNsaW1hdGUuY2FwbnA6U2VydmljZS5nZXREYXRhc2V0c0ZvciRSZXMPdWx0c1EEAwQAAAQBAAARDUoAAFEMAwFRKAIB/2RhdGFzZXRzAAAAAQ4AAVADAQER//BgWfDR/TX2AAABAQ4AAQ==",  # climate/climate.capnp:Service.getDatasetsFor$Results
    "ECZQBgb/2SmZxWzCGKQAERYD/xhF6xDkOh2gAAABM6UmqSkxFVoBESkXAAARNUcRXRcAAP9jbGltYXRlLwRjbGltYXRlLmNhcG5wOkNTVlRpbWVTZXJpZXNGYWN0bwNyeVEEAQH/uJBm9KkcqOsAEQFS/0NTVkNvbmZpAAFnUQQDBQAA/0cFdQEmjarPATRVrsjrr+/vERE6AAIRBQc/Y3JlYXRlQAFRBAEB/9VInFnL0a+yAAAA",  # climate/climate.capnp:CSVTimeSeriesFactory
    "EG9QBgb/uJBm9KkcqOsAUSsBAf/ZKZnFbMIYpAAFAgcAADMTJxUpMRWqAREtBwAAESnnAAH/Y2xpbWF0ZS8FY2xpbWF0ZS5jYXBucDpDU1ZUaW1lU2VyaWVzRmFjdG9yeS5DU1ZDbw9uZmlnUAEBURADBAAABAEBARFhIgAAUVwDAVFoAgERAQEUAQEAABFpUgAAUWgDAVHMAgEBAhQBAgEBEcmSAABRzAMBUdgCAREDARQBAwEBEdXSAABR3AMBUegCAQdzZXABDAACAQwAABEBEgEs/2hlYWRlck1hAAFwAQ4AAVADAQEQ/zNHFyVHhtS5AAAAQAERAR9RBAIB/zNHFyVHhtS5AAAAEQEnUQgBAQEBUQgDAQEBURADAQEMAAIBDAACAQ4AAf9za2lwTGluZQFzVG9IZWFkZQFyAQMAAgEDAAH/c2tpcExpbmUCc0Zyb21IZWFkZXJUb0RhdAFhAQMAAgUDAQAB",  # climate/climate.capnp:CSVTimeSeriesFactory.CSVConfig
    "EDRQBgb/RwV1ASaNqs8AESsBAAAFAgcAATEVygEAAREpdwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6Q1NWVGltZVNlcmllc0ZhY3RvcnkuY3JlYXRlJFBhcmFtcwAAUQgDBAAABAEAABEpQgAAUSQDAVEwAgERAQEUAQEAABEtOgAAUSgDAVE0AgF/Y3N2RGF0YQEMAAIBDAABP2NvbmZpZwEQ/7iQZvSpHKjrAAABARAAAQ==",  # climate/climate.capnp:CSVTimeSeriesFactory.create$Params
    "EDVQBgb/NFWuyOuv7+8AESsBAAAFAgcAATEV0gEAAREpdwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6Q1NWVGltZVNlcmllc0ZhY3RvcnkuY3JlYXRlJFJlc3VsdAFzUQgDBAAABAEAABEpWgAAUSgDAVE0AgERAQEUAQEAABExMgAAUSwDAVE4AgH/dGltZXNlcmkAA2VzARH/6G1u/kCfdqcAAAEBEQABH2Vycm9yAQwAAgEMAAE=",  # climate/climate.capnp:CSVTimeSeriesFactory.create$Results
    "EFdQBgb/soSXl++A9OEAERYD/xhF6xDkOh2gAAABM6spNS0xFWoBESknAAAxQUcBEyEBFwAA/2NsaW1hdGUvBGNsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhD3BwZXJRCAEB/8W+kPO6uYXQABEJQv/KWMMHUXjdtQARBVJ/QWx0ZXJlZP9BbHRlclR5cAABZVEUAwUAAP+pNvvZ7iYf4wGq95CPtd0u+xGRkgACEY0HAQH/noZB2gwioMsBZhdxvLV1W90RgYIAAhF5BwEC/+TmKSmcHmvTARyEvoBi7KHEEW0yAAIRYQcBA/9T/0VN/vx72wE7ABMwsoBJ9BFVOgACEUkHAQT/aFB+vS0WCI8Bu5TNgn54CosRPcoAAhE9B/93cmFwcGVkVAFpbWVTZXJpZQFzQAH/YWx0ZXJlZEUBbGVtZW50cwBAAR9hbHRlckABP3JlbW92ZUAB/3JlcGxhY2VXAnJhcHBlZFRpbWVTZXJpZXMAAEABUQQBAf/obW7+QJ92pwAAAA==",  # climate/climate.capnp:AlterTimeSeriesWrapper
    "EENQBgb/xb6Q87q5hdAAUS0BAf+yhJeX74D04QAEBwAAM6kqBSsxFaoBES0HAAARKa8AAf9jbGltYXRlLwVjbGltYXRlLmNhcG5wOkFsdGVyVGltZVNlcmllc1dyYXBwZXIuQWx0D2VyZWRQAQFRDAMEAAAEAQAAEUVCAABRQAMBUUwCAREBARQBAQAAEUkyAABRRAMBUVACARECARQBAgAAEU0qAABRSAMBUVQCAX9lbGVtZW50AQ//ZLVa27RgV+MAAAEBDwABH3ZhbHVlAQoAAgEKAAEPdHlwZQEP/8pYwwdReN21AAABAQ8AAQ==",  # climate/climate.capnp:AlterTimeSeriesWrapper.Altered
    "EB5QBgb/yljDB1F43bUAES0C/7KEl5fvgPThAAABM2orlisxFboBES0HAAARKTcAAf9jbGltYXRlLwVjbGltYXRlLmNhcG5wOkFsdGVyVGltZVNlcmllc1dyYXBwZXIuQWx0P2VyVHlwZVABAVEIAQIAABERIgAAAQERCSIAAAdhZGQHbXVs",  # climate/climate.capnp:AlterTimeSeriesWrapper.AlterType
    "EBZQBgb/qTb72e4mH+MAES0BAAAEBwABMRUyAgAE/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci53cmFwcGVkVGltZVNlcmllcyRQH2FyYW1z",  # climate/climate.capnp:AlterTimeSeriesWrapper.wrappedTimeSeries$Params
    "ECdQBgb/qveQj7XdLvsAES0BAAAFAQcAATEVOgIAAREtPwAB/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci53cmFwcGVkVGltZVNlcmllcyRSP2VzdWx0c1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/3RpbWVTZXJpAANlcwER/+htbv5An3anAAABAREAAQ==",  # climate/climate.capnp:AlterTimeSeriesWrapper.wrappedTimeSeries$Results
    "EBZQBgb/noZB2gwioMsAES0BAAAEBwABMRUiAgAE/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci5hbHRlcmVkRWxlbWVudHMkUGFyB2Ftcw==",  # climate/climate.capnp:AlterTimeSeriesWrapper.alteredElements$Params
    "ECpQBgb/ZhdxvLV1W90AES0BAAAFAQcAATEVKgIAAREtPwAB/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci5hbHRlcmVkRWxlbWVudHMkUmVzD3VsdHNRBAMEAAAEAQAAEQ0qAABRCAMBUSQCAQ9saXN0AQ4AAVADAQEQ/8W+kPO6uYXQAAABAQ4AAQ==",  # climate/climate.capnp:AlterTimeSeriesWrapper.alteredElements$Results
    "EDVQBgb/5OYpKZwea9MAUS0BAQAABQEHAAExFdIBAAERKXcAAf9jbGltYXRlLwZjbGltYXRlLmNhcG5wOkFsdGVyVGltZVNlcmllc1dyYXBwZXIuYWx0ZXIkUGFyYW0Bc1EIAwQAAAQBAAARKSoAAFEkAwFRMAIBAQEUAQEBAREtggAAUSwDAVE4AgEPZGVzYwEQ/8W+kPO6uYXQAAABARAAAf9hc05ld1RpbQFlU2VyaWVzAAEBAAIBAQAB",  # climate/climate.capnp:AlterTimeSeriesWrapper.alter$Params
    "ECZQBgb/HIS+gGLsocQAES0BAAAFAQcAATEV2gEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci5hbHRlciRSZXN1bAN0c1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/3RpbWVTZXJpAANlcwER/+htbv5An3anAAABAREAAQ==",  # climate/climate.capnp:AlterTimeSeriesWrapper.alter$Results
    "ECZQBgb/U/9FTf78e9sAUS0BAQAABAcAATEV2gEAAREpPwAB/2NsaW1hdGUvBmNsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci5yZW1vdmUkUGFyYQNtc1EEAwQAAAQBAAARDXoAAFEMAwFRGAIB/2FsdGVyZWRFAD9sZW1lbnQBD/9ktVrbtGBX4wAAAQEPAAE=",  # climate/climate.capnp:AlterTimeSeriesWrapper.remove$Params
    "EBVQBgb9OxMwsoBJ9BEtAQAABAcAATEV4gEABP9jbGltYXRlLwZjbGltYXRlLmNhcG5wOkFsdGVyVGltZVNlcmllc1dyYXBwZXIucmVtb3ZlJFJlc3UHbHRz",  # climate/climate.capnp:AlterTimeSeriesWrapper.remove$Results
    "EChQBgb/aFB+vS0WCI8AES0BAAAFAQcAATEVagIAARExPwAB/2NsaW1hdGUvCGNsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci5yZXBsYWNlV3JhcHBlZFRpbWVTZXJpZXMkUGEPcmFtc1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/3RpbWVTZXJpAANlcwER/+htbv5An3anAAABAREAAQ==",  # climate/climate.capnp:AlterTimeSeriesWrapper.replaceWrappedTimeSeries$Params
    "EBdQBgb/u5TNgn54CosAES0BAAAEBwABMRVyAgAE/2NsaW1hdGUvCGNsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlci5yZXBsYWNlV3JhcHBlZFRpbWVTZXJpZXMkUmUfc3VsdHM=",  # climate/climate.capnp:AlterTimeSeriesWrapper.replaceWrappedTimeSeries$Results
    "ECNQBgb/RCelovAt8cUAERYD/xhF6xDkOh2gAAABMzctVC4xFaIBES0HAAARKUcRURcAAP9jbGltYXRlLwVjbGltYXRlLmNhcG5wOkFsdGVyVGltZVNlcmllc1dyYXBwZXJGYWN0B29yeVABAVEEAwUAAP/+iwHcBkgGlQERXc2brIKJtBERKgACEQUHD3dyYXBAAVEEAQH/1UicWcvRr7IAAAA=",  # climate/climate.capnp:AlterTimeSeriesWrapperFactory
    "ECZQBgb//osB3AZIBpUAETQBAAAFAQcAATEVAgIAAREpPwAB/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlckZhY3Rvcnkud3JhcCRQYXJhbXMAUQQDBAAABAEAABENWgAAUQwDAVEYAgH/dGltZVNlcmkAA2VzARH/6G1u/kCfdqcAAAEBEQAB",  # climate/climate.capnp:AlterTimeSeriesWrapperFactory.wrap$Params
    "ECZQBgb/EV3Nm6yCibQAETQBAAAFAQcAATEVCgIAAREtPwAB/2NsaW1hdGUvB2NsaW1hdGUuY2FwbnA6QWx0ZXJUaW1lU2VyaWVzV3JhcHBlckZhY3Rvcnkud3JhcCRSZXN1bHRzAABRBAMEAAAEAQAAEQ1CAABRCAMBURQCAX93cmFwcGVyARH/soSXl++A9OEAAAEBEQAB",  # climate/climate.capnp:AlterTimeSeriesWrapperFactory.wrap$Results
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
GCM = _EnumModule(_loader.get(0xCE396869EEDE9F10).as_enum(), "GCM")
RCM = _EnumModule(_loader.get(0x8671DEC53083E351).as_enum(), "RCM")
SSP = _EnumModule(_loader.get(0xD3780AE416347AEE).as_enum(), "SSP")
RCP = _EnumModule(_loader.get(0x8EF30778310C94CC).as_enum(), "RCP")
EnsembleMember = _StructModule(
    _loader.get(0xC8CAACD1CD5DA434).as_struct(),
    "EnsembleMember",
)
Metadata = _StructModule(_loader.get(0xFB36D2E966556DB0).as_struct(), "Metadata")
Metadata.Supported = _InterfaceModule(
    _loader.get(0xAB06444B30722E01).as_interface(),
    "Supported",
)
Metadata.Value = _StructModule(_loader.get(0xC48E24C968A234DB).as_struct(), "Value")
Metadata.Entry = _StructModule(_loader.get(0x85AF7FEA06D0820C).as_struct(), "Entry")
Metadata.Information = _InterfaceModule(
    _loader.get(0xC781EDEAB8160CB7).as_interface(),
    "Information",
)
Dataset = _InterfaceModule(_loader.get(0xF635FDD1F05960F0).as_interface(), "Dataset")
Dataset.GetLocationsCallback = _InterfaceModule(
    _loader.get(0xD61BA043F14FE175).as_interface(),
    "GetLocationsCallback",
)
MetaPlusData = _StructModule(
    _loader.get(0xD7A67FEC5F22E5A0).as_struct(),
    "MetaPlusData",
)
Element = _EnumModule(_loader.get(0xE35760B4DB5AB564).as_enum(), "Element")
Location = _StructModule(_loader.get(0x85BA7385F313FE19).as_struct(), "Location")
Location.KV = _StructModule(_loader.get(0xC5FD13A53AE6D46A).as_struct(), "KV")
TimeSeries = _InterfaceModule(
    _loader.get(0xA7769F40FE6E6DE8).as_interface(),
    "TimeSeries",
)
TimeSeries.Resolution = _EnumModule(
    _loader.get(0xB466CACF63EC03C2).as_enum(),
    "Resolution",
)
TimeSeriesData = _StructModule(
    _loader.get(0xF1C1CCF59BC6964F).as_struct(),
    "TimeSeriesData",
)
Service = _InterfaceModule(_loader.get(0xFE7D08D4352B0C5F).as_interface(), "Service")
CSVTimeSeriesFactory = _InterfaceModule(
    _loader.get(0xA418C26CC59929D9).as_interface(),
    "CSVTimeSeriesFactory",
)
CSVTimeSeriesFactory.CSVConfig = _StructModule(
    _loader.get(0xEBA81CA9F46690B8).as_struct(),
    "CSVConfig",
)
AlterTimeSeriesWrapper = _InterfaceModule(
    _loader.get(0xE1F480EF979784B2).as_interface(),
    "AlterTimeSeriesWrapper",
)
AlterTimeSeriesWrapper.Altered = _StructModule(
    _loader.get(0xD085B9BAF390BEC5).as_struct(),
    "Altered",
)
AlterTimeSeriesWrapper.AlterType = _EnumModule(
    _loader.get(0xB5DD785107C358CA).as_enum(),
    "AlterType",
)
AlterTimeSeriesWrapperFactory = _InterfaceModule(
    _loader.get(0xC5F12DF0A2A52744).as_interface(),
    "AlterTimeSeriesWrapperFactory",
)

AlterTimeSeriesWrapperFactory.Server.WrapResultTuple = NamedTuple(
    "WrapResultTuple",
    [("wrapper", object)],
)
AlterTimeSeriesWrapper.Server.AlterResultTuple = NamedTuple(
    "AlterResultTuple",
    [("timeSeries", object)],
)
AlterTimeSeriesWrapper.Server.AlteredelementsResultTuple = NamedTuple(
    "AlteredelementsResultTuple",
    [("list", object)],
)
AlterTimeSeriesWrapper.Server.WrappedtimeseriesResultTuple = NamedTuple(
    "WrappedtimeseriesResultTuple",
    [("timeSeries", object)],
)
CSVTimeSeriesFactory.Server.CreateResultTuple = NamedTuple(
    "CreateResultTuple",
    [("timeseries", object), ("error", object)],
)
Dataset.Server.ClosesttimeseriesatResultTuple = NamedTuple(
    "ClosesttimeseriesatResultTuple",
    [("timeSeries", object)],
)
Dataset.Server.LocationsResultTuple = NamedTuple(
    "LocationsResultTuple",
    [("locations", object)],
)
Dataset.Server.MetadataResultTuple = NamedTuple(
    "MetadataResultTuple",
    [("entries", object), ("info", object)],
)
Dataset.Server.StreamlocationsResultTuple = NamedTuple(
    "StreamlocationsResultTuple",
    [("locationsCallback", object)],
)
Dataset.Server.TimeseriesatResultTuple = NamedTuple(
    "TimeseriesatResultTuple",
    [("timeSeries", object)],
)
Dataset.GetLocationsCallback.Server.NextlocationsResultTuple = NamedTuple(
    "NextlocationsResultTuple",
    [("locations", object)],
)
Metadata.Information.Server.ForallResultTuple = NamedTuple(
    "ForallResultTuple",
    [("all", object)],
)
Metadata.Information.Server.ForoneResultTuple = NamedTuple(
    "ForoneResultTuple",
    [("id", object), ("name", object), ("description", object)],
)
Metadata.Supported.Server.CategoriesResultTuple = NamedTuple(
    "CategoriesResultTuple",
    [("types", object)],
)
Metadata.Supported.Server.SupportedvaluesResultTuple = NamedTuple(
    "SupportedvaluesResultTuple",
    [("values", object)],
)
Service.Server.GetavailabledatasetsResultTuple = NamedTuple(
    "GetavailabledatasetsResultTuple",
    [("datasets", object)],
)
Service.Server.GetdatasetsforResultTuple = NamedTuple(
    "GetdatasetsforResultTuple",
    [("datasets", object)],
)
TimeSeries.Server.DataResultTuple = NamedTuple("DataResultTuple", [("data", object)])
TimeSeries.Server.DatatResultTuple = NamedTuple("DatatResultTuple", [("data", object)])
TimeSeries.Server.HeaderResultTuple = NamedTuple(
    "HeaderResultTuple",
    [("header", object)],
)
TimeSeries.Server.LocationResultTuple = NamedTuple(
    "LocationResultTuple",
    [
        ("id", object),
        ("heightNN", object),
        ("latlon", object),
        ("timeSeries", object),
        ("customData", object),
    ],
)
TimeSeries.Server.MetadataResultTuple = NamedTuple(
    "MetadataResultTuple",
    [("entries", object), ("info", object)],
)
TimeSeries.Server.RangeResultTuple = NamedTuple(
    "RangeResultTuple",
    [("startDate", object), ("endDate", object)],
)
TimeSeries.Server.ResolutionResultTuple = NamedTuple(
    "ResolutionResultTuple",
    [("resolution", object)],
)
TimeSeries.Server.SubheaderResultTuple = NamedTuple(
    "SubheaderResultTuple",
    [("timeSeries", object)],
)
TimeSeries.Server.SubrangeResultTuple = NamedTuple(
    "SubrangeResultTuple",
    [("timeSeries", object)],
)
