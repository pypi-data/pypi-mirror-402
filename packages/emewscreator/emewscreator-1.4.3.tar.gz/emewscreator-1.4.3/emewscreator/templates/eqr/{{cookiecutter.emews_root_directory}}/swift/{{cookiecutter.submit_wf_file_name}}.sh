{% include 'common/submission_prefix.j2' %}
{% include 'common/eq_submission_prefix.j2' %}

{% include 'common/submission_job_exports.j2' %}

{% include 'common/submission_r_paths.j2' %}

# EQ/R location
EQR="{{cookiecutter.eqr_dir}}"

# TODO: If Python cannot be found or there are "Cannot find 
# X package" type errors then these two environment variables
# will need to be uncommented and set correctly.
# export PYTHONHOME=/path/to/python

# Resident task workers and ranks
export TURBINE_RESIDENT_WORK_WORKERS=1
export RESIDENT_WORK_RANKS=$(( PROCS - 2 ))

{% include 'common/machine.j2' %}

EMEWS_EXT="$EMEWS_PROJECT_ROOT/ext/emews"

# Copies ME config file to experiment directory
FNAME=$(basename "$ME_CONFIG")
ME_CONFIG_CP="$TURBINE_OUTPUT/$FNAME"
cp "$ME_CONFIG" "$ME_CONFIG_CP"

CMD_LINE_ARGS="$* --me_config_file=$ME_CONFIG_CP --trials=$CFG_TRIALS"

{% include 'common/submission_args.j2' %}
{% include 'common/submission.j2' %}
