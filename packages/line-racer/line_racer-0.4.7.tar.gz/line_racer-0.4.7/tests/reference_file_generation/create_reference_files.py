import numpy as np
import line_racer.line_racer as lr
import os
import zarr.storage
from pathlib import Path
import time
import warnings


def create_intensity_correction_reference_files():

    from line_racer.intensity_correction_precalculation import calculate_correction_grid

    os.makedirs("data", exist_ok=True)

    # Define parameters for the correction grid calculation
    gamma_sigma_ratio_minimum = 1e-9
    gamma_sigma_ratio_maximum = 1e6
    sigma_minimum = 1e-6
    sigma_maximum = 1e2
    width_points = 5
    cutoff_minimum = 1
    cutoff_maximum = 5000
    cutoff_points = 5

    # calculate the grid for the Hartmann and cutoff correction
    hartmann = True
    hartmann_cutoff_correction_grid, sigma_grid, gamma_sigma_ratio_grid, cutoff_grid = calculate_correction_grid(
        gamma_sigma_ratio_minimum,
        gamma_sigma_ratio_maximum,
        sigma_minimum, sigma_maximum, width_points,
        cutoff_minimum, cutoff_maximum,
        cutoff_points, hartmann)

    np.savez('data/correction_grid_hartmann_cutoff.npz', sigma_grid=sigma_grid,
             gamma_sigma_ratio_grid=gamma_sigma_ratio_grid,
             cutoff_grid=cutoff_grid, correction_grid=hartmann_cutoff_correction_grid)

    hartmann = False
    cutoff_correction_grid, sigma_grid, gamma_sigma_ratio_grid, cutoff_grid = calculate_correction_grid(
        gamma_sigma_ratio_minimum,
        gamma_sigma_ratio_maximum,
        sigma_minimum, sigma_maximum, width_points,
        cutoff_minimum, cutoff_maximum,
        cutoff_points, hartmann)

    np.savez('data/correction_grid_cutoff.npz', sigma_grid=sigma_grid, gamma_sigma_ratio_grid=gamma_sigma_ratio_grid,
             cutoff_grid=cutoff_grid, correction_grid=cutoff_correction_grid)

    pressures = [1]
    temperatures = [300]

    lorentz_widths = np.zeros(10)
    lorentz_widths += np.logspace(-5, 2, 10)

    doppler_widths = np.zeros(10)
    doppler_widths += np.logspace(-4, 2, 10)

    lorentz_widths, doppler_widths = np.meshgrid(lorentz_widths, doppler_widths)
    lorentz_widths = lorentz_widths.flatten()
    doppler_widths = doppler_widths.flatten()

    intensity_cor_hartmann_test_racer = lr.LineRacer(database="exomol",
                                                     input_folder="/",
                                                     mass=123.0,
                                                     cutoff=100,
                                                     hartmann=True,
                                                     species_isotope_dict={"1H2-16O": 1.0},
                                                     temperatures=temperatures,
                                                     pressures=pressures,
                                                     broadening_type="sharp_burrows",
                                                     )

    intensity_cor_hartmann_test_racer._interpolate_cutoff_correction_cube()
    intensity_corrections_hartmann = (
        intensity_cor_hartmann_test_racer._intensity_correction(lorentz_widths, doppler_widths,
                                                            intensity_cor_hartmann_test_racer.hartmann))

    np.savez('../reference_files/reference_intensity_corrections_hartmann.npz', lorentz_widths=lorentz_widths,
             doppler_widths=doppler_widths, intensity_corrections=intensity_corrections_hartmann)

    intensity_cutoff_test_racer = lr.LineRacer(database="exomol",
                                               input_folder="/",
                                               mass=123.0,
                                               cutoff=25,
                                               hartmann=False,
                                               species_isotope_dict={"1H2-16O": 1.0},
                                               temperatures=temperatures,
                                               pressures=pressures,
                                               broadening_type="sharp_burrows",
                                               )

    intensity_cutoff_test_racer._interpolate_cutoff_correction_cube()
    intensity_corrections_cutoff = (
        intensity_cutoff_test_racer._intensity_correction(lorentz_widths, doppler_widths,
                                                          intensity_cutoff_test_racer.hartmann))

    np.savez('../reference_files/reference_intensity_corrections_cutoff.npz', lorentz_widths=lorentz_widths,
             doppler_widths=doppler_widths, intensity_corrections=intensity_corrections_cutoff)


