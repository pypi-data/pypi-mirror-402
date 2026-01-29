# Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of iactsim.
#
# iactsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iactsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Union

from tqdm.auto import tqdm

try:
    import tmm_fast
    _HAS_TMM_FAST = True
except ImportError:
    _HAS_TMM_FAST = False

try:
    import tmm
    _HAS_TMM = True
except ImportError:
    _HAS_TMM = False

from ._air_refractive_index import calculate_ciddor_rindex
from ._surface_misc import SurfaceProperties
from ..visualization._iactsim_style import iactsim_style

class OpticalStackSimulator:
    """
    A class to handle dispersive Transfer Matrix Method (TMM) simulations 
    using the tmm_fast backend, with a dynamic material database.

    Parameters
    ----------
    core_materials : List[str]
        List of material names for the core layers (from top to bottom).
    core_thicknesses : List[float]
        List of thicknesses for the core layers in meters.
    ambient : str, optional
        Name of the ambient medium (default is "Air").
    substrate : str, optional
        Name of the substrate material (default is "SiO2").
    coh_mask : list, optional
        List of coherence tags ('c' for coherent, 'i' for incoherent) for each layer 
        (including ambient and substrate). If empty, coherent simulation is assumed.

    """

    def __init__(
        self, 
        core_materials: List[str], 
        core_thicknesses: List[float],
        ambient: str = "Air", 
        substrate: str = "SiO2",
        coh_list: list = []
    ):
        """
        Initialize the optical stack and load default materials.
        
        Raises
        ------
        ImportError
            If the 'tmm_fast' package is not installed.
        """
        if not _HAS_TMM_FAST and not _HAS_TMM:
            raise ImportError(
                "Neither 'tmm_fast' nor 'tmm' package are installed.\n"
            )

        # Internal database: Maps name -> callable function(wavelength)
        self._material_db: Dict[str, Callable[[np.ndarray], np.ndarray]] = {}
        self._load_default_materials()

        # Set up stack materials thicknesses
        core_materials = list(core_materials)
        self.materials = [ambient] + core_materials + [substrate]

        # Validate materials
        self._validate_materials(self.materials)

        # Set up thicknesses (in meters)
        core_thicknesses_list = list(core_thicknesses)
        self.thicknesses = np.array([0.0] + core_thicknesses_list + [0.0])

        self._wavelengths: Optional[np.ndarray] = None
        self._angles_rad: Optional[np.ndarray] = None

        if len(coh_list) and not _HAS_TMM:
            raise(RuntimeError('tmm package is needed for incoherent simulation.'))
        
        self._coh_list = coh_list

        self.show_progress = True
    
    @property
    def wavelengths(self):
        return self._wavelengths*1e9  # Convert to nm
    
    @property
    def incidence_angles(self):
        return self._angles_rad*180/np.pi  # Convert to degrees

    def get_available_materials(self) -> List[str]:
        """Returns a sorted list of all currently registered material names."""
        return sorted(list(self._material_db.keys()))

    def register_material(self, name: str, n_func: Callable[[np.ndarray], np.ndarray]) -> None:
        """
        Register a custom material using a refractive index function.

        Parameters
        ----------
        name : str
            The name to refer to the material.
        n_func : Callable
            Function accepting 1D wavelengths (m) and returning 1D complex indices.
        """
        self._material_db[name] = n_func

    def register_sellmeier_material(self, name: str, B_coeffs: List[float], C_coeffs: List[float]) -> None:
        """Register a material defined by the Sellmeier equation."""
        def sellmeier_wrapper(lam_meters):
            return self._sellmeier_n(lam_meters, B_coeffs, C_coeffs)
        self.register_material(name, sellmeier_wrapper)

    def register_ciddor_air(
        self, 
        name: str = "Air", 
        p: float = 101325.0, 
        t: float = 288.15, 
        xCO2: float = 450.0, 
        rh: Optional[float] = 0.0
    ) -> None:
        """
        Register the air refractive index using the Ciddor equation.

        Parameters
        ----------
        name : str
            The material name to register (defaults to "Air", overwriting the default vacuum).
        p : float
            Pressure in Pascals (default 101325 Pa).
        t : float
            Temperature in Kelvin (default 288.15 K).
        xCO2 : float
            CO2 concentration in ppm (default 450 ppm).
        rh : float, optional
            Relative humidity (0.0 to 1.0).
        """
        def ciddor_wrapper(lam_meters: np.ndarray) -> np.ndarray:
            # Calculate real index (returns float64)
            n_real = calculate_ciddor_rindex(lam_meters*1e9, p, t, xCO2, rh)
            # Convert to complex128 for TMM compatibility
            return n_real.astype(np.complex128)
        
        self.register_material(name, ciddor_wrapper)

    def set_simulation_params(
        self, 
        wl_range: Union[Tuple[float, float, int], np.ndarray, List[float]] = (200, 1000, 801),
        angle_range: Union[Tuple[float, float, int], np.ndarray, List[float]] = (0, 90, 91)
    ) -> None:
        """
        Set the wavelength (in nanometers) and angle ranges (in degrees).

        Parameters
        ----------
        wl_range : Tuple, List, or np.ndarray
            If tuple: (start_nm, stop_nm, points).
            If array/list: exact wavelengths in Nanometers.
            Default is (200, 1000, 801).
        angle_range : Tuple, List, or np.ndarray
            If tuple: (start_deg, stop_deg, points).
            If array/list: exact angles in Degrees.
            Default is (0, 90, 91).
        """
        if isinstance(wl_range, (list, np.ndarray)):
            wl_nm = np.array(wl_range, dtype=np.float64)
        elif isinstance(wl_range, tuple):
             wl_nm = np.linspace(*wl_range)
        else:
            raise TypeError("wl_range must be a tuple, list, or numpy array.")
        
        # Store internally as meters
        self._wavelengths = wl_nm * 1e-9

        if isinstance(angle_range, (list, np.ndarray)):
            ang_deg = np.array(angle_range, dtype=np.float64)
        elif isinstance(angle_range, tuple):
            ang_deg = np.linspace(*angle_range)
        else:
            raise TypeError("angle_range must be a tuple, list, or numpy array.")

        # Store internally as radians
        self._angles_rad = np.deg2rad(ang_deg)

    def _run(self, polarization: str = 's') -> np.ndarray:
        if self._wavelengths is None or self._angles_rad is None:
            raise ValueError("Simulation parameters not set. Call set_simulation_params() first.")

        # Matrix of refractive indices for all materials and wavelengths
        n_matrix = np.zeros((len(self._wavelengths), len(self.materials)), dtype=np.complex128)
        for i, name in enumerate(self.materials):
            if name not in self._material_db:
                 raise ValueError(f"Material '{name}' not found. Available: {self.get_available_materials()}")
            n_matrix[:, i] = self._material_db[name](self._wavelengths)
        
        # Reshape for tmm_fast broadcasting
        T = self.thicknesses[np.newaxis, :]
        N = n_matrix.T[np.newaxis, :, :]

        if _HAS_TMM_FAST:
            from tmm_fast import coh_tmm
            args = {
                'pol': polarization, 
                'N': N, 
                'T': T,
                'Theta': self._angles_rad,
                'lambda_vacuum': self._wavelengths,
                'device': 'cpu'
            }
        else:
            from tmm import coh_tmm
            args = {
                'pol': polarization, 
                'n_list': N, 
                'd_list': T,
                'th_0': self._angles_rad,
                'lam_vac': self._wavelengths,
            }    
        
        if len(self._coh_list) > 0:
            if not _HAS_TMM:
                raise ImportError("For transfer-matrix-method calculation in the incoherent case tmm package is needed.")
            else:
                from tmm import inc_tmm
                args = {
                    'pol': polarization, 
                    'n_list': N, 
                    'd_list': T,
                    'c_list': self._coh_list,
                    'th_0': self._angles_rad,
                    'lam_vac': self._wavelengths,
                }   
            tmm_func = inc_tmm
        else:
            tmm_func = coh_tmm

        # Run Simulation
        if _HAS_TMM_FAST and len(self._coh_list) == 0:
            if polarization not in ['s', 'p']:
                args['pol'] = 's'
                res_s = tmm_func(**args)
                args['pol'] = 'p'
                res_p = tmm_func(**args)
                # Average results for unpolarized light
                results = {}
                for key in res_s:
                    results[key] = 0.5*(res_s[key] + res_p[key])
            else:
                results = tmm_func(**args)

            # Squeeze results to remove singleton dimensions
            for key in results:
                results[key] = np.squeeze(results[key])
            
            for key in ['R', 'T']:
                results[key] = np.clip(results[key], 0.0, 1.0)
        else:
            d_list = T[0]
            d_list[0] = np.inf
            d_list[-1] = np.inf
            from tmm import inc_tmm

            args = {
                'pol': polarization, 
                'n_list': None, 
                'd_list': T[0],
                'th_0': None,
                'lam_vac': None,
            }
            if len(self._coh_list) > 0:
                args['c_list'] = ['i'] + self._coh_list + ['i']
            
            results = {
                'R': np.empty((len(self._angles_rad), len(self._wavelengths))),
                'T': np.empty((len(self._angles_rad), len(self._wavelengths)))
            }

            with tqdm(total=results['T'].size, disable=not self.show_progress) as pbar:
                for i,ang in enumerate(self._angles_rad):
                    for j,lam in enumerate(self._wavelengths):
                        args['n_list'] = N[0,:,j]
                        args['th_0'] = ang
                        args['lam_vac'] = lam
                        if abs(ang-np.pi/2) < 1e-6:
                            res = {'R':1.0, 'T':0.}
                        else:
                            res = inc_tmm(**args)
                        results['R'][i,j] = res['R']
                        results['T'][i,j] = res['T']
                        pbar.update()
        
        return results
    
    def run(self, polarization: str = 's') -> np.ndarray:
        """Run the TMM simulation for a specific polarization."""
        if polarization in ['s', 'p']:
            results = self._run(polarization)
            if polarization == 'p':
                self._tran_p = results['T']
                self._refl_p = results['R']
                self._tran_s = None
                self._refl_s = None
            else:
                self._tran_s = results['T']
                self._refl_s = results['R']
                self._tran_p = None
                self._refl_p = None
        else:
            self._results_s = self._run('s')
            self._results_p = self._run('p')
            results = {}
            results['T'] = 0.5*(self._results_s['T'] + self._results_p['T'])
            results['R'] = 0.5*(self._results_s['R'] + self._results_p['R'])

            self._tran_s = self._results_s['T']
            self._refl_s = self._results_s['R']
            self._tran_p = self._results_p['T']
            self._refl_p = self._results_p['R']
        
        self.transmittance = results['T']
        self.reflectance = results['R']

        return results


    def _validate_materials(self, materials_list: List[str]) -> None:
        """Check if requested materials exist in the DB."""
        missing = [m for m in materials_list if m not in self._material_db]
        if missing:
            print(f"Warning: Materials {missing} are not yet registered. Please register them.")

    def _load_default_materials(self) -> None:
        """Populates the database with the standard set of materials."""
        defaults = {
            "SiO2":  ([0.6961663, 0.4079426, 0.8974794], [0.0684043**2, 0.1162414**2, 9.896161**2]),
            "MgF2":  ([0.48755108, 0.39875031, 2.3120353], [0.04338408**2, 0.09461442**2, 23.793604**2]),
            "ZrO2":  ([1.347091, 2.117788, 9.452943], [0.062543**2, 0.166739**2, 24.320570**2]),
            "Al2O3": ([1.4313493, 0.65054713, 5.3414021], [0.0726631**2, 0.1193242**2, 18.028251**2]),
            "TiO2":  ([5.913, 0.2441], [0.187**2, 10.0**2]),
            "Y2O3":  ([1.32854, 1.20309, 0.31251], [0.05320**2, 0.11653**2, 12.2425**2]),
            "Si3N4":  ([2.8939], [0.13967**2]), # Philipp 1973
        }
        for name, (B, C) in defaults.items():
            self.register_sellmeier_material(name, B, C)

        self.register_ciddor_air("Air")
        self.register_material("Si", self._get_silicon_n_interp)
        self.register_material("TiO2", self._get_titanium_dioxide_n_interp)
        self.register_material("HfO2", lambda lam: 1.875 + 6.28e-3 * (lam*1e6)**(-2) + 5.80e-4 * (lam*1e6)**(-4)+0.j) # Al-Kuhaili 2004

    @staticmethod
    def _sellmeier_n(lam_meters: np.ndarray, B_coeffs: List[float], C_coeffs: List[float]) -> np.ndarray:
        """Static helper for Sellmeier equation."""
        lam_um = lam_meters * 1e6
        lam_sq = lam_um ** 2
        n_sq = 1.0
        for B, C in zip(B_coeffs, C_coeffs):
            n_sq += (B * lam_sq) / (lam_sq - C)
        return np.sqrt(n_sq + 0j)

    @staticmethod
    def _get_silicon_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """Static helper for Silicon interpolation."""
        # Wavelength
        wl = np.array([
            0.2  , 0.205, 0.21 , 0.215, 0.22 , 0.225, 0.23 , 0.235, 0.24 ,
            0.245, 0.25 , 0.255, 0.26 , 0.265, 0.27 , 0.275, 0.28 , 0.285,
            0.29 , 0.295, 0.3  , 0.305, 0.31 , 0.315, 0.32 , 0.325, 0.33 ,
            0.335, 0.34 , 0.345, 0.35 , 0.355, 0.36 , 0.365, 0.37 , 0.375,
            0.38 , 0.385, 0.39 , 0.395, 0.4  , 0.405, 0.41 , 0.415, 0.42 ,
            0.425, 0.43 , 0.435, 0.44 , 0.445, 0.45 , 0.455, 0.46 , 0.465,
            0.47 , 0.475, 0.48 , 0.485, 0.49 , 0.495, 0.5  , 0.505, 0.51 ,
            0.515, 0.52 , 0.525, 0.53 , 0.535, 0.54 , 0.545, 0.55 , 0.555,
            0.56 , 0.565, 0.57 , 0.575, 0.58 , 0.585, 0.59 , 0.595, 0.6  ,
            0.605, 0.61 , 0.615, 0.62 , 0.625, 0.63 , 0.635, 0.64 , 0.645,
            0.65 , 0.655, 0.66 , 0.665, 0.67 , 0.675, 0.68 , 0.685, 0.69 ,
            0.695, 0.7  , 0.705, 0.71 , 0.715, 0.72 , 0.725, 0.73 , 0.735,
            0.74 , 0.745, 0.75 , 0.755, 0.76 , 0.765, 0.77 , 0.775, 0.78 ,
            0.785, 0.79 , 0.795, 0.8  , 0.805, 0.81 , 0.815, 0.82 , 0.825,
            0.83 , 0.835, 0.84 , 0.845, 0.85 , 0.855, 0.86 , 0.865, 0.87 ,
            0.875, 0.88 , 0.885, 0.89 , 0.895, 0.9  , 0.905, 0.91 , 0.915,
            0.92 , 0.925, 0.93 , 0.935, 0.94 , 0.945, 0.95 , 0.955, 0.96 ,
            0.965, 0.97 , 0.975, 0.98 , 0.985, 0.99 , 0.995
        ])

        # Refractive index
        n = np.array([
            0.99209946, 1.05679451, 1.1247059 , 1.19675741, 1.27722801,
            1.38535671, 1.52747131, 1.62875164, 1.63909853, 1.62707801,
            1.64601992, 1.68801776, 1.74633876, 1.85337491, 2.08212245,
            2.4735713 , 2.9656414 , 3.56649116, 4.35679744, 4.8708617 ,
            5.01330782, 5.02935245, 5.02716921, 5.03689444, 5.06259965,
            5.09984833, 5.1443719 , 5.1951483 , 5.25560353, 5.33514986,
            5.45127151, 5.6517578 , 6.02356285, 6.52374449, 6.87267149,
            6.84601974, 6.55543307, 6.24018864, 5.98412014, 5.77345359,
            5.59501086, 5.44339996, 5.31408555, 5.20228723, 5.10406115,
            5.01639235, 4.93713938, 4.86484232, 4.79848793, 4.73734021,
            4.68082417, 4.6284844 , 4.57990747, 4.53475048, 4.49273461,
            4.45355981, 4.41697064, 4.38276264, 4.35068386, 4.32058236,
            4.29224812, 4.26553028, 4.24029527, 4.21640707, 4.19374113,
            4.17220154, 4.15169579, 4.13214078, 4.11346761, 4.09560382,
            4.07849896, 4.06209996, 4.04635866, 4.03123764, 4.01669679,
            4.00270204, 3.98922182, 3.97623369, 3.96371109, 3.95162474,
            3.93995781, 3.92869179, 3.91779841, 3.90727404, 3.89708879,
            3.8872389 , 3.87769996, 3.86846609, 3.85951807, 3.85084976,
            3.84244663, 3.83429486, 3.82639138, 3.81872234, 3.81127742,
            3.80404653, 3.79702965, 3.79021264, 3.78358765, 3.77714858,
            3.7708897 , 3.76480337, 3.75888499, 3.75312789, 3.7475284 ,
            3.74207895, 3.73677596, 3.73161441, 3.72659027, 3.72169952,
            3.71693645, 3.71229846, 3.70778143, 3.70338166, 3.69909399,
            3.69491721, 3.69084831, 3.686882  , 3.68301396, 3.67924181,
            3.67556356, 3.67197414, 3.66846842, 3.66504525, 3.66170004,
            3.65842781, 3.65522712, 3.65209297, 3.64902105, 3.64601161,
            3.64305773, 3.64015947, 3.63731223, 3.63451505, 3.63176571,
            3.62906222, 3.6264038 , 3.62378843, 3.62121527, 3.61868419,
            3.61619317, 3.61374248, 3.61133135, 3.60895882, 3.60662551,
            3.60432924, 3.60207111, 3.59985025, 3.59766563, 3.59551717,
            3.59340478, 3.5913274 , 3.58928395, 3.58727653, 3.58530219,
            3.58336061, 3.58145128, 3.57957473, 3.57773035, 3.57591637
        ])

        # Extinction coefficient
        k = np.array([
            2.76174038e+00, 2.85497250e+00, 2.95025410e+00, 3.04900630e+00,
            3.15533029e+00, 3.26589236e+00, 3.33478537e+00, 3.33603115e+00,
            3.35632220e+00, 3.45959923e+00, 3.61423292e+00, 3.79597908e+00,
            4.02092953e+00, 4.31690824e+00, 4.66931982e+00, 4.98761361e+00,
            5.19755414e+00, 5.34668177e+00, 5.19238204e+00, 4.63778673e+00,
            4.13187804e+00, 3.79431720e+00, 3.56934176e+00, 3.40894635e+00,
            3.28349133e+00, 3.17817651e+00, 3.08827837e+00, 3.01457274e+00,
            2.96066532e+00, 2.93113414e+00, 2.93162926e+00, 2.96467969e+00,
            2.95110454e+00, 2.68394590e+00, 2.08462042e+00, 1.39478546e+00,
            9.07631653e-01, 6.46454291e-01, 4.96816637e-01, 3.96557465e-01,
            3.27081427e-01, 2.78088325e-01, 2.41746765e-01, 2.12907830e-01,
            1.88834334e-01, 1.68177696e-01, 1.50277447e-01, 1.34765367e-01,
            1.21376009e-01, 1.09872270e-01, 1.00027231e-01, 9.16207929e-02,
            8.44391727e-02, 7.82906582e-02, 7.30095144e-02, 6.84384658e-02,
            6.44439206e-02, 6.09199956e-02, 5.77664822e-02, 5.49133069e-02,
            5.22955975e-02, 4.98668190e-02, 4.75917630e-02, 4.54423676e-02,
            4.33981573e-02, 4.14456985e-02, 3.95754268e-02, 3.77806583e-02,
            3.60576018e-02, 3.44031125e-02, 3.28160307e-02, 3.12951599e-02,
            2.98395382e-02, 2.84485037e-02, 2.71209756e-02, 2.58557972e-02,
            2.46515407e-02, 2.35073960e-02, 2.24216261e-02, 2.13916801e-02,
            2.04163258e-02, 1.94936365e-02, 1.86205006e-02, 1.77964179e-02,
            1.70176287e-02, 1.62834499e-02, 1.55904834e-02, 1.49379030e-02,
            1.43226704e-02, 1.37437559e-02, 1.31988553e-02, 1.26859127e-02,
            1.22040663e-02, 1.17512078e-02, 1.13256362e-02, 1.09259210e-02,
            1.05513014e-02, 1.01999467e-02, 9.87048914e-03, 9.56186861e-03,
            9.27294879e-03, 9.00252875e-03, 8.74962074e-03, 8.51316480e-03,
            8.29219701e-03, 8.08553428e-03, 7.89223338e-03, 7.71129486e-03,
            7.54168421e-03, 7.38234634e-03, 7.23215344e-03, 7.09004509e-03,
            6.95486952e-03, 6.82544146e-03, 6.70056333e-03, 6.57904254e-03,
            6.45961247e-03, 6.34096943e-03, 6.22189307e-03, 6.10120000e-03,
            5.97766049e-03, 5.85026357e-03, 5.71812625e-03, 5.58042611e-03,
            5.43649588e-03, 5.28616827e-03, 5.12911478e-03, 4.96550103e-03,
            4.79580306e-03, 4.62027633e-03, 4.43999933e-03, 4.25562175e-03,
            4.06837980e-03, 3.87926312e-03, 3.68949473e-03, 3.50014637e-03,
            3.31236955e-03, 3.12715383e-03, 2.94538046e-03, 2.76799668e-03,
            2.59545931e-03, 2.42861182e-03, 2.26772687e-03, 2.11313519e-03,
            1.96529982e-03, 1.82406525e-03, 1.68974638e-03, 1.56236018e-03,
            1.44165910e-03, 1.32771436e-03, 1.22044114e-03, 1.11950236e-03,
            1.02470198e-03, 9.36114029e-04, 8.53287408e-04, 7.75963126e-04,
            7.03904686e-04, 6.37026669e-04, 5.75044592e-04, 5.17624701e-04
        ])
        um_lam_array = lam_array * 1e6  # Convert from meters to micrometers
        n_interp = np.interp(um_lam_array, wl, n)
        k_interp = np.interp(um_lam_array, wl, k)
        return n_interp + 1j * k_interp
    
    @staticmethod
    def _get_titanium_dioxide_n_interp(lam_array: np.ndarray) -> np.ndarray:
        """Static helper for Titanium dioxide interpolation (Franta 2015)."""
        # Wavelengths (micrometers)
        wl = np.array([
            0.114114, 0.115436, 0.116772, 0.118124, 0.119492, 0.120876, 0.122276, 
            0.123692, 0.125124, 0.126573, 0.128038, 0.129521, 0.131021, 0.132538, 
            0.134073, 0.135625, 0.137196, 0.138784, 0.140391, 0.142017, 0.143661, 
            0.145325, 0.147008, 0.14871, 0.150432, 0.152174, 0.153936, 0.155718, 
            0.157522, 0.159346, 0.161191, 0.163057, 0.164945, 0.166855, 0.168787, 
            0.170742, 0.172719, 0.174719, 0.176742, 0.178789, 0.180859, 0.182953, 
            0.185072, 0.187215, 0.189383, 0.191575, 0.193794, 0.196038, 0.198308, 
            0.200604, 0.202927, 0.205277, 0.207654, 0.210058, 0.212491, 0.214951, 
            0.21744, 0.219958, 0.222505, 0.225082, 0.227688, 0.230324, 0.232991, 
            0.235689, 0.238418, 0.241179, 0.243972, 0.246797, 0.249655, 0.252546, 
            0.25547, 0.258428, 0.261421, 0.264448, 0.26751, 0.270608, 0.273741, 
            0.276911, 0.280117, 0.283361, 0.286642, 0.289961, 0.293319, 0.296715, 
            0.300151, 0.303627, 0.307142, 0.310699, 0.314297, 0.317936, 0.321618, 
            0.325342, 0.329109, 0.33292, 0.336775, 0.340675, 0.34462, 0.34861, 
            0.352647, 0.35673, 0.360861, 0.36504, 0.369266, 0.373542, 0.377868, 
            0.382243, 0.386669, 0.391147, 0.395676, 0.400258, 0.404893, 0.409581, 
            0.414324, 0.419121, 0.423975, 0.428884, 0.43385, 0.438874, 0.443956, 
            0.449097, 0.454297, 0.459558, 0.464879, 0.470262, 0.475707, 0.481216, 
            0.486788, 0.492425, 0.498127, 0.503895, 0.50973, 0.515632, 0.521603, 
            0.527643, 0.533752, 0.539933, 0.546185, 0.55251, 0.558907, 0.565379, 
            0.571926, 0.578549, 0.585248, 0.592025, 0.59888, 0.605815, 0.61283, 
            0.619926, 0.627104, 0.634366, 0.641712, 0.649142, 0.656659, 0.664263, 
            0.671955, 0.679735, 0.687606, 0.695568, 0.703623, 0.71177, 0.720012, 
            0.72835, 0.736783, 0.745315, 0.753945, 0.762676, 0.771507, 0.780441, 
            0.789478, 0.798619, 0.807867, 0.817222, 0.826685, 0.836257, 0.845941, 
            0.855736, 0.865645, 0.875669, 0.885809, 0.896066, 0.906442, 0.916938, 
            0.927555, 0.938296, 0.949161, 0.960152, 0.97127, 0.982517, 0.993894, 
            1.0054, 1.01704, 1.02882, 1.04073, 1.05279, 1.06498, 1.07731, 1.08978, 
            1.1024, 1.11517, 1.12808, 1.14114, 1.15436, 1.16772, 1.18124, 1.19492, 
            1.20876, 1.22276, 1.23692, 1.25124, 1.26573, 1.28038, 1.29521, 1.31021, 
            1.32538, 1.34073, 1.35625, 1.37196, 1.38784, 1.40391, 1.42017, 1.43661, 
            1.45325, 1.47008, 1.4871, 1.50432, 1.52174, 1.53936, 1.55718, 1.57522, 
            1.59346, 1.61191, 1.63057, 1.64945, 1.66855, 1.68787, 1.70742, 1.72719, 
            1.74719, 1.76742, 1.78789, 1.80859, 1.82953, 1.85072, 1.87215, 1.89383, 
            1.91575, 1.93794, 1.96038, 1.98308
        ])

        # Refractive index
        n = np.asarray([
            0.9542948 , 0.95578109, 0.95842858, 0.96222934, 0.96718989,
            0.97332988, 0.98068133, 0.98928814, 0.99920578, 1.01050088,
            1.0232508 , 1.03754281, 1.05347291, 1.07114393, 1.09066278,
            1.1121365 , 1.13566683, 1.161343  , 1.1892324 , 1.21936917,
            1.25174067, 1.2862725 , 1.32281312, 1.36112004, 1.40084992,
            1.44155587, 1.48269485, 1.52364727, 1.56374929, 1.60233541,
            1.63878644, 1.67257591, 1.70330771, 1.7307393 , 1.75478787,
            1.77552029, 1.79313061, 1.80791029, 1.82021633, 1.83044153,
            1.83898951, 1.84625571, 1.85261423, 1.85841005, 1.86395531,
            1.86952873, 1.87537713, 1.88171824, 1.8887442 , 1.89662531,
            1.90551376, 1.9155472 , 1.92685196, 1.93954594, 1.95374119,
            1.96954604, 1.987067  , 2.00641016, 2.02768234, 2.05099181,
            2.07644855, 2.10416402, 2.13425035, 2.16681874, 2.20197691,
            2.23982538, 2.28045239, 2.32392684, 2.3702893 , 2.41954031,
            2.471626  , 2.52642068, 2.58370672, 2.64315224, 2.70428831,
            2.76648795, 2.82895076, 2.89069816, 2.95058466, 3.00733052,
            3.05957909, 3.10597792, 3.14527734, 3.17643444, 3.1987059 ,
            3.21171358, 3.21547066, 3.21036469, 3.19710272, 3.17663104,
            3.15004456, 3.11850032, 3.08314482, 3.04506065, 3.00523302,
            2.96453402, 2.92372153, 2.88344929, 2.84428705, 2.80675459,
            2.77141028, 2.7389754 , 2.70959666, 2.68301845, 2.65891214,
            2.6369579 , 2.61687011, 2.59840289, 2.58134814, 2.56553096,
            2.55080455, 2.53704542, 2.52414932, 2.51202768, 2.5006049 ,
            2.48981592, 2.47960449, 2.46992159, 2.46072428, 2.4519747 ,
            2.4436393 , 2.43568818, 2.42809459, 2.42083444, 2.41388601,
            2.4072296 , 2.40084727, 2.39472266, 2.3888408 , 2.38318792,
            2.37775138, 2.37251948, 2.36748141, 2.36262715, 2.35794739,
            2.35343348, 2.34907733, 2.34487141, 2.34080866, 2.33688246,
            2.33308663, 2.32941532, 2.32586307, 2.32242471, 2.31909537,
            2.31587046, 2.31274563, 2.30971678, 2.30678   , 2.30393162,
            2.30116812, 2.2984862 , 2.29588267, 2.29335454, 2.29089894,
            2.28851315, 2.28619455, 2.28394067, 2.28174914, 2.27961768,
            2.27754413, 2.27552641, 2.27356254, 2.27165061, 2.2697888 ,
            2.26797535, 2.26620858, 2.26448687, 2.26280868, 2.26117251,
            2.25957692, 2.25802053, 2.25650201, 2.25502007, 2.25357347,
            2.25216103, 2.25078158, 2.24943401, 2.24811725, 2.24683025,
            2.24557202, 2.24434157, 2.24313797, 2.2419603 , 2.24080767,
            2.23967923, 2.23857415, 2.23749162, 2.23643085, 2.23539108,
            2.23437157, 2.23337161, 2.23239048, 2.23142752, 2.23048204,
            2.22955341, 2.228641  , 2.22774418, 2.22686236, 2.22599495,
            2.22514137, 2.22430107, 2.22347349, 2.22265811, 2.22185438,
            2.2210618 , 2.22027986, 2.21950807, 2.21874594, 2.21799298,
            2.21724874, 2.21651274, 2.21578453, 2.21506366, 2.2143497 ,
            2.21364219, 2.21294073, 2.21224487, 2.2115542 , 2.21086831,
            2.21018678, 2.20950921, 2.20883519, 2.20816432, 2.20749621,
            2.20683045, 2.20616667, 2.20550446, 2.20484345, 2.20418324,
            2.20352344, 2.20286368, 2.20220356, 2.20154271, 2.20088074,
            2.20021727, 2.1995519 , 2.19888426, 2.19821396, 2.19754061,
            2.19686382, 2.1961832 , 2.19549835, 2.19480888, 2.19411439,
            2.19341447, 2.19270873, 2.19199674, 2.1912781
        ])

        # Extinction coefficient
        k = np.asarray([
            7.24760280e-001, 7.50886490e-001, 7.77204350e-001, 8.03727290e-001,
            8.30465110e-001, 8.57423570e-001, 8.84603530e-001, 9.11999710e-001,
            9.39599090e-001, 9.67379000e-001, 9.95304770e-001, 1.02332697e+000,
            1.05137825e+000, 1.07936978e+000, 1.10718731e+000, 1.13468707e+000,
            1.16169173e+000, 1.18798671e+000, 1.21331761e+000, 1.23738944e+000,
            1.25986869e+000, 1.28038943e+000, 1.29856475e+000, 1.31400434e+000,
            1.32633861e+000, 1.33524859e+000, 1.34049916e+000, 1.34197178e+000,
            1.33969137e+000, 1.33384180e+000, 1.32476578e+000, 1.31294723e+000,
            1.29897812e+000, 1.28351455e+000, 1.26722930e+000, 1.25076761e+000,
            1.23471195e+000, 1.21955832e+000, 1.20570476e+000, 1.19345010e+000,
            1.18300045e+000, 1.17448050e+000, 1.16794693e+000, 1.16340220e+000,
            1.16080733e+000, 1.16009298e+000, 1.16116861e+000, 1.16392964e+000,
            1.16826291e+000, 1.17405053e+000, 1.18117245e+000, 1.18950805e+000,
            1.19893674e+000, 1.20933803e+000, 1.22059094e+000, 1.23257301e+000,
            1.24515884e+000, 1.25821834e+000, 1.27161456e+000, 1.28520125e+000,
            1.29882001e+000, 1.31229707e+000, 1.32543972e+000, 1.33803233e+000,
            1.34983205e+000, 1.36056422e+000, 1.36991758e+000, 1.37753962e+000,
            1.38303243e+000, 1.38594945e+000, 1.38579422e+000, 1.38202196e+000,
            1.37404562e+000, 1.36124798e+000, 1.34300175e+000, 1.31869939e+000,
            1.28779371e+000, 1.24984898e+000, 1.20460003e+000, 1.15201389e+000,
            1.09234521e+000, 1.02617454e+000, 9.54418280e-001, 8.78301820e-001,
            7.99294360e-001, 7.19011350e-001, 6.39099020e-001, 5.61118990e-001,
            4.86450640e-001, 4.16223470e-001, 3.51284130e-001, 2.92195610e-001,
            2.39261260e-001, 1.92564270e-001, 1.52013690e-001, 1.17390390e-001,
            8.83882600e-002, 6.46485500e-002, 4.57866700e-002, 3.14117900e-002,
            2.11360000e-002, 1.42398700e-002, 9.63155000e-003, 6.54028000e-003,
            4.45884000e-003, 3.05206000e-003, 2.09761000e-003, 1.44753000e-003,
            1.00302000e-003, 6.97860000e-004, 4.87540000e-004, 3.42000000e-004,
            2.40880000e-004, 1.70350000e-004, 1.20960000e-004, 8.62331577e-005,
            6.17205079e-005, 4.43502820e-005, 3.19934333e-005, 2.31690491e-005,
            1.68431512e-005, 1.22911005e-005, 9.00315357e-006, 6.61940432e-006,
            4.88480400e-006, 3.61795111e-006, 2.68935783e-006, 2.00626128e-006,
            1.50197119e-006, 1.12837268e-006, 8.50631127e-007, 6.43439444e-007,
            4.88349222e-007, 3.71866305e-007, 2.84087206e-007, 2.17719511e-007,
            1.67375805e-007, 1.29063077e-007, 9.98122807e-008, 7.74087162e-008,
            6.01951637e-008, 4.69276890e-008, 3.66696953e-008, 2.87138372e-008,
            2.25242936e-008, 1.76939629e-008, 1.39126268e-008, 1.09432028e-008,
            8.60397853e-009, 6.75528170e-009, 5.28945022e-009, 4.12326382e-009,
            3.19221699e-009, 2.44617339e-009, 1.84605923e-009, 1.36134053e-009,
            9.68093255e-010, 6.47522949e-010, 3.84826333e-010, 1.68313498e-010,
            1.52693020e-239, 9.57369220e-234, 4.38062832e-228, 1.47353198e-222,
            3.66982787e-217, 6.81428706e-212, 9.49816903e-207, 1.00044296e-201,
            8.01492780e-197, 4.91494635e-192, 2.32136546e-187, 8.49582595e-183,
            2.42368593e-178, 5.42085653e-174, 9.55949075e-170, 1.33651821e-165,
            1.48946791e-161, 1.33012530e-157, 9.56743308e-154, 5.57089140e-150,
            2.63885160e-146, 1.02176680e-142, 3.24917184e-139, 8.52448791e-136,
            1.85346107e-132, 3.35442625e-129, 5.07491709e-126, 6.44509246e-123,
            6.89907171e-120, 6.24948851e-117, 4.80929840e-114, 3.15612779e-111,
            1.77287101e-108, 8.55512397e-106, 3.55912012e-103, 1.28094712e-100,
            4.00186404e-098, 1.08886108e-095, 2.58860008e-093, 5.39399748e-091,
            9.88209766e-089, 1.59657232e-086, 2.28143097e-084, 2.89170571e-082,
            3.26023408e-080, 3.27856011e-078, 2.94863775e-076, 2.37794026e-074,
            1.72398218e-072, 1.12642512e-070, 6.64920801e-069, 3.55444151e-067,
            1.72471984e-065, 7.61377368e-064, 3.06465232e-062, 1.12721199e-060,
            3.79659784e-059, 1.17340616e-057, 3.33461903e-056, 8.73066157e-055,
            2.11003783e-053, 4.71623189e-052, 9.76703087e-051, 1.87747691e-049,
            3.35579405e-048, 5.58690071e-047, 8.67821846e-046, 1.25975558e-044,
            1.71172379e-043, 2.18048065e-042, 2.60798837e-041, 2.93320376e-040,
            3.10667088e-039, 3.10301056e-038, 2.92691732e-037, 2.61076042e-036,
            2.20510569e-035, 1.76587798e-034, 1.34248934e-033, 9.70101257e-033,
            6.67120163e-032, 4.37103563e-031, 2.73186030e-030, 1.63047981e-029,
            9.30320761e-029, 5.08015296e-028, 2.65768330e-027, 1.33338938e-026,
            6.42203522e-026
       ])
        um_lam_array = lam_array * 1e6  # Convert from meters to micrometers
        n_interp = np.interp(um_lam_array, wl, n)
        k_interp = np.interp(um_lam_array, wl, k)
        return n_interp + 1j * k_interp
    
    @iactsim_style
    def plot_simulation_results(
        self,
        mode: str = 'R',
        cmap: str = "Spectral",
        show_all_pol: bool = True,
    ) -> None:
        """
        Plots simulation results for s-polarization, p-polarization, and unpolarized light.
        Automatically calculates axis extent from the stored simulation parameters.
    
        Parameters
        ----------
        mode : str
            'R' for Reflectance or 'T' for Transmittance. Determines which data key to use.
        cmap : str, optional
            The colormap to use for the plots.
        """
        if self._wavelengths is None or self._angles_rad is None:
            raise ValueError("Simulation parameters are missing. Cannot calculate plot extent.")

        from mpl_toolkits.axes_grid1 import ImageGrid
        import matplotlib.pyplot as plt

        has_p = False
        has_s = False
        if self._tran_p is not None:
            has_p = True
        if self._tran_s is not None:
            has_s = True
        
        if not has_s and not has_p:
            return
        
        data_s = None
        data_p = None
        data = None
        
        if not any([mode.lower().startswith(key) for key in ['t', 'r']]):
            raise ValueError("Invalid mode. Must be 'R' or 'T'.")
        
        if has_s:
            if mode.lower().startswith('t'):
                data_s = self._tran_s
            else:
                data_s = self._refl_s
        
        if has_p:
            if mode.lower().startswith('t'):
                data_p = self._tran_p
            else:
                data_p = self._refl_p
        
        if has_s and has_p:
            data = 0.5 * (data_s + data_p)
        elif has_s:
            data = data_s
        elif has_p:
            data = data_p
        
        if data is None:
            return
        
        if has_p and has_s and show_all_pol:
            plot_data = [
                ("S-polarization", data_s),
                ("P-polarization", data_p),
                ("Unpolarized", data)
            ]
        else:
            title = "S-polarization" if has_s else "P-polarization"
            plot_data = [(title, data)]
        
        xlabel = "Wavelength (nm)"
        ylabel = "Incident angle (°)"
        cbar_label = "Reflectance (%)" if mode.lower().startswith('r') else "Transmittance (%)"

        # Calculate extent
        wl_min_nm = self._wavelengths[0] * 1e9
        wl_max_nm = self._wavelengths[-1] * 1e9
        ang_min_deg = np.rad2deg(self._angles_rad[0])
        ang_max_deg = np.rad2deg(self._angles_rad[-1])
        extent = [wl_min_nm, wl_max_nm, ang_min_deg, ang_max_deg]
        
        # Calculate aspect ratio for figure sizing
        aspect_ratio = (wl_max_nm - wl_min_nm) / (ang_max_deg - ang_min_deg) / 3

        fig = plt.figure(figsize=(len(plot_data)*4*aspect_ratio, 4))  
        
        grid = ImageGrid(
            fig, 111,
            nrows_ncols=(1, len(plot_data)),
            axes_pad=0.5,
            share_all=True,
            cbar_location="right",
            cbar_mode="single",
            cbar_size="5%",
            cbar_pad=0.15,
        )
        
        for ax, (title, data) in zip(grid, plot_data):
            im = ax.imshow(
                data * 100,
                cmap=cmap, 
                aspect=aspect_ratio,
                extent=extent,
                origin='lower',
                vmin=0, vmax=100 
            )
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        
        # Add colorbar
        grid.cbar_axes[0].colorbar(im, label=cbar_label)
        plt.show()

