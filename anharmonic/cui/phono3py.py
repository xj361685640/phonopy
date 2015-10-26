# Copyright (C) 2015 Atsushi Togo
# All rights reserved.
#
# This file is part of phonopy.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name of the phonopy project nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import numpy as np
from phonopy.interface.vasp import read_vasp
from phonopy.harmonic.force_constants import show_drift_force_constants
from phonopy.file_IO import parse_BORN, write_FORCE_SETS, parse_FORCE_SETS
from phonopy.structure.spglib import get_grid_point_from_address
from phonopy.units import VaspToTHz
from anharmonic.phonon3.fc3 import show_drift_fc3
from anharmonic.file_IO import (parse_disp_fc2_yaml, parse_disp_fc3_yaml,
                                parse_FORCES_FC2, parse_FORCES_FC3,
                                write_FORCES_FC3_vasp, write_FORCES_FC2_vasp,
                                write_FORCES_FC2,
                                write_fc2_to_hdf5, read_fc3_from_hdf5,
                                read_fc2_from_hdf5, file_exists)
from anharmonic.cui.settings import Phono3pyConfParser
from anharmonic.phonon3 import (Phono3py, Phono3pyJointDos, Phono3pyIsotope,
                                get_gruneisen_parameters)
from anharmonic.cui.phono3py_argparse import get_parser
from anharmonic.cui.show_log import (print_phono3py, print_version, print_end,
                                     print_error, print_error_message,
                                     show_phono3py_settings,
                                     show_phono3py_cells,
                                     show_phono3py_force_constants_settings)
from anharmonic.cui.triplets_info import write_grid_points, show_num_triplets
from anharmonic.cui.translate_settings import get_phono3py_configurations
from anharmonic.cui.create_supercells import create_phono3py_supercells
from anharmonic.cui.create_force_constants import (create_phono3py_fc3,
                                                   create_phono3py_fc2,
                                                   create_phono3py_phonon_fc2)
phono3py_version = "0.9.14"

# Parse arguments
parser = get_parser()
(options, args) = parser.parse_args()
option_list = parser.option_list

# Log level
log_level = 1
if options.verbose:
    log_level = 2
if options.quiet:
    log_level = 0
if options.log_level is not None:
    log_level=options.log_level

# Input and output filename extension
input_filename = options.input_filename
output_filename = options.output_filename
if options.input_output_filename is not None:
    input_filename = options.input_output_filename
    output_filename = options.input_output_filename

# Title
if log_level:
    print_phono3py()
    print_version(phono3py_version)

#####################
# Create FORCES_FC3 #
#####################
if options.forces_fc3_mode or options.forces_fc3_file_mode:
    if input_filename is None:
        filename = 'disp_fc3.yaml'
    else:
        filename = 'disp_fc3.' + input_filename + '.yaml'
    file_exists(filename, log_level)
    if log_level:
        print("Displacement dataset is read from %s." % filename)
    disp_dataset = parse_disp_fc3_yaml()

    if options.forces_fc3_file_mode:
        file_exists(args[0], log_level)
        filenames = [x.strip() for x in open(args[0])]
    else:
        filenames = args
    write_FORCES_FC3_vasp(filenames, disp_dataset)
    
    if log_level:
        print("FORCES_FC3 has been created.")
        print_end()
    exit(0)

#####################
# Create FORCES_FC2 #
#####################
if options.forces_fc2_mode:
    if input_filename is None:
        filename = 'disp_fc2.yaml'
    else:
        filename = 'disp_fc2.' + input_filename + '.yaml'
    file_exists(filename, log_level)
    if log_level:
        print("Displacement dataset is read from %s." % filename)
    disp_dataset = parse_disp_fc2_yaml()
    write_FORCES_FC2_vasp(args, disp_dataset)

    if log_level:
        print("FORCES_FC2 has been created.")
        print_end()
    exit(0)

if options.force_sets_to_forces_fc2_mode:
    filename = 'FORCE_SETS'
    file_exists(filename, log_level)
    disp_dataset = parse_FORCE_SETS(filename=filename)
    write_FORCES_FC2(disp_dataset)

    if log_level:
        print("FORCES_FC2 has been created from FORCE_SETS.")
        print_end()
    exit(0)
    
