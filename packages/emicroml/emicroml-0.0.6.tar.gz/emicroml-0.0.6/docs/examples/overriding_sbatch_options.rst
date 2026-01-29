.. _examples_overriding_sbatch_options_sec:

Overriding ``sbatch`` options for SLURM jobs
============================================

There are numerous Python scripts sharing the basename ``execute_action.py``,
located in different subdirectories of ``<root>/examples``, where ``<root>`` is
the root of the ``emicroml`` repository. Each one of these Python scripts can be
executed to perform one or more "actions". To execute a particular action of a
particular script, one must first change into the directory containing said
script. Then, we need to run the Python script ``./execute_action.py`` via the
terminal command::

  python execute_action.py --action=<action> --use_slurm=<use_slurm>

where ``<action>`` is the string associated with the action of interest, and
``<use_slurm>`` is either ``yes`` or ``no``. If ``<use_slurm>`` equals ``yes``
and a SLURM workload manager is available on the server from which you intend to
run the script, then the action will be performed as one or more SLURM jobs. If
``<use_slurm>`` is equal to ``no``, then the action will be performed locally
without using a SLURM workload manager.

In performing an action as one or more SLURM jobs, a file with the basename
``prepare_and_submit_slurm_job.sh`` is executed as many times as there are SLURM
jobs for said action. This file, among other things, specifies the default
``sbatch`` options for the SLURM jobs of this action. Any line of the form::

  #SBATCH --<option_name>=<option_val>

within the aforementioned file specifies that the ``sbatch`` option
``--<option_name>`` has the default value ``<option_val>``.

To override the default ``sbatch`` options, first, create a file at the file
path ``<root>/overriding_sbatch_options.sh``. Then, for every ``sbatch`` option
``--<option_name>`` with the overriding value ``<overriding_option_val>``,
append said file with the following line::

  #SBATCH --<option_name>=<overriding_option_val>

We can also specify additional ``sbatch`` options that are not specified in the
file with the basename ``prepare_and_submit_slurm_job.sh``. Let
``--<name_of_extra_option>`` be an additional ``sbatch`` option with the
overriding value ``<overriding_val_of_extra_option>``. Then to specify this
additional ``sbatch`` option, simply add the following line to the file at the
file path ``<root>/overriding_sbatch_options.sh``::

  #SBATCH --<name_of_extra_option>=<overriding_val_of_extra_option>

The contents of an example valid file at the file path
``<root>/overriding_sbatch_options.sh`` may look like::

  #SBATCH --job-name=foobar
  #SBATCH --cpus-per-task=8
  #SBATCH --gpus-per-node=a100:1
  #SBATCH --mem=40G
  #SBATCH --time=00-08:59
  #SBATCH --mail-user=matthew.rc.fitzpatrick@gmail.com
  #SBATCH --mail-type=ALL
