{% include 'common/submission_prefix.j2' %}
echo "UPF FILE:              $CFG_UPF"
echo "--------------------------"

{% include 'common/submission_job_exports.j2' %}

{% include 'common/submission_r_paths.j2' %}

{% include 'common/submission_python_paths.j2' %}

{% include 'common/machine.j2' %}

EMEWS_EXT="$EMEWS_PROJECT_ROOT/ext/emews"

# Copies UPF file to experiment directory
U_UPF_FILE="$EMEWS_PROJECT_ROOT/$CFG_UPF"
UPF_FILE="$TURBINE_OUTPUT/upf.txt"
cp "$U_UPF_FILE" "$UPF_FILE"

CMD_LINE_ARGS="$* -f=$UPF_FILE "

{% include 'common/submission_args.j2' %}
{% include 'common/submission.j2' %}
