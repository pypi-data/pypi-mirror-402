{% include 'common/eq_imports.j2' %}

import EQSQL;

{% include 'common/swift_utils.j2' %}

string emews_root = getenv("EMEWS_PROJECT_ROOT");
string turbine_output = getenv("TURBINE_OUTPUT");
int resident_work_rank = string2int(getenv("RESIDENT_WORK_RANK"));

int TASK_TYPE = string2int(argv("task_type", "0"));
int BATCH_SIZE = string2int(argv("batch_size"));
int BATCH_THRESHOLD = string2int(argv("batch_threshold", "1"));
string WORKER_POOL_ID = argv("worker_pool_id", "default");

file model_sh = input(emews_root+"/scripts/{{cookiecutter.model_launcher_name}}.sh");
int n_trials = string2int(argv("trials", "1"));

{% include 'common/calc_model_result_placeholder.j2' %}

{% include 'common/calc_agg_model_result_placeholder.j2' %}

// app function used to run the task
app (file out, file err) run_task_app(file shfile, string task_payload, string output_file, int trial, string instance_dir) {
    "bash" shfile task_payload output_file trial emews_root instance_dir @stdout=out @stderr=err;
}

(float result) run_obj(string task_payload, int trial, string instance_dir, string instance_id) {
    file out <instance_dir + "/" + instance_id+"_out.txt">;
    file err <instance_dir + "/" + instance_id+"_err.txt">;
    string output_file = "%s/{{cookiecutter.model_output_file_name}}_%s{{cookiecutter.model_output_file_ext}}" % (instance_dir, instance_id);
    (out,err) = run_task_app(model_sh, task_payload, output_file,  trial, instance_dir) =>
    result = get_result(output_file);
}

(string obj_result) run_task(int task_id, string task_payload) {
    float results[];

    string instance = "%s/instance_%i/" % (turbine_output, task_id);
    mkdir(instance) => {
        foreach i in [0:n_trials-1:1] {
            int trial = i + 1;
            string instance_id = "%i_%i" % (task_id, trial);
            results[i] = run_obj(task_payload, trial, instance, instance_id);
        }
    }

    obj_result = float2string(get_aggregate_result(results)); // =>
    // TODO: delete the ";" above, uncomment the ""=>"" above and 
    // and the rm_dir below to delete the instance directory if
    // it is not needed after the result have been computed.
    // rm_dir(instance);
}


run(message msgs[]) {
  // printf("MSGS SIZE: %d", size(msgs));
  foreach msg, i in msgs {
    result_payload = run_task(msg.eq_task_id, msg.payload);
    eq_task_report(msg.eq_task_id, TASK_TYPE, result_payload);
  }
}


(void v) loop(location querier_loc) {
  for (boolean b = true;
       b;
       b=c)
  {
    message msgs[] = eq_batch_task_query(querier_loc);
    boolean c;
    if (msgs[0].msg_type == "status") {
      if (msgs[0].payload == "EQ_STOP") {
        printf("loop.swift: STOP") =>
          v = propagate() =>
          c = false;
      } else {
        // sleep to give time for Python etc.
        // to flush messages
        sleep(5);
        printf("loop.swift: got %s: exiting!", msgs[0].payload) =>
        v = propagate() =>
        c = false;
      }
    } else {
      run(msgs);
      c = true;
    }
  }
}

(void o) start() {
  location querier_loc = locationFromRank(resident_work_rank);
  eq_init_batch_querier(querier_loc, WORKER_POOL_ID, BATCH_SIZE, BATCH_THRESHOLD, TASK_TYPE) =>
  loop(querier_loc) => {
    eq_stop_batch_querier(querier_loc);
    o = propagate();
  }
}

start() => printf("worker pool: normal exit.");