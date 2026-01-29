from niwrap_afni import afni
from niwrap_ants import ants
from niwrap_c3d import c3d
from niwrap_dcm2niix import dcm2niix
from niwrap_fastsurfer import fastsurfer
from niwrap_freesurfer import freesurfer
from niwrap_fsl import fsl
from niwrap_greedy import greedy
from niwrap_mrtrix import mrtrix
from niwrap_mrtrix3tissue import mrtrix3tissue
from niwrap_niftyreg import niftyreg
from niwrap_workbench import workbench
from styxdefs import *  # Reexport styxdefs
from styxdocker import DockerRunner
from styxsingularity import SingularityRunner
from styxgraph import GraphRunner


def use_local(*args, **kwargs):
    """Set the LocalRunner as the global runner."""
    set_global_runner(LocalRunner(*args, **kwargs))


def use_dry(*args, **kwargs):
    """Set the DryRunner as the global runner."""
    set_global_runner(DryRunner(*args, **kwargs))


def use_docker(*args, **kwargs):
    """Set the DockerRunner as the global runner."""
    set_global_runner(DockerRunner(*args, **kwargs))


def use_singularity(*args, **kwargs):
    """Set the SingularityRunner as the global runner."""
    set_global_runner(SingularityRunner(*args, **kwargs))


def use_graph(*args, **kwargs):
    """Set the GraphRunner as the global runner."""
    set_global_runner(GraphRunner(*args, **kwargs))

def execute(params, runner: Runner | None = None):
    stype = params["@type"]
    if (stype.startswith("afni/")): return afni.execute(params, runner)
    if (stype.startswith("ants/")): return ants.execute(params, runner)
    if (stype.startswith("c3d/")): return c3d.execute(params, runner)
    if (stype.startswith("dcm2niix/")): return dcm2niix.execute(params, runner)
    if (stype.startswith("fastsurfer/")): return fastsurfer.execute(params, runner)
    if (stype.startswith("freesurfer/")): return freesurfer.execute(params, runner)
    if (stype.startswith("fsl/")): return fsl.execute(params, runner)
    if (stype.startswith("greedy/")): return greedy.execute(params, runner)
    if (stype.startswith("mrtrix/")): return mrtrix.execute(params, runner)
    if (stype.startswith("mrtrix3tissue/")): return mrtrix3tissue.execute(params, runner)
    if (stype.startswith("niftyreg/")): return niftyreg.execute(params, runner)
    if (stype.startswith("workbench/")): return workbench.execute(params, runner)
    return None