class SipmStackSimulator(OpticalStackSimulator):
    """
    A simulator for calculating the Photon Detection Efficiency (PDE) of Silicon Photomultipliers (SiPMs) given a coating stack.

    This class extends `OpticalStackSimulator` to model the optical transport through thin-film coatings 
    into a Silicon substrate. It calculates the PDE by combining optical transmittance with the 
    probability of electron-hole pair generation within the active depletion region.

    Parameters
    ----------
    layers : list of str
        List of material names for the coating stack (e.g., ``["Si3N4", "SiO2"]``).
    thicknesses : list of float
        List of layer thicknesses in meters.
    medium : str
        The incident medium material name (e.g., ``"Air"``).
    type_layers : list of str
        List of layer types corresponding to `layers`:
        - ``'c'``: Coherent (phase-sensitive, interference calculated).
        - ``'i'``: Incoherent (phase-averaged, intensity addition).
    depletion_layer_depth : float, optional
        Depth of the start of the depletion region ($x_1$) in nm. Default is 5.0 nm.
    depletion_layer_width : float, optional
        Depth extent of the depletion region ($x_2$) in nm. Default is 2100.0 nm.
    fill_factor : float, optional
        Geometric fill factor ($FF$). Default is 1.0.
    breakdown_probability : float, optional
        Avalanche triggering probability ($P_{br}$). Default is 1.0.
    ucell_size : float, optional
        Size of the micro-cell in meters. Default is 75e-6 m.
"""

    def __init__(self, layers: list, thicknesses: list, medium: str, type_layers: list, 
                 depletion_layer_depth: float = 5.0, 
                 depletion_layer_width: float = 2100.0, 
                 fill_factor: float = 1.0,
                 breakdown_probability: float = 1.0,
                 ucell_size = 75e-6):
        # Initialize base class with "Si" hardcoded as the substrate
        super().__init__(layers, thicknesses, medium, "Si", type_layers)
        
        self.depletion_layer_depth = depletion_layer_depth
        self.depletion_layer_width = depletion_layer_width
        self.fill_factor = fill_factor
        self.breakdown_probability = breakdown_probability
        self.ucell_size = ucell_size
        
        # Results
        self.qe = None
        self.pde = None

    def run(self, polarization: str = 'unpolarized') -> np.ndarray:
        """
        Execute the simulation to calculate quantum efficiency and PDE.

        The method performs the following steps:
        1. Calculate optical transmittance into the Silicon substrate.
        2. Calculate the internal path lengths correcting for refraction/incidence angle.
        3. Computes the Silicon absorption coefficient from the complex refractive index.
        4. Computes the probability of photon absorption strictly within the depletion region.
        5. Combines factors: $PDE = T \\times P_{int} \\times FF \\times P_{br}$.

        Parameters
        ----------
        polarization : str, optional
            Polarization mode: ``'s'``, ``'p'``, or ``'unpolarized'`` (default).
            If ``'unpolarized'``, the average of s and p transmittances is used.

        Returns
        -------
        np.ndarray
            The calculated PDE array with shape (n_angles, n_wavelengths).
        """
        super().run(polarization)

        # Silicon refractive index
        n_silicon_complex = self._material_db['Si'](self._wavelengths)
        n_silicon_real = np.real(n_silicon_complex)
        k_silicon = np.imag(n_silicon_complex)
        
        # Internal angle inside Silicon to get the correct path length
        # sin(theta2) = sin(theta1) * n1 / n2
        sin_theta_ext = np.sin(self._angles_rad[:, np.newaxis])
        n_air = np.real(self._material_db['Air'](self._wavelengths))
        sin_theta_si = sin_theta_ext * n_air / n_silicon_real
        sin_theta_si = np.clip(sin_theta_si, 0.0, 1.0)
        
        # Path length inside the Silicon
        cos_theta_si = np.sqrt(1 - sin_theta_si**2)
        cos_theta_si = np.clip(cos_theta_si, 1e-12, 1.0)
        max_thickness_limit = self.ucell_size * 1e9
        xx1 = self.depletion_layer_depth / cos_theta_si
        xx1[xx1 > max_thickness_limit] = max_thickness_limit
        
        # Path length inside the depletion layer
        xx2 = self.depletion_layer_width / cos_theta_si
        xx2[xx2 > max_thickness_limit] = max_thickness_limit

        # alpha = 4 * pi * k / lambda [1/nm]
        alpha = 4. * np.pi * k_silicon / self.wavelengths

        # (fraction absorbed in the non active region) -
        # - (fraction absorbed in the active region)
        interaction_prob = np.exp(-alpha * xx1) - np.exp(-alpha * xx2)

        # Quantum efficiency
        self.qe = self.transmittance * interaction_prob

        # PDE
        self._update_pde()
        
        return self.pde

    def constrain_pde(self, lambda0: float, pde0: float):
        """
        Adjusts the breakdown probability to force the PDE to match a specific value 
        at a specific wavelength (at normal incidence).

        This is useful for calibrating the model against a known experimental data point.
        It modifies ``self.breakdown_probability`` in place.

        Parameters
        ----------
        lambda0 : float
            The target wavelength in nanometers.
        pde0 : float
            The target PDE value (0.0 to 1.0) at that wavelength.
        
        Raises
        ------
        RuntimeError
            If ``run()`` has not been called yet.
        """
        if self.qe is None:
            raise(RuntimeError("Simulation not yet run. Running defaults..."))

        # Extract QE at normal incidence (index 0 assumed to be 0 degrees)
        qe_at_normal = self.qe[0]
        
        # Interpolate QE to the specific target wavelength
        qe0 = np.interp(lambda0, self.wavelengths, qe_at_normal)

        if qe0 <= 1e-9:
            raise(RuntimeError(f"Warning: QE at {lambda0}nm is effectively zero. Cannot constrain."))

        required_breakdown = pde0 / (qe0 * self.fill_factor)
        
        self.breakdown_probability = required_breakdown
        self._update_pde()

    def _update_pde(self):
        """Internal helper to re-compute PDE when factors change."""
        if self.qe is not None:
            self.pde = self.qe * self.fill_factor * self.breakdown_probability

    @iactsim_style
    def plot_pde_normal(self,
            compare_data: tuple = None,
            compare_model: tuple = None
    ) -> None:
        """
        Plots the simulated PDE at normal incidence against optional comparison data.

        Parameters
        ----------
        compare_data : tuple, optional
            Experimental data tuple ``(wavelengths, values, errors)``.
        compare_model : tuple, optional
            External model data tuple ``(wavelengths, values)``.
        """
        if self.pde is None:
            return

        import matplotlib.pyplot as plt

        plt.figure(figsize=(7, 4.5))
        
        plt.plot(self.wavelengths, self.pde[0], 
                 label='Simulated PDE (Stack)', linewidth=2, color='tab:blue')
        
        plt.plot(self.wavelengths, self.qe[0], 
                 label='Optical QE (No FF/Br)', ls=':', color='tab:blue', alpha=0.6)

        if compare_model:
            model_wl, model_val = compare_model
            plt.plot(model_wl, model_val, label='Reference Model', ls='--', color='black')
        
        if compare_data:
            meas_wl, meas_val, meas_std = compare_data
            plt.errorbar(meas_wl, meas_val, yerr=meas_std, 
                         label='Measurement', 
                         ms=5, fmt='o', capsize=3, mfc='none', mec='red', ecolor='red')

        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Efficiency")
        plt.title(f"SiPM PDE simulation\n"
                  f"$x_1={self.depletion_layer_depth:.2f}$ nm, $x_2={self.depletion_layer_width:.2f}$ nm, "
                  f"$FF={self.fill_factor:.3f}$, $P_{{br}}={self.breakdown_probability:.3f}$")
        plt.grid(True, which='both', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

    @iactsim_style
    def plot_pde_results(
        self,
        mode: str = 'R',
        cmap: str = "Spectral"
    ) -> None:
        """
        Plots simulation results for s-polarization, p-polarization, and unpolarized light.
        Automatically calculates axis extent from the stored simulation parameters.
    
        Parameters
        ----------
        mode : str
            'R' for Reflectance or 'T' for Transmittance. Determines which data key to use.
        cmap : str, optional
            The colormap to use for the plots.
        """
        if self.pde is None:
            return

        from mpl_toolkits.axes_grid1 import ImageGrid
        import matplotlib.pyplot as plt
        
        has_p = False
        has_s = False
        if self._tran_p is not None:
            has_p = True
        if self._tran_s is not None:
            has_s = True
        
        if not has_s and not has_p:
            return

        # Calculate extent
        wl_min_nm = self._wavelengths[0] * 1e9
        wl_max_nm = self._wavelengths[-1] * 1e9
        ang_min_deg = np.rad2deg(self._angles_rad[0])
        ang_max_deg = np.rad2deg(self._angles_rad[-1])
        extent = [wl_min_nm, wl_max_nm, ang_min_deg, ang_max_deg]
        
        # Calculate aspect ratio for figure sizing
        aspect_ratio = (wl_max_nm - wl_min_nm) / (ang_max_deg - ang_min_deg) / 3

        fig = plt.figure(figsize=(2*3.5*aspect_ratio, 3.5))  
        
        grid = ImageGrid(
            fig, 111,
            nrows_ncols=(1, 2),
            axes_pad=0.5,
            share_all=True,
            cbar_location="right",
            cbar_mode="each",
            cbar_size="5%",
            cbar_pad=0.15,
        )
        
        if mode.lower().startswith('t'):
            label_ax1 = "Transmittance"
            data_ax1 = self.transmittance
            cbar_label_ax1 = "Transmittance (%)"
        else:
            label_ax1 = "Reflectance"
            data_ax1 = self.reflectance
            cbar_label_ax1 = "Reflectance (%)"
         
        plot_data = [
            (label_ax1, cbar_label_ax1, data_ax1),
            ('PDE', "PDE (%)", self.pde),
        ]

        xlabel = "Wavelength (nm)"
        ylabel = "Incident angle (°)"
        
        for ax, cax, (title, cbar_label, data) in zip(grid, grid.cbar_axes, plot_data):
            im = ax.imshow(
                data * 100,
                cmap=cmap, 
                aspect=aspect_ratio,
                extent=extent,
                origin='lower',
                # vmin=0, vmax=100 
            )
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        
            # Add colorbar to the specific cax (colorbar axis)
            cbar = cax.colorbar(im)
            # Set label on the colorbar axis
            cax.set_ylabel(cbar_label, rotation=-90, va="bottom")
        
        plt.tight_layout()
        plt.show()
    
    def get_surfcace_properties_obj(self, with_reflections=True, side='both'):
        """
        Creates a SurfaceProperties object from the simulation results.

        Parameters
        ----------
        with_reflections : bool, optional
            If True, the surface properties will include the simulated reflectance
            and absorption. The detection efficiency will be defined relative to
            absorbed photons ('absorbed' kind).
            If False, reflectance is set to zero, and detection efficiency is
            defined relative to incident photons ('incident' kind).
            Default is True.
        side : str, optional
            Specifies which side(s) of the surface to populate properties for.
            Options are 'front', 'back', or 'both'.
            Default is 'both'.

        Returns
        -------
        SurfaceProperties
            The populated surface properties object containing wavelength, incidence angle,
            reflectance, absorption, and efficiency data.
        """
        sipm_prop = SurfaceProperties()

        R_in_sipm = self.reflectance

        sipm_prop.wavelength = self.wavelengths
        sipm_prop.incidence_angle = self.incidence_angles
        sipm_prop.efficiency_wavelength = self.wavelengths
        sipm_prop.efficiency_incidence_angle = self.incidence_angles

        if with_reflections:
            # No transmittance since absorption in the photon path is not yet simulated.
            # So every photon not reflected is absorbed.
            if side in ['front', 'both']:
                sipm_prop.transmittance = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance = R_in_sipm
                sipm_prop.absorption = 1. - R_in_sipm
            
            if side in ['back', 'both']:
                sipm_prop.transmittance_back = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance_back = R_in_sipm
                sipm_prop.absorption_back = 1. - R_in_sipm

            # Since the surface reflects, the efficiency must be relative
            # to the number of absorbed photons (1-R).
            sipm_prop.efficiency_kind = 'absorbed'

            # absorption*efficiency = pde -> efficiency = pde / absorption
            absorption = 1. - R_in_sipm
            efficiency = np.zeros_like(absorption)
            efficiency[R_in_sipm<1] = self.pde[R_in_sipm<1] / absorption[R_in_sipm<1]
            efficiency[np.argwhere(self.incidence_angles>90-1e-3)] = 0.
            sipm_prop.efficiency = efficiency
            
        else:
            if side in ['front', 'both']:
                sipm_prop.transmittance = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance = np.zeros_like(R_in_sipm)
            
            if side in ['back', 'both']:
                sipm_prop.transmittance_back = np.zeros_like(R_in_sipm)
                sipm_prop.reflectance_back = np.zeros_like(R_in_sipm)

            sipm_prop.efficiency_kind = 'incident'
            sipm_prop.efficiency = self.pde

        return sipm_prop