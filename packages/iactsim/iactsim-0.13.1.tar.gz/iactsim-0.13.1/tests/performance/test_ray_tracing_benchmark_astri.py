import pytest
import cupy as cp
import iactsim
import numpy as np

@pytest.fixture(scope="module")
def telescope_setup():
    """Initializes the telescope and GPU context."""
    astri = iactsim.models.astri.AstriTelescope()

    m1 = astri.optical_system['M1']

    offsets = np.flip(np.asarray([
        [856.5, 0.0],
        [428.2, 741.4],
        [-428.2, 741.4],
        [-856.5, 0.0],
        [-428.2, -741.4],
        [428.2, -741.4],
        [1280.5, 738.8],
        [0.0, 1478.6],
        [-1280.5, 739.3],
        [-1280.5, -739.3],
        [0.0, -1478.6],
        [1280.5, -739.3],
        [1704.8, 0.0],
        [852.4, 1476.4],
        [-852.4, 1476.4],
        [-1704.8, 0.0],
        [-852.4, -1476.4],
        [852.4, -1476.4],
    ]), axis=1)

    offsets[:,0]*=-1

    for i,offset in enumerate(offsets):
        segment = iactsim.optics.AsphericalSurface(
            conic_constant=m1.conic_constant,
            aspheric_coefficients=m1.aspheric_coefficients,
            half_aperture=846./2., 
            curvature=m1.curvature,
            position=[offset[0], offset[1], m1.sagitta(np.sqrt(offset[0]**2+offset[1]**2))],
            surface_type=iactsim.optics.SurfaceType.REFLECTIVE_FRONT,
            name = f'Mirror{i}',
            aperture_shape=iactsim.optics.ApertureShape.HEXAGONAL
        )
        segment.offset = offset
        astri.optical_system.add_surface(segment, replace=True)
                    
    astri.optical_system.remove_surface('M1')

    astri.optical_system.camera_window_parameters = (240, 8.61, 1.5, 1, 3) 

    astri.optical_system.build_masts()

    astri.cuda_init()

    return astri

def test_ray_tracing_performance_astri(benchmark, telescope_setup):
    telescope = telescope_setup
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.set_target(distance=11000)

    def setup_round_on_axis():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_on_axis, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_off_axis(benchmark, telescope_setup):
    telescope = telescope_setup
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)
    def setup_round_off_axis():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_off_axis, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms(benchmark, telescope_setup):
    telescope = telescope_setup
    telescope.optical_system.build_camera_modules()
    telescope.cuda_init()
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)

    def setup_round_pdms():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms_window(benchmark, telescope_setup):
    telescope = telescope_setup
    telescope.optical_system.build_camera_modules()
    telescope.optical_system.camera_window_parameters = (240, 8.61, 1.5, 1, 3) 
    telescope.cuda_init()
    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)

    def setup_round_pdms_window():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms_window, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms_window_props(benchmark, telescope_setup):
    telescope = telescope_setup

    telescope.optical_system.build_camera_modules()

    telescope.optical_system.camera_window_parameters = (240, 8.61, 1.5, 1, 3) 

    gen = iactsim.optics.FresnelSurfacePropertiesGenerator()
    wls = np.arange(200,1001,1.)
    angls = np.arange(0,91,1.)
    gen.generate(telescope.optical_system['WindowLayer1'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer2'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer3'], wls, angls,inplace=True)
    telescope.cuda_init()

    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)

    def setup_round_pdms_window():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms_window, rounds=100, iterations=1, warmup_rounds=5)

def test_ray_tracing_performance_astri_pdms_props_window_props(benchmark, telescope_setup):
    # SiPM optical properties
    sipm = iactsim.optics.SipmStackSimulator(
        layers=["SiO2", "ZrO2"],
        thicknesses=[3250e-9, 35e-9],
        medium="Air",
        type_layers=['c', 'c'],
        depletion_layer_depth=3.,
        depletion_layer_width=2600,
        fill_factor=0.75
    )
    sipm.set_simulation_params(
        wl_range=np.arange(200,1000,1),
        angle_range=np.arange(0,91,1)
    )
    sipm.run('u')
    sipm.constrain_pde(462, 0.582517*0.97)
    sipm_surface_prop = sipm.get_surfcace_properties_obj()

    telescope = telescope_setup

    telescope.optical_system.build_camera_modules()

    telescope.optical_system.camera_window_parameters = (240, 8.61, 1.5, 1, 3) 

    gen = iactsim.optics.FresnelSurfacePropertiesGenerator()
    wls = np.arange(200,1001,1.)
    angls = np.arange(0,91,1.)
    gen.generate(telescope.optical_system['WindowLayer1'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer2'], wls, angls,inplace=True)
    gen.generate(telescope.optical_system['WindowLayer3'], wls, angls,inplace=True)

    for s in telescope.optical_system:
        if s.name.startswith('PDM'):
            s.properties = sipm_surface_prop

    telescope.cuda_init()

    source = iactsim.optics.sources.Source(telescope)
    source.positions.radial_uniformity = False
    source.positions.random = True
    source.positions.r_max = 2500
    source.directions.altitude += 1
    source.set_target(distance=11000)
    
    def setup_round_pdms_window():
        ps, vs, wls, ts = source.generate(1_000_000)
        cp.cuda.Device().synchronize()
        return ((telescope, ps, vs, wls, ts), {})
    
    def run_trace(telescope, ps, vs, wls, ts):
        telescope.trace_photons(ps, vs, wls, ts)
        cp.cuda.Device().synchronize()
    
    benchmark.pedantic(run_trace, setup=setup_round_pdms_window, rounds=100, iterations=1, warmup_rounds=5)