#####################################
# Create FORCE_SETS from FORCES_FC* #
#####################################
if options.force_sets_mode:
    if options.phonon_supercell_dimension is not None:
        if input_filename is None:
            filename = 'disp_fc2.yaml'
        else:
            filename = 'disp_fc2.' + input_filename + '.yaml'
        file_exists(filename, log_level)
        disp_dataset = parse_disp_fc2_yaml()
        forces = parse_FORCES_FC2(disp_dataset)
    else:
        if input_filename is None:
            filename = 'disp_fc3.yaml'
        else:
            filename = 'disp_fc3.' + input_filename + '.yaml'
        file_exists(filename, log_level)
        disp_dataset = parse_disp_fc3_yaml()
        forces = parse_FORCES_FC3(disp_dataset)
        
    if log_level:
        print("Displacement dataset is read from %s." % filename)
        
    for force_set, disp1 in zip(forces, disp_dataset['first_atoms']):
        disp1['forces'] = force_set
    write_FORCE_SETS(disp_dataset)
    
    if log_level:
        print("FORCE_SETS has been created.")
        print_end()
    exit(0)
    
##################
# Parse settings #
##################
if len(args) > 0:
    settings = Phono3pyConfParser(filename=args[0],
                                  options=options,
                                  option_list=option_list).get_settings()
else:
    settings = Phono3pyConfParser(options=options,
                                  option_list=option_list).get_settings()
    
#########################################
# Run mode: conductivity/isotope/others #
#########################################
run_mode = None
if settings.get_is_gruneisen():
    run_mode = "gruneisen"
elif settings.get_is_joint_dos():
    run_mode = "jdos"
elif (settings.get_is_isotope() and
      not (settings.get_is_bterta() or settings.get_is_lbte())):
    run_mode = "isotope"
elif settings.get_is_linewidth():
    run_mode = "linewidth"
elif settings.get_is_imag_self_energy():
    run_mode = "imag_self_energy"
elif settings.get_is_frequency_shift():
    run_mode = "frequency_shift"
elif settings.get_is_bterta():
    run_mode = "conductivity-RTA"
elif settings.get_is_lbte():
    run_mode = "conductivity-LBTE"

if log_level:
    print("Run mode: %s" % run_mode)

###################################
# Read crystal structure (POSCAR) #
###################################
if options.cell_poscar is None:
    file_exists('POSCAR', log_level)
    unitcell_filename = 'POSCAR'
else:
    file_exists(options.cell_poscar, log_level)
    unitcell_filename = options.cell_poscar
unitcell = read_vasp(unitcell_filename, settings.get_chemical_symbols())

######################
# Translate settings #
######################
conf = get_phono3py_configurations(settings, options)
primitive_matrix = conf['primitive_matrix']
supercell_matrix = conf['supercell_matrix']
phonon_supercell_matrix = conf['phonon_supercell_matrix']
masses = conf['masses']
mesh = conf['mesh']
mesh_divs = conf['mesh_divs']
coarse_mesh_shifts = conf['coarse_mesh_shifts']
grid_points = conf['grid_points']
band_indices = conf['band_indices']
sigmas = conf['sigmas']
temperature_points = conf['temperature_points']
temperatures = conf['temperatures']
frequency_factor_to_THz = conf['frequency_factor_to_THz']
num_frequency_points = conf['num_frequency_points']
frequency_step = conf['frequency_step']
frequency_scale_factor = conf['frequency_scale_factor']
cutoff_frequency = conf['cutoff_frequency']
tsym_type = conf['tsym_type']

symprec = options.symprec

#################################################
# Create supercells with displacements and exit #
#################################################
if settings.get_create_displacements():
    create_phono3py_supercells(unitcell,
                               supercell_matrix,
                               phonon_supercell_matrix,
                               output_filename,
                               symprec,
                               settings,
                               log_level)