def create_exomol_read_in_reference_file_generation():
    import numpy as np
    import line_racer.line_racer as lr
    import os
    import zarr.storage
    from pathlib import Path

    # define states file
    upper_state = "           1 14321.54321    211     121      19   e"
    lower_state = "           2 90760.69115    245     122      31   e"

    os.makedirs("exomol_tests/", exist_ok=True)
    with open("exomol_tests/exomol.states", "w") as f:
        f.write(upper_state + "\n")
        f.write(lower_state + "\n")

    # define transition file
    transition = "           2            1 1.2345E-01   187.010999"

    with open("exomol_tests/exomol.trans", "w") as f:
        f.write(transition + "\n")

    # define partition function
    partition1 = "   797.0        295.2217"
    partition2 = "  1800.0        800.0860"

    with open("exomol_tests/exomol.pf", "w") as f:
        f.write(partition1 + "\n")
        f.write(partition2 + "\n")

    temperatures = [797.0, 1800]
    pressures = list(np.logspace(-6, 3, 5))

    # define broadening files
    broadening_1 = "m0        0.0435     0.5100    121"
    broadening_2 = "m0        0.0432     0.5100    122"

    with open("exomol_tests/broadening__air.broad", "w") as f:
        f.write(broadening_1 + "\n")
        f.write(broadening_2 + "\n")

    broadening_1 = "a0        0.0600    0.35   121"
    broadening_2 = "a0        0.0595    0.34   122"

    with open("exomol_tests/broadening__self.broad", "w") as f:
        f.write(broadening_1 + "\n")
        f.write(broadening_2 + "\n")

    # create line racer object
    exomol_test_racer = lr.LineRacer(database="exomol",
                                     input_folder="exomol_tests/",
                                     mass=18.0,
                                     lambda_max=1.0e-4,
                                     lambda_min=1.1e-5,
                                     hartmann=True,
                                     cutoff=10000,
                                     species_isotope_dict={"1H2-16O": 1.0},
                                     temperatures=temperatures,
                                     pressures=pressures,
                                     broadening_type="exomol_table",
                                     broadening_species_dict={"air": 0.5, "self": 0.5},
                                     )

    exomol_test_racer.test_tests = True
    exomol_test_racer.no_intensity_correction = True

    transition_files_list = (
        exomol_test_racer.prepare_opacity_calculation(transition_files_list=['exomol_tests/exomol.trans']))
    final_cross_section_file_name = exomol_test_racer.calculate_opacity(transition_files_list, use_mpi=False)

    with zarr.storage.ZipStore(final_cross_section_file_name, mode='a') as store:
        z = zarr.group(store=store)
        cross_section_exomol = z['cross-sections'][:]
        wavenumbers = z['wavenumbers'][:]

    ref_opacity_filename = Path("../reference_files/reference_exomol_cross_section.zarr.zip")

    if ref_opacity_filename.exists():
        ref_opacity_filename.unlink()

    with zarr.storage.ZipStore(ref_opacity_filename, mode='w') as store:
        root = zarr.group(store=store)

        root.create('xsec',
                    shape=(len(pressures), len(temperatures), len(wavenumbers)),
                    dtype='f8')

        root['xsec'][:] = cross_section_exomol


