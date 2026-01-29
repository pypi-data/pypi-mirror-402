library(reticulate)
library(jsonlite)
library(EQ.SQL)


run <- function(exp_id, params) {
    db_started <- FALSE
    pool <- NULL
    task_queue <- NULL

    eqsql <- init_eqsql(python_path = params$python_path)

    tryCatch({
        eqsql$db_tools$start_db(params$db_path)
        db_started <- TRUE

        task_queue <- init_task_queue(eqsql, params$db_host, params$db_user, params$db_port,
                                      params$db_name)

        if (!task_queue$are_queues_empty()) {
            print("WARNING: task input / output queues are not empty. Aborting run")
        } else {
            pool_params <- eqsql$worker_pool$cfg_file_to_dict(params$pool_cfg_file)
            pool <- eqsql$worker_pool$start_local_pool(params$worker_pool_id, params$pool_launch_script,
                                                       exp_id, pool_params)

            task_type <- params$task_type

            # TODO: submit some tasks to DB, and use the returned list of eqsql.task_queuecore.Future
            # For example:
            # m <- matrix(runif(20), nrow=10)
            # payloads <- apply(m, 1, function(r) {
            #     toJSON(list(x = r[1], y = r[2]))
            # })
            # result <- task_queue$submit_tasks(exp_id, task_type, payloads)
            # fts <- result[[2]]

            # TODO: do something with the completed futures. See documentation
            # for more options. For example:
            # result <- as_completed(task_queue, fts, function(ft) {
            #    ft$result()
            # })
        }

    }, finally = {
        if (!is.null(task_queue)) task_queue$close()
        if (!is.null(pool)) pool$cancel()
        if (db_started) eqsql$db_tools$stop_db(params$db_path)
    })
}

args <- commandArgs(trailingOnly = TRUE)
exp_id <- args[1]
params_file <- args[2]
params <- parse_yaml_cfg(params_file)
run(exp_id, params)
