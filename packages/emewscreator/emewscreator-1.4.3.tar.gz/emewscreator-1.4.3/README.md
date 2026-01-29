# EMEWS Creator

EMEWS Creator is a Python application for creating workflow projects for EMEWS (Extreme-scale Model Exploration with Swift).
The EMEWS framework enables the direct integration of multi-language model exploration (ME) algorithms
while scaling dynamic computational experiments to very large numbers (millions) of models on all major
HPC platforms. EMEWS has been designed for any "black box" application code, such as agent-based and 
microsimulation models or training of machine learning models, that require multiple runs as part of
heuristic model explorations. One of the main goals of EMEWS is to democratize the use of large-scale
computing resources by making them accessible to more researchers in many more science domains.
EMEWS is built on the Swift/T parallel scripting language.

See the [EMEWS Site](https://emews.github.io) for more information.

## Installation

EMEWS Creator can be downloaded and installed from PyPI using pip.

```
pip install emewscreator
```

## Using EMEWS Creator

The following provides an overview of how to use EMEWS Creator to create
workflow projects. For a more comprehensive explanation see the
[EMEWS Tutorial](https://emews.org/emews-tutorial/).

EMEWS Creator is run from the command line.

```
$ emewscreator -h
Usage: emewscreator [OPTIONS] COMMAND [ARGS]...

Options:
  -V, --version          Show the version and exit.
  -o, --output-dir PATH  Directory into which the project template will be
                         generated. Defaults to the current directory

  -m, --model-name TEXT  Name of the model application. Defaults to "model".
  -w, --overwrite        Overwrite existing files
  -h, --help             Show this message and exit.

Commands:
  create_db          create an eqsql database
  create_db_cluster  create the database cluster for an eqsql database
  create_db_tables   create the required tables for an eqsql database
  eqpy               create an eqpy workflow
  eqr                create an eqr workflow
  eqsql              create an eqsql workflow
  init_db            fully initialize an eqsql database, creating the cluster,
                     the db, and the required tables
  sweep              create a sweep workflow
```
The `sweep`, `eqpy`, `eqr`, and `eqsql` commands create a particular type of workflow: a sweep, an eqpy-based workflow, an eqr-based workflow, or an eqsql-based workflow. Each of the commands has its own arguments specific to that
workflow type. Those arguments will be covered in the [Workflow Templates](#workflow_templates) section
below.

The options supplied to `emewscreator` are common to all the workflow types.

*  `--output-dir` - the root directory of the directory structure and files created
by EMEWS Creator. 
* `--model-name` - the name  of the model that will be run during the workflow. 
This will be used in the model execution bash script. Spaces will be replaced by underscores.
* `--overwrite` - if present, EMEWS Creator will overwrite any existing files in the
`output-dir` directory when creating the workflow. By default, existing files will *not* be overwritten. 

These values can also be supplied in a yaml format configuration file. Sample
configuration files can be found [here](https://github.com/emews/emews-project-creator/tree/master/example_cfgs)
in the `example_cfgs` directory in the EMEWS Creator github repository. See the
[Workflow Templates](#workflow_templates) section for more information.

The `init_db` command creates and fully initializes the postgresql database required for
running an esql workflow. The `create_db_cluster`, `create_db`, and `create_db_tables` commands individually
execute the three phases of `init_db` if necessary. For example, an HPC resource may provide
a database, in which case, only the table creation (`create_db_tables`) is required. More
details about and the arguments for these commands will be covered in the [Workflow Templates](#workflow_templates) section below. When executing the database releated commands, no arguments to `emewscreator` are required.

## EMEWS Project Structure ##

Each of the workflow types will create the default EMEWS project structure
in the directory specified by the `-o, --output-dir` argument. 
EMEWS Creator is designed such that multiple workflows can be run in the same directory. 
For example, you can begin with the `sweep` and then create an `eqr` or `eqpy`
workflow in the same output directory. When multiple workflows are created
in the same output directory, it is crucial that the `workflow_name`
configuration template argument is unique to each individual workflow. See
the [Workflow Templates](#workflow_templates) section for more information on the `workflow_name`
argument.

### Directories ###

Given an `--output-dir` argument of `my_emews_project`, the default directory structure 
produced by all the workflow types is:

```
my_emews_project/
  data/
  etc/
  ext/
  python/
    test/
  R/
    test/
  scripts/
  swift/
    cfgs/
  README.md
```

The directories are intended to contain the following:

 * `data` - date required by the model and algorithm (inputs, etc.).
 * `etc` - additional code used by EMEWS
 * `ext` - Swift/T extensions, including the default EMEWS utility code extension as well as
 the EQ/R and EQ/Py extensions
 * `python` - Python code (e.g., model exploration algorithms written in Python)
 * `python\test` - tests of the Python code
 * `R` - R code (e.g., model exploration algorithms written R)
 * `R\test` - tests of the R code
 * `scripts` - any necessary scripts (e.g., scripts to launch a model), excluding scripts used to run the workflow
 * `swift` - Swift/T code and scripts used to submit and run the workflow

 ### Files ###

Each of the workflow types will generate the following files. The file names
are derived from parameters specified in the workflow template configuration
arguments. The names of those parameters are included in curly brackets
in the file names below.

* `swift/run_{workflow_name}.sh` - a bash script used to launch the workflow
* `swift/{workflow_name}.swift` - the swift script that implements the workflow.
* `scripts/run_{model_name}_{workflow_name}.sh` - a bash script used to run the model application.
* `swift/cfgs/{workflow_name}.cfg` - a configuration file for running the workflow

These files may require some user customization before they can be used. The 
relevant sections are marked with `TODO`.

Once any edits have been completed, the workflows can be run with:

```
$ run_{workflow_name}.sh <experiment_name> cfgs/{workflow_name}.cfg
```

## Workflow Templates ##

Each workflow template has its own set of command line arguments, but all have the following
in common:

* `-n, --workflow-name` - the name of the workflow. This will be used as the file name for the workflow configuration, submission, and swift script files. Spaces will be replaced by underscores. 
**The `workflow_name` should be unique among all the workflows in the output directory.**
* `-c, --config` - path to the workflow template configuration file, optional if all
the required arguments are specified on the command line

The workflow template configuration file can be used to specify any of a
workflow template's configuration parameters when those parameters are
not specified on the command line. This file is in yaml format.
Sample configuration files can be found 
[here](https://github.com/emews/emews-project-creator/tree/master/example_cfgs)
in the `example_cfgs` directory in the EMEWS Creator github repository. Arguments
supplied on the command line will override those supplied in a configuration file.
If any required arguments are missing from the command line, then the
configuration file is required to supply the missing arguments.

### Sweep ###
The sweep command creates a sweep workflow in which EMEWS reads an input file,
and runs an application using each line of the input file as input to an application run.

Usage:
```
$ emewscreator sweep -h
Usage: emewscreator sweep [OPTIONS]

Options:
  -c, --config PATH         Path to the template configuration file
                            [required if any command line arguments are
                            missing]

  -n, --workflow-name TEXT  Name of the workflow
  -h, --help                Show this message and exit.
```

A sample sweep configuration file can be found [here](https://github.com/emews/emews-project-creator/blob/master/example_cfgs/sweep.yaml).

For a more thorough explanation of the sweep workflow, see the [EMEWS Tutorial](https://www.mcs.anl.gov/~emews/tutorial/).

### EQPy ###

The EQPy workflow template creates a workflow that uses EMEWS Queues for Python (EQPy) to 
run an application using input parameters provided by a
Python model exploration (ME) algorithm. The workflow will start the Python ME
which then iteratively provides json format input parameters for model
execution.

Usage:

```
$ emewscreator eqpy -h

Usage: emewscreator eqpy [OPTIONS]

Options:
  -c, --config PATH              Path to the template configuration file
                                 [required if any command line arguments are
                                 missing]

  -n, --workflow-name TEXT       Name of the workflow
  --module-name TEXT             Python model exploration algorithm module
                                 name

  --me-cfg-file PATH             Configuration file for the model exploration
                                 algorithm

  --trials INTEGER               Number of trials / replicates to perform for
                                 each model run. Defaults to 1

  --model-output-file-name TEXT  Model output base file name, file name only
                                 (e.g., "output.csv")

  --eqpy-dir PATH                Directory where the eqpy extension is
                                 located. If the extension does not exist at
                                 this location it will be installed there.
                                 Defaults to {output_dir}/ext/EQ-Py

  -h, --help                     Show this message and exit.
```

In addition to the common configuration arguments described [above](#workflow_templates),
the eqpy template also has the following:

* `--module-name` - the Python module implementing the ME algorithm
* `--me-cfg-file` - the path to a configuration file for the Python ME algorithm. This
path will be passed to the Python ME when it is initialized. This is relative to the
directory specified in `--output-dir`.
* `--trials` - the number of trials or replicates to perform for each model run. Defaults to 1.
* `model-output-file-name` - each model run is passed a file path for writing its output.
This is the name of that file.

In addition to the default set of files described in the
[EMEWS Project Structure](#emews-project-structure) section, the eqpy workflow template will also
install the EQPy EMEWS Swift-t extension. By default, the extension will be installed in
in `ext/EQ-Py`. An alternative location can be specified with the `--eqpy-dir`
configuration parameter.

* `--eqpy-dir` - specifies the location of the eqpy extension (defaults to `ext/EQ-Py`)

You can set this to use an existing EQ-Py extension, or if the specified location
doesn't exist, the extension will be installed there.

The extension consists of the following files.

* `eqpy.py`
* `EQPy.swift`

These should not be edited by the user.

A sample `eqpy` configuration file can be found [here](https://github.com/emews/emews-project-creator/blob/master/example_cfgs/eqpy.yaml).

For a more thorough explanation of Python-based ME workflows, see the [EMEWS Tutorial](https://www.mcs.anl.gov/~emews/tutorial/).

### EQR ###

The EQR template creates a workflow that uses EMEWS Queues for R (EQR) to 
run an application using input parameters provided by a
R model exploration (ME) algorithm. The workflow will start the R ME
which then iteratively provides json format input parameters for model
execution.

*Note*: The EQR extension typically requires an additional compilation step.Once the template has been run,
see `{eqr_dir}/src/README.md` for compilation instructions.

Usage:

```
$ emewscreator eqr -h
Usage: emewscreator eqr [OPTIONS]

Options:
  -c, --config PATH              Path to the template configuration file
                                 [required if any command line arguments are
                                 missing]

  -n, --workflow-name TEXT       Name of the workflow
  --script-file TEXT             Path to the R model exploration algorithm
  --me-cfg-file PATH             Configuration file for the model exploration
                                 algorithm

  --trials INTEGER               Number of trials / replicates to perform for
                                 each model run

  --model-output-file-name TEXT  Model output base file name, file name only
                                 (e.g., "output.csv")

  --eqr-dir PATH                 Directory where the eqr extension is located.
                                 If the extension does not exist at this
                                 location it will be installed there. Defaults
                                 to {output_dir}/ext/EQ-R

  -h, --help                     Show this message and exit.

```

In addition to the common configuration parameters described [above](#workflow_templates),
the `eqr` template also has the following:

* `--script-file` - the path to the R script implementing the ME algorithm
* `--me-cfg-file` - the path to a configuration file for the R ME algorithm. This
path will be passed to the R ME when it is initialized. This path is relative
to the directory specified by `--output-dir`.
* `--trials` - the number of trials or replicates to perform for each model run
* `--model_output_file_name` - each model run is passed a file path for writing its output.
This is the name of that file.

In addition to the default set of files described in the
[EMEWS Project Structure](#emews-project-structure) section, the eqr workflow template will also
install the source for the EQ/R EMEWS Swift-t extension. By default, the extension will typically be installed 
in `ext/EQ-R`. If EMEWS Creator has been installed as part of a binary install using
the EMEWS installer, the default location will reflect that.
An alternative location can be specified with the `--eqr-dir` configuration argument.

* `--eqr-dir` - specifies the location of the eqr extension (defaults to `ext/EQ-R`).

You can set this to use an existing EQ-R extension, or if the specified location
doesn't exist, the extension will be installed there. 

The extension typically needs to be compiled before it can be used. See `{eqr_dir}/src/README.md` for compilation instructions. If EMEWS Creator has been installed as part of a binary install using the EMEWS installer, compilation is not necessary.

A sample EQR configuration file can be found [here](https://github.com/emews/emews-project-creator/blob/master/example_cfgs/eqr.yaml).

For a more thorough explanation of R-based ME workflows, see the [EMEWS Tutorial](https://www.mcs.anl.gov/~emews/tutorial/).

### INIT DB ###

The `init_db` command creates a fuly initialized EQSQL database in a user specified directory. `init_db` 
creates a postgresql database cluster in a specified path, then creates a user and database
in that cluster, and finally populates that datbase with the required eqsql tables. Note that
these steps can be performed individually if necessary using the `create_db_cluster`, `create_db`,
and `create_db_tables` commands. `init_db` (and the other database commands) require that
the postgresql binaries, `initdb`, `pg_ctl`, `'createuser`, and `createdb` are in the user's
PATH, or that the directory path is specified via the `--pg-bin-path` argument. 

Usage:

```
$ emewscreator init_db [OPTIONS]

Options:
  -d, --db-path PATH      Database directory path. The database will be
                          created in this directory.  [required]
  -u, --db-user TEXT      The database user name
  -n, --db-name TEXT      The database name
  -p, --db-port INTEGER   The database port, if any.
  -b, --pg-bin-path PATH  The path to postgresql's bin directory (i.e., the
                          directory that contains the pg_ctl, createuser and
                          createdb executables)
  -h, --help              Show this message and exit.
  ```

`init_db` takes the following arguments:

* `--db-path` - the directory in which to create the database cluster. This must not already exist,
and will be created by the command.
* `--db-user` - the database user's name, defaults to `eqsql_user`
* `--db-name` - the name of the database to create, defaults to `EQ_SQL`
* `--db-port` - an optional port number for the database to listen for connections on, if any
* `--pg-bin-path` - the path to a directory containing postgresql's `initdb`, `pg_ctl`, `createuser`, and `createdb` executables, defaults to an empty string in which case the executables are assumed to be in the user's
PATH.

### CREATE DB CLUSTER ###

The `create_db_cluster` command creates a postgresql database cluster in a specified directory. `create_db_cluster` requires that the postgresql executable `initdb` is in the user's PATH, or that the directory path is specified via the `--pg-bin-path` argument. 

Usage:

```
$ emewscreator create_db_cluster [OPTIONS]

Options:
  -d, --db-path PATH      Database directory path. The cluster will be created
                          in this directory.  [required]
  -b, --pg-bin-path PATH  The path to postgresql's bin directory (i.e., the
                          directory that contains the initdb exectuable)
  -h, --help              Show this message and exit.
```

`create_db_cluster` takes the following arguments:

* `--db-path` - the directory in which to create the database cluster. This must not already exist,
and will be created by the command.
* `--pg-bin-path` - the path to a directory containing postgresql's `initdb` executable, defaults to an empty string in which case the executable is assumed to be in the user's PATH.


### CREATE DB ###

The `create_db` command creates an eqsql database and and eqsql user in a specified postgresql database cluster. `create_db` requires that the postgresql executables, `pg_ctl`, `createuser`, and `createdb` are in the user's PATH, or that the directory path is specified in the `--pg-bin-path` argument. 

Usage:

```
$ emewscreator create_db [OPTIONS]

Options:
  -d, --db-path PATH      Database directory path. The database will be
                          created in this directory.  [required]
  -u, --db-user TEXT      The database user name
  -n, --db-name TEXT      The database name
  -p, --db-port INTEGER   The database port, if any.
  -b, --pg-bin-path PATH  The path to postgresql's bin directory (i.e., the
                          directory that contains the pg_ctl, createuser and
                          createdb executables)
  -h, --help              Show this message and exit.
  ```

`create_db` takes the following arguments:

* `--db-path` - the database cluster directory
* `--db-user` - the database user's name, defaults to `eqsql_user`
* `--db-name` - the name of the database to create, defaults to `EQ_SQL`
* `--db-port` - an optional port number for the database to listen for connections on, if any
* `--pg-bin-path` - the path to a directory containing postgresql's `pg_ctl`, `createuser`, and `createdb` executables, defaults to an empty string in which case the executables are assumed to be in the user's
PATH.

### CREATE DB TABLES ###

The `create_db_tables` command creates the required database tables in the specified database. 
`create_db_tables` requires that the postgresql's `pg_ctl` executable is in the user's PATH, or
that the directory path is specified in the `--pg-bin-path` argument. 

Usage:

```
emewscreator create_db_tables [OPTIONS]

Options:
  -d, --db-path PATH      Database directory path. The tables will be created
                          in the database in this directory.  [required]
  -u, --db-user TEXT      The database user name
  -n, --db-name TEXT      The database name
  -p, --db-port INTEGER   The database port, if any.
  -b, --pg-bin-path PATH  The path to postgresql's bin directory (i.e., the
                          directory that contains the pg_ctl, createuser and
                          createdb executables)
  -h, --help              Show this message and exit.
  ```

`create_db_tables` takes the following arguments:

* `--db-path` - the database cluster directory
* `--db-user` - the database user's name, defaults to `eqsql_user`
* `--db-name` - the name of the database in which to create the tabes, defaults to `EQ_SQL`
* `--db-port` - an optional port number for the database to listen for connections on, if any
* `--pg-bin-path` - the path to a directory containing postgresql's `pg_ctl` executable, defaults to an empty string in which case the executable is assumed to be in the user's PATH.



### EQSQL ###

The EQSQL workflow template creates a workflow that submits tasks (such as
application runs) to a queue implemented in a database. Worker pools pop tasks 
off this queue for evaluation, and push the results back to a database input queue. 
The tasks can be provided by a Python or R language model exploration (ME) algorithm. 

Usage:

```
$ emewscreator eqsql -h
Usage: emewscreator eqsql [OPTIONS]

Options:
  -c, --config PATH              Path to the template configuration file.
                                 [required if any command line arguments are
                                 missing]
  --pool-id TEXT                 The name of the task worker pool.
  --task-type INTEGER            The task type id for the tasks consumed by
                                 the worker pool.
  -n, --workflow-name TEXT       Name of the workflow.
  --trials INTEGER               Number of trials / replicates to perform for
                                 each model run. Defaults to 1.
  --model-output-file-name TEXT  Model output base file name, file name only
                                 (e.g., "output.csv").
  --me-language [python|R|None]  Model exploration algorithm programming
                                 language: Python, R, or None.
  --me-file-name TEXT            The name of the model exploration algorithm
                                 template file to generate. Omit the extension
                                 (e.g., "algo", not "algo.py").
  --me-cfg-file-name TEXT        The name of the model exploration algorithm
                                 configuration file.
  --esql-db-path PATH            The path to the eqsql database.
  -h, --help                     Show this message and exit.
```

In addition to the common configuration arguments described [above](#workflow_templates),
the eqsql template also has the following:

* `--pool-id` - a unique identifier for the swift-t worker pool created by the template.
* `--task-type` - an integer identifying the type of task the worker pool will consume. 
* `--trials` - the number of trials or replicates to perform for each task evalution. Defaults to 1.
* `--model-output-file-name` - each task evaulation is passed a file path for writing its output.
This is the name of that file.
* `--me-language` - the ME programming language (R, Python, None). The template will create an example ME written
in this language. If the value is `None`, then no ME example will be created.
* `--me-cfg-file-name` - the name of the yaml format configuration file that gets passed to the
example ME to configure it.
* `--esql-db-path` - the path to the eqsql database. This is used in the example ME to start
the database.

A sample `eqsql` configuration file can be found [here](https://github.com/emews/emews-project-creator/blob/master/example_cfgs/eqsql.yaml).

The swift file created by the `eqsql` template is a worker pool that polls the database
for tasks of the specified type to evaluate. The results of those task evaluations are
pushed back to the database together with the pool id. The example ME contains example
code for submitting tasks to the database and working with the completed tasks.

For a more thorough explanation of EQSQL-based ME workflows, see the [EMEWS Tutorial](https://www.mcs.anl.gov/~emews/tutorial/).

### HPC Parameters ###

The workflow templates' configuration file (specified with the `--config` argument)
can also contain **optional** entries for running the workflow on an HPC system
where a job is submitted via an HPC scheduler (e.g., the slurm scheduler).
See your HPC resource's documentation for details on how to set these. 

* `walltime` - the estimated duration of the workflow job. The value must be surrounded by single quotes.
* `queue` - the queue to run the workflow job on
* `project` - the project to run the workflow job with
* `nodes` - the number of nodes to allocate to the workflow job
* `ppn` - the number of processes per node to allocate to the workflow job