#####################
# Initiate phono3py #
#####################
phono3py = Phono3py(
    unitcell,
    supercell_matrix,
    primitive_matrix=primitive_matrix,
    phonon_supercell_matrix=phonon_supercell_matrix,
    masses=masses,
    mesh=mesh,
    band_indices=band_indices,
    sigmas=sigmas,
    cutoff_frequency=cutoff_frequency,
    frequency_factor_to_THz=frequency_factor_to_THz,
    is_symmetry=True,
    is_nosym=options.is_nosym,
    symmetrize_fc3_q=options.is_symmetrize_fc3_q,
    symprec=symprec,
    log_level=log_level,
    lapack_zheev_uplo=options.uplo)

supercell = phono3py.get_supercell()
primitive = phono3py.get_primitive()
phonon_supercell = phono3py.get_phonon_supercell()
phonon_primitive = phono3py.get_phonon_primitive()
symmetry = phono3py.get_symmetry()

#####################################
# Show supercell and primitive cell #
#####################################
if log_level:
    show_phono3py_cells(symmetry,
                        primitive,
                        supercell,
                        phonon_primitive,
                        phonon_supercell,
                        settings)


#####################################################  
# Write ir-grid points and grid addresses, and exit #
#####################################################
if options.write_grid_points:
    write_grid_points(primitive,
                      mesh,
                      mesh_divs,
                      coarse_mesh_shifts,
                      options,
                      log_level)

##################################################
# Show reduced number of triplets at grid points #
##################################################
if options.show_num_triplets:
    show_num_triplets(primitive,
                      mesh,
                      mesh_divs,
                      grid_points,
                      coarse_mesh_shifts,
                      options,
                      log_level)    

###################
# Force constants #
###################
if log_level:
    show_phono3py_force_constants_settings(options.read_fc2,
                                           options.is_symmetrize_fc2,
                                           options.read_fc3,
                                           options.is_symmetrize_fc3_r,
                                           options.is_symmetrize_fc3_q,
                                           tsym_type,
                                           settings)
        
# fc3
if (settings.get_is_joint_dos() or
    (settings.get_is_isotope() and
     not (settings.get_is_bterta() or settings.get_is_lbte())) or
    settings.get_read_gamma() or
    settings.get_read_amplitude() or
    settings.get_constant_averaged_pp_interaction() is not None):
    pass
else:
    if options.read_fc3: # Read fc3.hdf5
        if input_filename is None:
            filename = 'fc3.hdf5'
        else:
            filename = 'fc3.' + input_filename + '.hdf5'
        file_exists(filename, log_level)
        if log_level:
            print("Reading fc3 from %s" % filename)
        fc3 = read_fc3_from_hdf5(filename=filename)
        phono3py.set_fc3(fc3)
    else: # fc3 from FORCES_THIRD and FORCES_SECOND
        create_phono3py_fc3(phono3py,
                            tsym_type,
                            options.is_symmetrize_fc3_r,
                            options.is_symmetrize_fc2,
                            settings.get_cutoff_fc3_distance(),
                            input_filename,
                            output_filename,
                            log_level)
    if log_level:
        show_drift_fc3(phono3py.get_fc3())

# fc2
if options.read_fc2:
    if input_filename is None:
        filename = 'fc2.hdf5'
    else:
        filename = 'fc2.' + input_filename + '.hdf5'
    file_exists(filename, log_level)
    if log_level:
        print("Reading fc2 from %s" % filename)
    phonon_fc2 = read_fc2_from_hdf5(filename=filename)
    if phonon_fc2.shape[0] != phonon_supercell.get_number_of_atoms():
        print_error_message("Matrix shape of fc2 doesn't agree with supercell.")
        if log_level:
            print_error()
        sys.exit(1)
    
    phono3py.set_fc2(phonon_fc2)
else:
    if log_level:
        print("Solving fc2")
        
    if phonon_supercell_matrix is None:
        if phono3py.get_fc2() is None:
            create_phono3py_fc2(phono3py,
                                tsym_type,
                                options.is_symmetrize_fc2,
                                input_filename,
                                log_level)
    else:
        create_phono3py_phonon_fc2(phono3py,
                                   tsym_type,
                                   options.is_symmetrize_fc2,
                                   input_filename,
                                   log_level)
    if output_filename is None:
        filename = 'fc2.hdf5'
    else:
        filename = 'fc2.' + output_filename + '.hdf5'
    if log_level:
        print("Writing fc2 to %s" % filename)
    write_fc2_to_hdf5(phono3py.get_fc2(), filename=filename)

