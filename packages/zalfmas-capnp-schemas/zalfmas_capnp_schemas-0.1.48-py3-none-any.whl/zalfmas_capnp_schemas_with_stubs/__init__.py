"""Shim package to provide backward compatibility for imports from zalfmas_capnp_schemas_with_stubs."""

import os

from mas.schema.climate import climate_capnp
from mas.schema.cluster import cluster_admin_service_capnp
from mas.schema.common import common_capnp, date_capnp
from mas.schema.config import config_capnp
from mas.schema.crop import crop_capnp
from mas.schema.data import field_exp_data_capnp
from mas.schema.fbp import fbp_capnp
from mas.schema.geo import geo_capnp
from mas.schema.grid import grid_capnp
from mas.schema.jobs import jobs_capnp
from mas.schema.management import management_capnp
from mas.schema.model import model_capnp
from mas.schema.model.monica import (
    monica_management_capnp,
    monica_params_capnp,
    monica_state_capnp,
)
from mas.schema.model.weberest import web_berest_data_import_capnp
from mas.schema.model.yieldstat import yieldstat_capnp
from mas.schema.persistence import persistence_capnp
from mas.schema.registry import registry_capnp
from mas.schema.service import service_capnp
from mas.schema.soil import soil_capnp, soil_params_capnp
from mas.schema.storage import storage_capnp

schemas_dir = os.path.abspath("../../../zalfmas_capnp_schemas")

__all__ = [
    "climate_capnp",
    "cluster_admin_service_capnp",
    "common_capnp",
    "config_capnp",
    "crop_capnp",
    "date_capnp",
    "fbp_capnp",
    "field_exp_data_capnp",
    "geo_capnp",
    "grid_capnp",
    "jobs_capnp",
    "management_capnp",
    "model_capnp",
    "monica_management_capnp",
    "monica_params_capnp",
    "monica_state_capnp",
    "persistence_capnp",
    "registry_capnp",
    "service_capnp",
    "soil_capnp",
    "soil_params_capnp",
    "storage_capnp",
    "web_berest_data_import_capnp",
    "yieldstat_capnp",
]