def create_hitran_read_in_reference_file_generation():
    # define hitran line file
    line = (" 21 1000.004186 1.015E-29 1.989E-06.07660.104 2074.65420.68-.001303       0 1 1 11       0 3 3 01"
            "                    Q 13e     3666632429 9 9 711    27.0   27.0")

    os.makedirs("hitran_tests/", exist_ok=True)
    with open("hitran_tests/hitran.par", "w") as f:
        f.write(line + "\n")

    header = "Molecule MolID IsoID Isotope IsoAbundance     Q(296K)      gj    MolarMass(g)"
    species_info = "CO	5     1     26  9.86544E-01    1.0742E+02    1     27.994915"

    os.makedirs("data/", exist_ok=True)
    with open("data/molparam.txt", "w") as f:
        f.write(header + "\n")
        f.write(species_info + "\n")

    # define partition function
    partition1 = "   295.0        295.2217"
    partition2 = "   297.0        299.2217"
    partition3 = "  1000.0        800.0860"

    with open("hitran_tests/q26.txt", "w") as f:
        f.write(partition1 + "\n")
        f.write(partition2 + "\n")
        f.write(partition3 + "\n")

    temperatures = [296.0, 1000.0]
    pressures = list(np.logspace(-6, 3, 5))

    hitran_test_racer = lr.LineRacer(lambda_min=9.0e-4,
                                     lambda_max=1.1e-3,
                                     database="hitran",
                                     input_folder="hitran_tests/",
                                     species_isotope_dict={"12C-16O": 1.0},
                                     temperatures=temperatures,
                                     pressures=pressures,
                                     broadening_type="hitran_table",
                                     broadening_species_dict={"air": 1.0},
                                     )

    hitran_test_racer.test_tests = True
    hitran_test_racer.no_intensity_correction = True

    transition_files_list = (
        hitran_test_racer.prepare_opacity_calculation(transition_files_list=['hitran_tests/hitran.par']))

    final_cross_section_file_name = hitran_test_racer.calculate_opacity(transition_files_list, use_mpi=False)

    with zarr.storage.ZipStore(final_cross_section_file_name, mode='a') as store:
        z = zarr.group(store=store)
        cross_section_hitran = z['cross-sections'][:]
        wavenumbers = z['wavenumbers'][:]

    ref_opacity_filename = Path("../reference_files/reference_hitran_cross_section.zarr.zip")

    if ref_opacity_filename.exists():
        ref_opacity_filename.unlink()

    with zarr.storage.ZipStore(ref_opacity_filename, mode='w') as store:
        root = zarr.group(store=store)

        root.create('xsec',
                    shape=(len(pressures), len(temperatures), len(wavenumbers)),
                    dtype='f8')

        root['xsec'][:] = cross_section_hitran


def create_many_lines_processing_reference_file():

    import numpy as np
    import os
    import line_racer.line_racer as lr

    rng = np.random.default_rng(12345)

    pressure = 1e-3
    temperature = 1000

    effective_wavenumbers = np.zeros(5000)
    effective_wavenumbers += 1000 + (rng.random(5000) * 4 - 2)

    einstein_a = np.zeros(5000)
    einstein_a += 1e-5 + (rng.random(5000) * 1e-5)

    g_up = np.zeros(5000)
    g_up += 5 + rng.integers(2, size=5000)

    # define partition function
    partition1 = "    999        295.2217"
    partition2 = "   1000        800.0860"

    os.makedirs("many_lines_test/", exist_ok=True)

    with open("many_lines_test/test.pf", "w") as f:
        f.write(partition1 + "\n")
        f.write(partition2 + "\n")

    j_upper = np.zeros(5000)
    j_upper += 3
    j_lower = np.zeros(5000)
    j_lower += 2

    energies_lower_state = np.zeros(5000)
    energies_lower_state += 30000 + (rng.random(5000) * 5000)

    iso_masses = global_iso_ids = line_intensities_t_ref = delta_ref = None

    test_many_lines = lr.LineRacer(lambda_min=8.3e-4,
                                   lambda_max=12.5e-4,
                                   cutoff=100,
                                   resolution=1e6,
                                   database="exomol",
                                   hartmann=False,
                                   input_folder="many_lines_test/",
                                   mass=20,
                                   species_isotope_dict={"12C-16O": 1.0},
                                   temperatures=[temperature],
                                   pressures=[pressure],
                                   broadening_type="constant",
                                   constant_broadening=[0.07, 0.5]
                                   )

    test_many_lines.test_tests = True

    test_many_lines.no_intensity_correction = True
    test_many_lines._construct_fixed_resolution_grid()
    test_many_lines._subgrid_molliere2015_method()

    sig = test_many_lines._calculate_pressure_temperature_point(pressure, temperature,
                                                                effective_wavenumbers, einstein_a, g_up, j_upper,
                                                                j_lower,
                                                                energies_lower_state, iso_masses,
                                                                line_intensities_t_ref, delta_ref,
                                                                global_iso_ids, sampling_boost=1.0,
                                                                coarse_grid_switch=True)

    np.savez('../reference_files/reference_many_lines_processing.npz', sigma=sig)