if log_level:    
    show_drift_force_constants(phono3py.get_fc2(), name='fc2')

if settings.get_is_nac():
    file_exists('BORN', log_level)
    nac_params = parse_BORN(phonon_primitive)
    nac_q_direction = settings.get_nac_q_direction()
else:
    nac_params = None
    nac_q_direction = None

if mesh is None:
    if log_level:
        print_end()
    sys.exit(0)
    
##############################
# Phonon Gruneisen parameter #
##############################
if settings.get_is_gruneisen():
    fc2 = phono3py.get_fc2()
    fc3 = phono3py.get_fc3()
    if len(fc2) != len(fc3):
        print_error_message("Supercells used for fc2 and fc3 have to be same.")
        if log_level:
            print_error()
        sys.exit(1)
    
    band_paths = settings.get_bands()
    qpoints = settings.get_qpoints()
    ion_clamped = settings.get_ion_clamped()

    if (mesh is None and
        band_paths is None and
        qpoints is None):

        print_error_message("An option of --mesh, --band, or --qpoints "
                            "has to be specified.")
        if log_level:
            print_error()
        sys.exit(1)

    if log_level:
        print("------ Phonon Gruneisen parameter ------")
        if mesh is not None:
            print("Mesh sampling: [ %d %d %d ]" % tuple(mesh))
        elif band_paths is not None:
            print("Paths in reciprocal reduced coordinates:")
            for path in band_paths:
                print("[%5.2f %5.2f %5.2f] --> [%5.2f %5.2f %5.2f]" %
                      (tuple(path[0]) + tuple(path[-1])))
        if ion_clamped:
            print("To be calculated with ion clamped.")
            
        sys.stdout.flush()

    gr = get_gruneisen_parameters(fc2,
                                  fc3,
                                  supercell,
                                  primitive,
                                  nac_params=nac_params,
                                  nac_q_direction=nac_q_direction,
                                  ion_clamped=ion_clamped,
                                  factor=VaspToTHz,
                                  symprec=symprec)
    if mesh is not None:
        gr.set_sampling_mesh(mesh, is_gamma_center=True)
    elif band_paths is not None:
        gr.set_band_structure(band_paths)
    elif qpoints is not None:
        gr.set_qpoints(qpoints)
    gr.run()

    if output_filename is None:
        filename = 'gruneisen3.yaml'
    else:
        filename = 'gruneisen3.' + output_filename + '.yaml'
    gr.write_yaml(filename=filename)

    if log_level:
        print_end()
    sys.exit(0)

#################
# Show settings #
#################
if log_level:
    show_phono3py_settings(settings,
                           mesh,
                           mesh_divs,
                           band_indices,
                           sigmas,
                           temperatures,
                           temperature_points,
                           grid_points,
                           cutoff_frequency,
                           frequency_factor_to_THz,
                           frequency_step,
                           num_frequency_points,
                           log_level)
    
#############
# Joint DOS #
#############
if run_mode == "jdos":
    joint_dos = Phono3pyJointDos(
        phonon_supercell,
        phonon_primitive,
        mesh,
        phono3py.get_fc2(),
        nac_params=nac_params,
        nac_q_direction=nac_q_direction,
        sigmas=sigmas,
        cutoff_frequency=cutoff_frequency,
        frequency_step=frequency_step,
        num_frequency_points=num_frequency_points,
        temperatures=temperature_points,
        frequency_factor_to_THz=frequency_factor_to_THz,
        frequency_scale_factor=frequency_scale_factor,
        is_nosym=options.is_nosym,
        symprec=symprec,
        output_filename=output_filename,
        log_level=log_level)
    joint_dos.run(grid_points)
    if log_level:
        print_end()
    sys.exit(0)
    
######################
# Isotope scattering #
######################
if settings.get_is_isotope() and settings.get_mass_variances() is None:
    from phonopy.structure.atoms import isotope_data
    symbols = phonon_primitive.get_chemical_symbols()
    in_database = True
    for s in set(symbols):
        if not s in isotope_data:
            print("%s is not in the list of isotope databese" % s)
            print("(not implemented).")
            print("Use --mass_variances option.")
            in_database = False
    if not in_database:
        if log_level:
            print_end()
        sys.exit(0)

