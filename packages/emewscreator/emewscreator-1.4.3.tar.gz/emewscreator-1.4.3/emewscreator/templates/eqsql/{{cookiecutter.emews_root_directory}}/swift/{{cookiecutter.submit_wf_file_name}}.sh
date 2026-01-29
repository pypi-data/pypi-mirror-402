{% include 'common/submission_prefix.j2' %}
{% include 'common/eqsql_submission_prefix.j2' %}

{% include 'common/submission_job_exports.j2' %}

{% include 'common/submission_r_paths.j2' %}

# EQSQL swift extension location
EQSQL="{{cookiecutter.eqsql_dir}}"
EMEWS_EXT="$EMEWS_PROJECT_ROOT/ext/emews"

# TODO: if Python cannot be found then uncomment
# and edit this line.
# export PYTHONHOME=/path/to/python

# TODO: if there are "Cannot find 
# X package" type Python errors then append
# the missing package's path to the PYTHONPATH
# variable below, separating the entries with ":"
export PYTHONPATH="$EMEWS_PROJECT_ROOT/python:$EQSQL"

# Resident task workers and ranks
export TURBINE_RESIDENT_WORK_WORKERS=1
export RESIDENT_WORK_RANK=$(( PROCS - 2 ))

# EQSQ DB variables, set from the CFG file.
# To change, these edit the CFG file.
export DB_HOST=$CFG_DB_HOST
export DB_USER=$CFG_DB_USER
export DB_PORT=${CFG_DB_PORT:-}
export DB_NAME=$CFG_DB_NAME
export EQ_DB_RETRY_THRESHOLD=$CFG_DB_RETRY_THRESHOLD

# TODO: Set MACHINE to your schedule type (e.g. pbs, slurm, cobalt etc.),
# or empty for an immediate non-queued unscheduled run
MACHINE=""

if [ -n "$MACHINE" ]; then
  MACHINE="-m $MACHINE"
else
  echo "Logging output and errors to $TURBINE_OUTPUT/output.txt"
  # Redirect stdout and stderr to output.txt
  # if running without a scheduler.
  exec &> "$TURBINE_OUTPUT/output.txt"
fi

CMD_LINE_ARGS="--trials=$CFG_TRIALS --task_type=$CFG_TASK_TYPE --batch_size=$CFG_BATCH_SIZE "
CMD_LINE_ARGS+="--batch_threshold=$CFG_BATCH_THRESHOLD --worker_pool_id=$CFG_POOL_ID $*"

{% include 'common/submission_args.j2' %}
{% include 'common/eqsql_submission.j2' %}
