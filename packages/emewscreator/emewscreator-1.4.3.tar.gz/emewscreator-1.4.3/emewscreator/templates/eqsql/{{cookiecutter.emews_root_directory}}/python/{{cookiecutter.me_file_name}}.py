import argparse
from typing import Dict

from eqsql import worker_pool, db_tools, cfg
from eqsql.task_queues import local_queue


def run(exp_id: str, params: Dict):
    db_started = False
    pool = None
    task_queue = None
    try:
        # start database
        db_tools.start_db(params['db_path'])
        db_started = True

        # start local task queue
        task_queue = local_queue.init_task_queue(params['db_host'], params['db_user'],
                                                 port=None, db_name=params['db_name'])

        # check if the input and output queues are empty,
        # if not, then exit with a warning.
        if not task_queue.are_queues_empty():
            print("WARNING: db input / output queues are not empty. Aborting run", flush=True)
            return

        # start worker pool
        pool_params = worker_pool.cfg_file_to_dict(params['pool_cfg_file'])
        pool = worker_pool.start_local_pool(params['worker_pool_id'], params['pool_launch_script'],
                                            exp_id, pool_params)
        task_type = params['task_type']
        fts = []

        # TODO: submit some tasks to DB, and append the returned eqsql.eq.futures to
        # the list of futures. For example:

        # payloads = [json.dumps({'x': random.uniform(0, 10), 'y': random.uniform(0, 10)}) for _ in range(100)]
        # _, fts = task_queue.submit_tasks(exp_id, task_type, payloads)

        # TODO: do something with the completed futures. See the EQSQL documentation
        # for more options. For example:
        # for ft in task_queue.as_completed(fts):
        #     print(ft.result())

    finally:
        if task_queue is not None:
            task_queue.close()
        if pool is not None:
            pool.cancel()
        if db_started:
            db_tools.stop_db(params['db_path'])


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('exp_id', help='experiment id')
    parser.add_argument('config_file', help="yaml format configuration file")
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    params = cfg.parse_yaml_cfg(args.config_file)

    run(args.exp_id, params)