if run_mode == "isotope":
    mass_variances = settings.get_mass_variances()
    if band_indices is not None:
        band_indices = np.hstack(band_indices).astype('intc')
    iso = Phono3pyIsotope(
        mesh,
        phonon_primitive,
        mass_variances=mass_variances,
        band_indices=band_indices,
        sigmas=sigmas,
        frequency_factor_to_THz=frequency_factor_to_THz,
        symprec=symprec,
        cutoff_frequency=settings.get_cutoff_frequency(),
        lapack_zheev_uplo=options.uplo)
    iso.set_dynamical_matrix(phono3py.get_fc2(),
                             phonon_supercell,
                             phonon_primitive,
                             nac_params=nac_params,
                             frequency_scale_factor=frequency_scale_factor)
    iso.run(grid_points)
    if log_level:
        print_end()
    sys.exit(0)
            
#########
# Ph-ph #
#########
ave_pp = settings.get_constant_averaged_pp_interaction()
phono3py.set_phph_interaction(
    nac_params=nac_params,
    nac_q_direction=nac_q_direction,
    constant_averaged_interaction=ave_pp,
    frequency_scale_factor=frequency_scale_factor,
    unit_conversion=options.pp_unit_conversion)

if run_mode == "linewidth":
    if grid_points is None:
        print_error_message("Grid point(s) has to be specified with --gp or "
                            "--ga option.")
        if log_level:
            print_error()
        sys.exit(1)
    phono3py.run_linewidth(
        grid_points,
        temperatures=temperatures,
        run_with_g=settings.get_run_with_g(),
        write_details=settings.get_write_detailed_gamma())
    phono3py.write_linewidth(filename=output_filename)
elif run_mode == "imag_self_energy":
    if not settings.get_run_with_g() and settings.get_scattering_event_class():
        print_error_message("--run_without_g and --scattering_event_class can "
                            "not used together.")
        if log_level:
            print_error()
        sys.exit(1)
    if grid_points is None:
        print_error_message("Grid point(s) has to be specified with --gp or "
                            "--ga option.")
        if log_level:
            print_error()
        sys.exit(1)
    phono3py.run_imag_self_energy(
        grid_points,
        frequency_step=frequency_step,
        num_frequency_points=num_frequency_points,
        temperatures=temperature_points,
        scattering_event_class=settings.get_scattering_event_class(),
        run_with_g=settings.get_run_with_g(),
        write_details=settings.get_write_detailed_gamma())
    phono3py.write_imag_self_energy(filename=output_filename)
elif run_mode == "frequency_shift":
    phono3py.get_frequency_shift(
        grid_points,
        epsilons=sigmas,
        temperatures=temperatures,
        output_filename=output_filename)
elif run_mode == "conductivity-RTA" or run_mode == "conductivity-LBTE":
    phono3py.run_thermal_conductivity(
        is_LBTE=settings.get_is_lbte(),
        temperatures=temperatures,
        sigmas=sigmas,
        is_isotope=settings.get_is_isotope(),
        mass_variances=settings.get_mass_variances(),
        grid_points=grid_points,
        boundary_mfp=settings.get_boundary_mfp(),
        use_averaged_pp_interaction=settings.get_average_pp_interaction(),
        gamma_unit_conversion=options.gamma_unit_conversion,
        mesh_divisors=mesh_divs,
        coarse_mesh_shifts=settings.get_coarse_mesh_shifts(),
        is_reducible_collision_matrix=options.is_reducible_collision_matrix,
        no_kappa_stars=settings.get_no_kappa_stars(),
        gv_delta_q=settings.get_group_velocity_delta_q(),
        run_with_g=settings.get_run_with_g(),
        pinv_cutoff=settings.get_pinv_cutoff(),
        write_gamma=settings.get_write_gamma(),
        read_gamma=settings.get_read_gamma(),
        write_collision=settings.get_write_collision(),
        read_collision=settings.get_read_collision(),
        input_filename=input_filename,
        output_filename=output_filename)
else:
    if log_level:
        print("** None of anharmonic properties were calculated. **")

if log_level:
    print_end()