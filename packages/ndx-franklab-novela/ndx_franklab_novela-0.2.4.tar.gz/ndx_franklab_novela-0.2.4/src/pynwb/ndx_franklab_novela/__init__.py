from importlib.resources import files
import os
from pynwb import load_namespaces, get_class

import ndx_optogenetics  # noqa: F401

# the above import is needed because the definition of FrankLabOptogeneticsEpochsTable
# depends on the definition of OptogeneticEpochsTable in ndx_optogenetics

# Get path to the namespace.yaml file with the expected location when installed not in editable mode
__location_of_this_file = files(__name__)
__spec_path = __location_of_this_file / "spec" / "ndx-franklab-novela.namespace.yaml"

# If that path does not exist, we are likely running in editable mode. Use the local path instead
if not os.path.exists(__spec_path):
    __spec_path = __location_of_this_file.parent.parent.parent / "spec" / "ndx-franklab-novela.namespace.yaml"

# Load the namespace
load_namespaces(str(__spec_path))

AssociatedFiles = get_class("AssociatedFiles", "ndx-franklab-novela")
CameraDevice = get_class("CameraDevice", "ndx-franklab-novela")
DataAcqDevice = get_class("DataAcqDevice", "ndx-franklab-novela")
FrankLabOptogeneticEpochsTable = get_class("FrankLabOptogeneticEpochsTable", "ndx-franklab-novela")
HeaderDevice = get_class("HeaderDevice", "ndx-franklab-novela")
NwbElectrodeGroup = get_class("NwbElectrodeGroup", "ndx-franklab-novela")
Probe = get_class("Probe", "ndx-franklab-novela")
Shank = get_class("Shank", "ndx-franklab-novela")
ShanksElectrode = get_class("ShanksElectrode", "ndx-franklab-novela")

# define aliases to maintain backward compatibility
Probe.add_shank = Probe.add_shanks
Probe.get_shank = Probe.get_shanks
Shank.add_shanks_electrode = Shank.add_shanks_electrodes
Shank.get_shanks_electrode = Shank.get_shanks_electrodes

# TODO: Add all classes to __all__ to make them accessible at the package level
__all__ = [
    "AssociatedFiles",
    "CameraDevice",
    "DataAcqDevice",
    "FrankLabOptogeneticEpochsTable",
    "HeaderDevice",
    "NwbElectrodeGroup",
    "Probe",
    "Shank",
    "ShanksElectrode",
]

# Remove these functions/modules from the package
del load_namespaces, get_class, files, os, __location_of_this_file, __spec_path