def create_sampling_method_reference_file():

    import numpy as np
    import os
    import line_racer.line_racer as lr

    rng = np.random.default_rng(12345)

    pressure = 1e-3
    temperature = 1000

    effective_wavenumbers = np.zeros(1000)
    effective_wavenumbers += 15000 + (rng.random(1000) * 2 - 2)

    einstein_a = np.zeros(1000)
    einstein_a += 1e-5 + (rng.random(1000) * 1e-5)

    g_up = np.zeros(1000)
    g_up += 5 + rng.integers(2, size=1000)

    j_upper = np.zeros(1000)
    j_upper += 3
    j_lower = np.zeros(1000)
    j_lower += 2

    # define partition function
    partition1 = "    999        295.2217"
    partition2 = "   1000        800.0860"

    os.makedirs("sampling_method/", exist_ok=True)

    with open("sampling_method/test.pf", "w") as f:
        f.write(partition1 + "\n")
        f.write(partition2 + "\n")

    energies_lower_state = np.zeros(1000)
    energies_lower_state += 30000 + (rng.random(1000) * 5000)

    iso_masses = global_iso_ids = line_intensities_t_ref = delta_ref = None

    test_sampling = lr.LineRacer(lambda_min=0.5e-4,
                                 lambda_max=0.7e-4,
                                 cutoff=100,
                                 resolution=1e6,
                                 database="exomol",
                                 input_folder="sampling_method/",
                                 mass=20,
                                 species_isotope_dict={"12C-16O": 1.0},
                                 temperatures=[temperature],
                                 pressures=[pressure],
                                 broadening_type="constant",
                                 constant_broadening=[0.07, 0.5]
                                 )

    test_sampling.test_tests = True
    test_sampling.no_intensity_correction = True

    test_sampling._construct_fixed_resolution_grid()
    test_sampling._subgrid_molliere2015_method()

    sigma_sampling = test_sampling._calculate_pressure_temperature_point(pressure, temperature, effective_wavenumbers,
                                                                         einstein_a, g_up, j_upper, j_lower,
                                                                         energies_lower_state, iso_masses,
                                                                         line_intensities_t_ref, delta_ref,
                                                                         global_iso_ids, sampling_boost=10.0,
                                                                         coarse_grid_switch=False)

    np.savez('../reference_files/sampling_method_sigma.npz', sigma=sigma_sampling)


if __name__ == '__main__':

    warnings.warn("YOU ARE ABOUT TO (RE)CREATE REFERENCE FILES USED FOR TESTING!", UserWarning)
    time.sleep(2)
    print("Make sure you really want to do this, as existing reference files will be overwritten!")
    time.sleep(2)
    print("DO NOT DO THIS UNLESS YOU KNOW WHAT YOU ARE DOING!")
    time.sleep(1)
    print("....")
    time.sleep(1)
    print("!!!!")
    time.sleep(1)
    print("Please specify which reference files you want to recreate")

    name = input("Options are: 'intensity_corrections', 'exomol_read_in', "
                 "'hitran_read_in', 'many_lines_processing', 'sampling_method': ").strip()

    if name == 'intensity_corrections':

        print("Creating intensity correction reference files...")
        create_intensity_correction_reference_files()

    elif name == 'exomol_read_in':

        print("Creating ExoMol read-in reference files...")
        create_exomol_read_in_reference_file_generation()

    elif name == 'hitran_read_in':

        print("Creating HITRAN read-in reference files...")
        create_hitran_read_in_reference_file_generation()

    elif name == 'many_lines_processing':

        print("Creating many lines processing reference files...")
        create_many_lines_processing_reference_file()

    elif name == 'sampling_method':

        print("Creating sampling method reference files...")
        create_sampling_method_reference_file()

    else:
        print("Unknown option selected. Exiting.")



