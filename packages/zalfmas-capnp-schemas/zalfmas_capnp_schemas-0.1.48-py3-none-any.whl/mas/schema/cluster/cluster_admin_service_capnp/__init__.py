"""This is an automatically generated stub for `cluster_admin_service.capnp`."""

import base64
from typing import NamedTuple

import capnp
import schema_capnp
from capnp.lib.capnp import _EnumModule, _InterfaceModule, _StructModule

capnp.remove_import_hook()

# Embedded compiled schemas (base64-encoded)
_SCHEMA_NODES = [
    "EEJQBgb/+tCpbX2ywfMAAR4AAzEVIgERJRcRMWcAAv9jbHVzdGVyLwNjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2EHcG5wUQQBAf99DvLWVl1I9wARAUJ/Q2x1c3RlclEQAQL/LF+Av575xrkAUSgCAUE8Af9s+bDj/qNejABROAIBQUwB/+AreSMQf6m+AFFIAgFBVAH/tUQOJgG2MOEAUVACAUF4AQEMAAARAar/bWFzOjpzY2gBZW1hOjpjbHUPc3RlcgAAAQwAABEBmv9tYXMuc2NoZQFtYS5jbHVzdANlcgAAAQwAABEBQn9jbHVzdGVyAAABDAAAMQHKAf9naXRodWIuYwZvbS96YWxmLXJwbS9tYXNfY2FwbnByb3RvX3NjaGVtYXMvZ2VuL2dvL2NsdXN0ZXIAAQ==",  # cluster/cluster_admin_service.capnp
    "EDFQBgb/fQ7y1lZdSPcAESQB//rQqW19ssHzAAQHAAAzrQGMEDEVYgERKXcAA/9jbHVzdGVyLwRjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1cwd0ZXJRHAEB/74bZZKh97HoABExWv/OM/ZljCckvwARMWL/YEs1KN/GQuwAETFa/3ZHXOqPhEn4ABExQv9kKsy+oksDyQARLar/yLTy3IDwrNYAETFi/74On4+ZWZn9ABExqv9VbnJlZ2lzdAADZXL/QWRtaW5NYXMAB3Rlcv9Vc2VyTWFzdAADZXJ/UnVudGltZf9abXFQaXBlbAFpbmVBZGRyZQ9zc2Vz/1ZhbHVlSG9sAAdkZXL/TW9kZWxJbnMBdGFuY2VGYWMPdG9yeQ==",  # cluster/cluster_admin_service.capnp:Cluster
    "ECJQBgb/vhtlkqH3segAESwD/30O8tZWXUj3AAABM8EBBAIxFboBES0HAAARKUcRVQcAAP9jbHVzdGVyLwVjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5VbnJlP2dpc3RlclABAVEEAwUAAP+jrvepMom34QGPM09x826puxERWgACEQkH/3VucmVnaXN0AANlckABUAEB",  # cluster/cluster_admin_service.capnp:Cluster.Unregister
    "EBdQBgb/o673qTKJt+EAETcBAAAEBwABMRVKAgAE/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlVucmVnaXN0ZXIudW5yZWdpc3RlciRQYXJhbXMAAA==",  # cluster/cluster_admin_service.capnp:Cluster.Unregister.unregister$Params
    "ECdQBgb/jzNPcfNuqbsAUTcBAQAABAcAATEVUgIAARExPwAB/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlVucmVnaXN0ZXIudW5yZWdpc3RlciRSZXN1bHQBc1EEAwQAAAQBAAARDUIAAFEIAwFRFAIBf3N1Y2Nlc3MBAQACAQEAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.Unregister.unregister$Results
    "EDFQBgb/zjP2ZYwnJL8AESwD/30O8tZWXUj3AAABMwgC8wMxFcIBES0HAAARKYcRiRcAAP9jbHVzdGVyLwZjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5BZG1pbk1hc3RlcgBQAQFRCAMFAAD/EOZNb+5UO5QB3uOx4oFPQ+cRMeoAAhExBwEB/47Mpmtlm2agAY8AxKcBzr7UESWCAAIRHQf/cmVnaXN0ZXICTW9kZWxJbnN0YW5jZUZhYw90b3J5QAH/YXZhaWxhYmwBZU1vZGVscwBAAVEEAQH/1UicWcvRr7IAAAA=",  # cluster/cluster_admin_service.capnp:Cluster.AdminMaster
    "EDpQBgb/EOZNb+5UO5QAETgBAAAFAgcAATEV4gIAARE5dwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLkFkbWluTWFzdGVyLnJlZ2lzdGVyTW9kZWxJbnN0YW5jZUZhY3RvcnkkUGFyB2Ftc1EIAwQAAAQBAAARKUoAAFEoAwFRNAIBEQEBFAEBAAARMUoAAFEwAwFRPAIB/2FNb2RlbElkAAAAAQwAAgEMAAH/YUZhY3RvcnkAAAABEf++Dp+PmVmZ/QAAAQERAAE=",  # cluster/cluster_admin_service.capnp:Cluster.AdminMaster.registerModelInstanceFactory$Params
    "EGxQBgb/vg6fj5lZmf0AESwD/30O8tZWXUj3AAABM9QKihAxFQoCETUHAAAxMccBE3UBFwAA/2NsdXN0ZXIvB2NsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5AABQAQFRHAMFAQL/dBLx0mQS+IsBHIRfUdyxaPQR0WIAAhHJBwED/wTi1+Kig12YAZOhDefd9qy8Eb1qAAIRtQcBBP8Ww1fPUYJdiwFcmU0dxlMQqBGp8gACEakHAQX/IXa2mPnDpP4BGTBn9aF5+boRnYoAAhGZBwEB/9h0xPsr6rbkAdrmA+dAWs/jEY1CAAIRgQcAAP/EAcGHRB2kvgEIX27BpLKPyhF1sgACEXEHAQb/fbzizHg/itgB/VwsRvD7zeURZYoAAhFhB/9uZXdJbnN0YQAHbmNlQAH/bmV3SW5zdGEAD25jZXNAAf9uZXdDbG91ZAJWaWFabXFQaXBlbGluZVByH294aWVzQAH/bmV3Q2xvdWQBVmlhUHJveHkAAEABf21vZGVsSWRAAf9yZWdpc3RlcgFNb2RlbElucx90YW5jZUAB/3Jlc3RvcmVTAXR1cmR5UmVmAABAAVEEAQH/1UicWcvRr7IAAAA=",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory
    "EBhQBgb/dBLx0mQS+IsAEUEBAAAEBwABMRWiAgAE/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0luc3RhbmNlJFBhcgdhbXM=",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newInstance$Params
    "EClQBgb/HIRfUdyxaPQAEUEBAAAFAQcAATEVqgIAARE1PwAB/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0luc3RhbmNlJFJlcw91bHRzUQQDBAAABAEAABENSgAAUQwDAVEYAgH/aW5zdGFuY2UAAAABEf/ItPLcgPCs1gAAAQERAAE=",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newInstance$Results
    "EExQBgb/yLTy3IDwrNYAESwD/30O8tZWXUj3AAAAEAEz1AnQCjEVwgERLQcAABEphxHxBxHxD/9jbHVzdGVyLwZjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5WYWx1ZUhvbGRlcgBQAQFRCAMFAAD/T+gBypxWposBbNrxePeJXoERMTIAAEEsAUE8ARFNBwEB/5aIJwqwyGepAcXgO1kYmr3dEUFCEUEfQWQBQXQBEYUHH3ZhbHVlEQEfUQQCAf/ItPLcgPCs1gABAQAAEQEfUQQCAf/ItPLcgPCs1gABAQAAQAF/cmVsZWFzZVEEAQL/8Y0vFxJgucIAUQQCAUEUAQEMAAARAWr/cmVsZWFzZVYAD2FsdWUAABEBH1EEAgH/yLTy3IDwrNYAAQEAABEBH1EEAgH/yLTy3IDwrNYAAQEAAEABUAEBQQQBEQESAVQ=",  # cluster/cluster_admin_service.capnp:Cluster.ValueHolder
    "EBZQBgb/T+gBypxWposAETgBAAAEBxABAAAxFSoCAAT/Y2x1c3Rlci8HY2x1c3Rlcl9hZG1pbl9zZXJ2aWNlLmNhcG5wOkNsdXN0ZXIuVmFsdWVIb2xkZXIudmFsdWUkUGEPcmFtcw==",  # cluster/cluster_admin_service.capnp:Cluster.ValueHolder.value$Params
    "ECZQBgb/bNrxePeJXoEAETgBAAAFAQcQAQAAMRUyAgABES0/AAH/Y2x1c3Rlci8HY2x1c3Rlcl9hZG1pbl9zZXJ2aWNlLmNhcG5wOkNsdXN0ZXIuVmFsdWVIb2xkZXIudmFsdWUkUmUfc3VsdHNRBAMEAAAEAQAAEQ0iAABRCAMBURQCAQd2YWwBEgEB/8i08tyA8KzWAAAAARIAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.ValueHolder.value$Results
    "EBZQBgb/lognCrDIZ6kAETgBAAAEBxABAAAxFToCAAT/Y2x1c3Rlci8HY2x1c3Rlcl9hZG1pbl9zZXJ2aWNlLmNhcG5wOkNsdXN0ZXIuVmFsdWVIb2xkZXIucmVsZWFzZSQ/UGFyYW1z",  # cluster/cluster_admin_service.capnp:Cluster.ValueHolder.release$Params
    "EBZQBgb/xeA7WRiavd0AETgBAAAEBxABAAAxFUICAAT/Y2x1c3Rlci8IY2x1c3Rlcl9hZG1pbl9zZXJ2aWNlLmNhcG5wOkNsdXN0ZXIuVmFsdWVIb2xkZXIucmVsZWFzZSRSZXN1bHRzAA==",  # cluster/cluster_admin_service.capnp:Cluster.ValueHolder.release$Results
    "ECpQBgb/BOLX4qKDXZgAUUEBAQAABAcAATEVqgIAARE1PwAB/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0luc3RhbmNlcyRQYQ9yYW1zUQQDBAAABAEAABENkgAAURADAVEcAgH/bnVtYmVyT2YBSW5zdGFuY2UBcwEDAAIBAwAB",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newInstances$Params
    "EDlQBgb/k6EN5932rLwAEUEBAAAFAQcAATEVsgIAARE1PwAB/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0luc3RhbmNlcyRSZR9zdWx0c1EEAwQAAAQBAAARDVIAAFEMAwFRWAIB/2luc3RhbmNlAAFzARH/yLTy3IDwrNYAAABAAREBH1EEAgH/yLTy3IDwrNYAAAARARdRBAEBAQFQAwEBDgABUAMBARH/yLTy3IDwrNYAAAEBEQAB",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newInstances$Results
    "ECxQBgb/FsNXz1GCXYsAUUEBAQAABAcAATEVMgMAARE9PwAB/2NsdXN0ZXIvC2NsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0Nsb3VkVmlhWm1xUGlwZWxpbmVQcm94aWVzJFAfYXJhbXNRBAMEAAAEAQAAEQ2SAABREAMBURwCAf9udW1iZXJPZgFJbnN0YW5jZQFzAQMAAgEDAAE=",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newCloudViaZmqPipelineProxies$Params
    "EDdQBgb/XJlNHcZTEKgAEUEBAAAFAQcAATEVOgMAARE9PwAB/2NsdXN0ZXIvC2NsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0Nsb3VkVmlhWm1xUGlwZWxpbmVQcm94aWVzJFI/ZXN1bHRzUQQDBAAABAEAABENegAAUQwDAVFIAgH/cHJveHlBZGQAP3Jlc3NlcwER/8i08tyA8KzWAAAAQAERAR9RBAIB/8i08tyA8KzWAAAAEQEXUQQBAQEBUAMBARD/ZCrMvqJLA8kAAAEBEQAB",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newCloudViaZmqPipelineProxies$Results
    "ECtQBgb/IXa2mPnDpP4AUUEBAQAABAcAATEVygIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0Nsb3VkVmlhUHJveHkkUGFyYW1zAABRBAMEAAAEAQAAEQ2SAABREAMBURwCAf9udW1iZXJPZgFJbnN0YW5jZQFzAQMAAgEDAAE=",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newCloudViaProxy$Params
    "EClQBgb/GTBn9aF5+boAEUEBAAAFAQcAATEV0gIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm5ld0Nsb3VkVmlhUHJveHkkUmVzdWx0AXNRBAMEAAAEAQAAEQ0yAABRCAMBURQCAR9wcm94eQER/8i08tyA8KzWAAABAREAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.newCloudViaProxy$Results
    "EBdQBgb/2HTE+yvqtuQAEUEBAAAEBwABMRWCAgAE/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm1vZGVsSWQkUGFyYW1zAA==",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.modelId$Params
    "EChQBgb/2uYD50Baz+MAEUEBAAAFAQcAATEVigIAARE1PwAB/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5Lm1vZGVsSWQkUmVzdWx0cwAAUQQDBAAABAEAABENGgAAUQgDAVEUAgEDaWQBDAACAQwAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.modelId$Results
    "EDxQBgb/xAHBh0QdpL4AEUEBAAAFAgcAATEV8gIAARE5dwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5LnJlZ2lzdGVyTW9kZWxJbnN0YW5jZSRQH2FyYW1zUQgDBAAABAEAABEpSgAAUSgDAVE0AgERAQEUAQEBARExkgAAUTQDAVFAAgH/aW5zdGFuY2UAAAABEgQDAAEBEgAB/3JlZ2lzdHJhAXRpb25Ub2tlAW4BDAACAQwAABEBCgAA",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.registerModelInstance$Params
    "ECpQBgb/CF9uwaSyj8oAEUEBAAAFAQcAATEV+gIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5LnJlZ2lzdGVyTW9kZWxJbnN0YW5jZSRSP2VzdWx0c1EEAwQAAAQBAAARDVoAAFEMAwFRGAIB/3VucmVnaXN0AANlcgER/74bZZKh97HoAAABAREAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.registerModelInstance$Results
    "ECpQBgb/fbzizHg/itgAEUEBAAAFAQcAATEVygIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5LnJlc3RvcmVTdHVyZHlSZWYkUGFyYW1zAABRBAMEAAAEAQAAEQ1SAABRDAMBURgCAf9zdHVyZHlSZQABZgEMAAIBDAAB",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.restoreSturdyRef$Params
    "EClQBgb//VwsRvD7zeUAEUEBAAAFAQcAATEV0gIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLk1vZGVsSW5zdGFuY2VGYWN0b3J5LnJlc3RvcmVTdHVyZHlSZWYkUmVzdWx0AXNRBAMEAAAEAQAAEQ0iAABRCAMBURQCAQdjYXABEf/ItPLcgPCs1gAAAQERAAE=",  # cluster/cluster_admin_service.capnp:Cluster.ModelInstanceFactory.restoreSturdyRef$Results
    "ECpQBgb/3uOx4oFPQ+cAETgBAAAFAQcAATEV6gIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLkFkbWluTWFzdGVyLnJlZ2lzdGVyTW9kZWxJbnN0YW5jZUZhY3RvcnkkUmVzD3VsdHNRBAMEAAAEAQAAEQ1aAABRDAMBURgCAf91bnJlZ2lzdAADZXIBEf++G2WSofex6AAAAQERAAE=",  # cluster/cluster_admin_service.capnp:Cluster.AdminMaster.registerModelInstanceFactory$Results
    "EBdQBgb/jsyma2WbZqAAETgBAAAEBwABMRV6AgAE/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLkFkbWluTWFzdGVyLmF2YWlsYWJsZU1vZGVscyQ/UGFyYW1z",  # cluster/cluster_admin_service.capnp:Cluster.AdminMaster.availableModels$Params
    "ECxQBgb9j8SnAc6+1BE4AQAABQEHAAExFYICAAERMT8AAf9jbHVzdGVyLwljbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5BZG1pbk1hc3Rlci5hdmFpbGFibGVNb2RlbHMkUmVzdWx0cwBRBAMEAAAEAQAAEQ1SAABRDAMBUSgCAf9mYWN0b3JpZQABcwEOAAFQAwEBEf++Dp+PmVmZ/QAAAQEOAAE=",  # cluster/cluster_admin_service.capnp:Cluster.AdminMaster.availableModels$Results
    "ECRQBgb/YEs1KN/GQuwAESwD/30O8tZWXUj3AAABM/cDGwUxFboBES0HAAARKUcRVRcAAP9jbHVzdGVyLwVjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5Vc2VyP01hc3RlclABAVEEAwUAAP9l4OqFwO+AmgHaGwj3++RHsRERggACEQkH/2F2YWlsYWJsAWVNb2RlbHMAQAFRBAEB/9VInFnL0a+yAAAA",  # cluster/cluster_admin_service.capnp:Cluster.UserMaster
    "EBdQBgb/ZeDqhcDvgJoAETcBAAAEBwABMRVyAgAE/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlVzZXJNYXN0ZXIuYXZhaWxhYmxlTW9kZWxzJFAfYXJhbXM=",  # cluster/cluster_admin_service.capnp:Cluster.UserMaster.availableModels$Params
    "ECxQBgb/2hsI9/vkR7EAETcBAAAFAQcAATEVegIAARExPwAB/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlVzZXJNYXN0ZXIuYXZhaWxhYmxlTW9kZWxzJFI/ZXN1bHRzUQQDBAAABAEAABENUgAAUQwDAVEoAgH/ZmFjdG9yaWUAAXMBDgABUAMBARH/vg6fj5lZmf0AAAEBDgAB",  # cluster/cluster_admin_service.capnp:Cluster.UserMaster.availableModels$Results
    "EFRQBgb/dkdc6o+ESfgAESwD/30O8tZWXUj3AAABMx8FggkxFaIBES0HAAAxKUcBExUBFwAA/2NsdXN0ZXIvBWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnQHaW1lUAEBURQDBQAA/4jORnmPimbDAdRLZoh7q9+oEZHqAAIRkQcBAf8a3RoSvqo1/gEpze629bO9kxGFggACEX0HAQL/bHZUUAwsPZsBfw0lmp9YsuYRcXIAAhFpBwED/062iWD/tyTCAcZyITAyrgTwEV2SAAIRWQcBBP/pnREqMAvQtAG7TGLqjN3YvBFNqgACEUkH/3JlZ2lzdGVyAk1vZGVsSW5zdGFuY2VGYWMPdG9yeUAB/2F2YWlsYWJsAWVNb2RlbHMAQAH/bnVtYmVyT2YAH0NvcmVzQAH/ZnJlZU51bWIBZXJPZkNvcmUBc0AB/3Jlc2VydmVOAXVtYmVyT2ZDD29yZXNAAVEEAQH/1UicWcvRr7IAAAA=",  # cluster/cluster_admin_service.capnp:Cluster.Runtime
    "EDlQBgb/iM5GeY+KZsMAETQBAAAFAgcAATEVwgIAARE1dwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUucmVnaXN0ZXJNb2RlbEluc3RhbmNlRmFjdG9yeSRQYXJhbXMAUQgDBAAABAEAABEpSgAAUSgDAVE0AgERAQEUAQEAABExSgAAUTADAVE8AgH/YU1vZGVsSWQAAAABDAACAQwAAf9hRmFjdG9yeQAAAAER/74On4+ZWZn9AAABAREAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.registerModelInstanceFactory$Params
    "ECpQBgb/1EtmiHur36gAETQBAAAFAQcAATEVygIAARE5PwAB/2NsdXN0ZXIvCmNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUucmVnaXN0ZXJNb2RlbEluc3RhbmNlRmFjdG9yeSRSZXN1bHRzAABRBAMEAAAEAQAAEQ1aAABRDAMBURgCAf91bnJlZ2lzdAADZXIBEf++G2WSofex6AAAAQERAAE=",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.registerModelInstanceFactory$Results
    "EBdQBgb/Gt0aEr6qNf4AETQBAAAEBwABMRVaAgAE/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUuYXZhaWxhYmxlTW9kZWxzJFBhcmEDbXM=",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.availableModels$Params
    "ECxQBgb/Kc3utvWzvZMAETQBAAAFAQcAATEVYgIAARExPwAB/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUuYXZhaWxhYmxlTW9kZWxzJFJlc3UHbHRzUQQDBAAABAEAABENUgAAUQwDAVEoAgH/ZmFjdG9yaWUAAXMBDgABUAMBARH/vg6fj5lZmf0AAAEBDgAB",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.availableModels$Results
    "EBdQBgb/bHZUUAwsPZsAETQBAAAEBwABMRVKAgAE/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUubnVtYmVyT2ZDb3JlcyRQYXJhbXMAAA==",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.numberOfCores$Params
    "ECdQBgb/fw0lmp9YsuYAUTQBAQAABAcAATEVUgIAARExPwAB/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUubnVtYmVyT2ZDb3JlcyRSZXN1bHQBc1EEAwQAAAQBAAARDTIAAFEIAwFRFAIBH2NvcmVzAQMAAgEDAAE=",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.numberOfCores$Results
    "EBdQBgb/TraJYP+3JMIAETQBAAAEBwABMRVqAgAE/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUuZnJlZU51bWJlck9mQ29yZXMkUGEPcmFtcw==",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.freeNumberOfCores$Params
    "ECdQBgb/xnIhMDKuBPAAUTQBAQAABAcAATEVcgIAARExPwAB/2NsdXN0ZXIvCGNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUuZnJlZU51bWJlck9mQ29yZXMkUmUfc3VsdHNRBAMEAAAEAQAAEQ0yAABRCAMBURQCAR9jb3JlcwEDAAIBAwAB",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.freeNumberOfCores$Results
    "EDhQBgb/6Z0RKjAL0LQAUTQBAQAABQEHAAExFYICAAERMXcAAf9jbHVzdGVyLwljbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5SdW50aW1lLnJlc2VydmVOdW1iZXJPZkNvcmVzJFBhcmFtcwBRCAMEAAAEAQAAESlqAABRKAMBUTQCAQEBFAEBAAARMUoAAFEwAwFRPAIB/3Jlc2VydmVDAA9vcmVzAQMAAgEDAAH/YU1vZGVsSWQAAAABDAACAQwAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.reserveNumberOfCores$Params
    "EClQBgb/u0xi6ozd2LwAUTQBAQAABAcAATEVigIAARE1PwAB/2NsdXN0ZXIvCWNsdXN0ZXJfYWRtaW5fc2VydmljZS5jYXBucDpDbHVzdGVyLlJ1bnRpbWUucmVzZXJ2ZU51bWJlck9mQ29yZXMkUmVzdWx0cwAAUQQDBAAABAEAABENcgAAUQwDAVEYAgH/cmVzZXJ2ZWQAH0NvcmVzAQMAAgEDAAE=",  # cluster/cluster_admin_service.capnp:Cluster.Runtime.reserveNumberOfCores$Results
    "EDZQBgb/ZCrMvqJLA8kAESwB/30O8tZWXUj3AAUCBwAAM4YJ0AkxFQoCETUHAAARMXcAAf9jbHVzdGVyLwdjbHVzdGVyX2FkbWluX3NlcnZpY2UuY2FwbnA6Q2x1c3Rlci5abXFQaXBlbGluZUFkZHJlc3NlcwAAUAEBUQgDBAAABAEAABEpMgAAUSQDAVEwAgERAQEUAQEAABEtOgAAUSgDAVE0AgEfaW5wdXQBDAACAQwAAT9vdXRwdXQBDAACAQwAAQ==",  # cluster/cluster_admin_service.capnp:Cluster.ZmqPipelineAddresses
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
Cluster = _StructModule(_loader.get(0xF7485D56D6F20E7D).as_struct(), "Cluster")
Cluster.Unregister = _InterfaceModule(
    _loader.get(0xE8B1F7A192651BBE).as_interface(),
    "Unregister",
)
Cluster.AdminMaster = _InterfaceModule(
    _loader.get(0xBF24278C65F633CE).as_interface(),
    "AdminMaster",
)
Cluster.UserMaster = _InterfaceModule(
    _loader.get(0xEC42C6DF28354B60).as_interface(),
    "UserMaster",
)
Cluster.Runtime = _InterfaceModule(
    _loader.get(0xF849848FEA5C4776).as_interface(),
    "Runtime",
)
Cluster.ZmqPipelineAddresses = _StructModule(
    _loader.get(0xC9034BA2BECC2A64).as_struct(),
    "ZmqPipelineAddresses",
)
Cluster.ValueHolder = _InterfaceModule(
    _loader.get(0xD6ACF080DCF2B4C8).as_interface(),
    "ValueHolder",
)
Cluster.ModelInstanceFactory = _InterfaceModule(
    _loader.get(0xFD9959998F9F0EBE).as_interface(),
    "ModelInstanceFactory",
)

Cluster.AdminMaster.Server.AvailablemodelsResultTuple = NamedTuple(
    "AvailablemodelsResultTuple",
    [("factories", object)],
)
Cluster.AdminMaster.Server.RegistermodelinstancefactoryResultTuple = NamedTuple(
    "RegistermodelinstancefactoryResultTuple",
    [("unregister", object)],
)
Cluster.ModelInstanceFactory.Server.ModelidResultTuple = NamedTuple(
    "ModelidResultTuple",
    [("id", object)],
)
Cluster.ModelInstanceFactory.Server.NewcloudviaproxyResultTuple = NamedTuple(
    "NewcloudviaproxyResultTuple",
    [("proxy", object)],
)
Cluster.ModelInstanceFactory.Server.NewcloudviazmqpipelineproxiesResultTuple = (
    NamedTuple("NewcloudviazmqpipelineproxiesResultTuple", [("proxyAddresses", object)])
)
Cluster.ModelInstanceFactory.Server.NewinstanceResultTuple = NamedTuple(
    "NewinstanceResultTuple",
    [("instance", object)],
)
Cluster.ModelInstanceFactory.Server.NewinstancesResultTuple = NamedTuple(
    "NewinstancesResultTuple",
    [("instances", object)],
)
Cluster.ModelInstanceFactory.Server.RegistermodelinstanceResultTuple = NamedTuple(
    "RegistermodelinstanceResultTuple",
    [("unregister", object)],
)
Cluster.ModelInstanceFactory.Server.RestoresturdyrefResultTuple = NamedTuple(
    "RestoresturdyrefResultTuple",
    [("cap", object)],
)
Cluster.Runtime.Server.AvailablemodelsResultTuple = NamedTuple(
    "AvailablemodelsResultTuple",
    [("factories", object)],
)
Cluster.Runtime.Server.FreenumberofcoresResultTuple = NamedTuple(
    "FreenumberofcoresResultTuple",
    [("cores", object)],
)
Cluster.Runtime.Server.NumberofcoresResultTuple = NamedTuple(
    "NumberofcoresResultTuple",
    [("cores", object)],
)
Cluster.Runtime.Server.RegistermodelinstancefactoryResultTuple = NamedTuple(
    "RegistermodelinstancefactoryResultTuple",
    [("unregister", object)],
)
Cluster.Runtime.Server.ReservenumberofcoresResultTuple = NamedTuple(
    "ReservenumberofcoresResultTuple",
    [("reservedCores", object)],
)
Cluster.Unregister.Server.UnregisterResultTuple = NamedTuple(
    "UnregisterResultTuple",
    [("success", object)],
)
Cluster.UserMaster.Server.AvailablemodelsResultTuple = NamedTuple(
    "AvailablemodelsResultTuple",
    [("factories", object)],
)
Cluster.ValueHolder.Server.ValueResultTuple = NamedTuple(
    "ValueResultTuple",
    [("val", object)],
)
