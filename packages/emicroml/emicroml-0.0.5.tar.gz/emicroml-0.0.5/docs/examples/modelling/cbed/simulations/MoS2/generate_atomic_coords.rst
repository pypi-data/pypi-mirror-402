.. _examples_modelling_cbed_simulations_MoS2_generate_atomic_coords_sec:

Generating the atomic coordinates of a model of MoS\ :sub:`2`
=============================================================

In this example, we perform the "action" of generating the atomic coordinates of
a model of a 5-layer :math:`\text{MoS}_2` thin film.

NOTE: Users are advised to read the remainder of the current page in its
entirety before trying to execute this action.

To execute the action, first we need to change into the directory
``<root>/examples/modelling/cbed/simulations/MoS2/scripts``, where ``<root>`` is
the root of the ``emicroml`` repository. Then, we need to run the Python script
``./execute_action.py`` via the terminal command::

  python execute_action.py --action=<action> --use_slurm=<use_slurm>

where ``<action>`` must be equal to ``generate_atomic_coords``, and
``<use_slurm>`` is either ``yes`` or ``no``. If ``<use_slurm>`` equals ``yes``
and a SLURM workload manager is available on the server from which you intend to
run the script, then the action will be performed as a SLURM job. If
``<use_slurm>`` is equal to ``no``, then the action will be performed locally
without using a SLURM workload manager.

If the action is to be performed locally without using a SLURM workload manager,
then prior to executing the above Python script, a set of Python libraries need
to be installed in the Python environment within which said Python script is to
be executed. See :ref:`this page
<examples_prerequisites_for_execution_without_slurm_sec>` for instructions on
how to do so. If the action is being performed as a SLURM job, then prior to
executing any Python commands that do not belong to Python's standard library, a
customizable sequence of commands are executed that are expected to try to
either activate an existing Python virtual environment, or create then activate
one, in which the Python libraries needed to complete the action successfully
are installed. See :ref:`this page
<examples_prerequisites_for_execution_with_slurm_sec>` for instructions how to
customize the sequence of commands.

We assume that the atoms are subject to room temperature. Furthermore, we assume
that the root-mean-square (RMS) :math:`x`-displacements of the Mo and S atoms
are 0.069 Å and 0.062 Å respectively. These values were taken from
Ref. [Schonfeld1]_.

Upon successful completion of the action, the atomic coordinates of the model of
:math:`\text{MoS}_2` are stored in the file at the file path
``<output_dirname>/atomic_coords.xyz``, where ``<output_dirname>`` is
``<root>/examples/modelling/cbed/simulations/MoS2/data``. Moreover, a subset of
the sample model parameters used to construct the model of :math:`\text{MoS}_2`
are stored in the JSON file at the file path
``<output_dirname>/sample_model_params_subset.json``. The atomic coordinates
file will be formatted as an atomic coordinates file that is accepted by
:mod:`prismatique`: see the description of the parameter
``atomic_coords_filename`` of the class :class:`prismatique.sample.ModelParams`
for a discussion on the correct formatting of such an atomic coordinates file.

In executing the action, multiple scripts are executed. The particular scripts
that are executed depend on the command line arguments of the parent Python
script introduced at the beginning of this page. If ``<use_slurm>`` equals
``yes``, then the following scripts are executed in the order that they appear
directly below:

:download:`<root>/examples/modelling/cbed/simulations/MoS2/scripts/execute_action.py <../../../../../../examples/modelling/cbed/simulations/MoS2/scripts/execute_action.py>`
:download:`<root>/examples/modelling/cbed/simulations/MoS2/scripts/generate_atomic_coords/execute_all_action_steps.py <../../../../../../examples/modelling/cbed/simulations/MoS2/scripts/generate_atomic_coords/execute_all_action_steps.py>`
:download:`<root>/examples/modelling/cbed/simulations/MoS2/scripts/generate_atomic_coords/prepare_and_submit_slurm_job.sh <../../../../../../examples/modelling/cbed/simulations/MoS2/scripts/generate_atomic_coords/prepare_and_submit_slurm_job.sh>`
:download:`<root>/examples/modelling/cbed/simulations/MoS2/scripts/generate_atomic_coords/execute_main_action_steps.py <../../../../../../examples/modelling/cbed/simulations/MoS2/scripts/generate_atomic_coords/execute_main_action_steps.py>`

Otherwise, if ``<use_slurm>`` equals ``no``, then the third script, i.e. the one
with the basename ``prepare_and_submit_slurm_job.sh`` is not executed. See the
contents of the scripts listed above for implementation details. Lastly, if the
action is being performed as a SLURM job, then the default ``sbatch`` options,
which are specified in the file with the basename
``prepare_and_submit_slurm_job.sh``, can be overridden by following the
instructions in :ref:`this page <examples_overriding_sbatch_options_sec>`.
