# ----------------------------------------------------------------------
#           Aurora Command Executor using ThreadPool
# ----------------------------------------------------------------------

import logging
import multiprocessing

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("tornado.access")

# thread-pool executor ------------------------------------------------

class ThreadAuroraExecutor():
    """Aurora Command Executor that spawns multiple threads to execute requests concurrently

    Multiple threads managed with concurrent.futures.ThreadPoolExecutor
    are used to provide simultaneous execution of Aurora commands.
    """

    def __init__(self, delegate, thread_pool, io_loop):
        logger.info("ThreadAuroraExecutor(threads=%s) created" %
            (str(thread_pool._max_workers) if thread_pool._max_workers else "unlimited"))

        self.delegate = delegate
        self.executor = thread_pool
        self.io_loop  = io_loop

    @run_on_executor
    def list_jobs(self, cluster, role):
        logger.info("entered ThreadAuroraExecutor::list_jobs")

        return self.delegate.list_jobs(cluster, role)

    @run_on_executor
    def create_job(self, cluster, role, environment, jobname, jobspec):
        logger.info("entered ThreadAuroraExecutor::create_job")

        return self.delegate.create_job(cluster, role, environment, jobname, jobspec)

    @run_on_executor
    def update_job(self, cluster, role, environment, jobname, jobspec, instances=[]):
        logger.info("entered ThreadAuroraExecutor::update_job")

        return self.delegate.update_job(cluster, role, environment, jobname, jobspec, instances)

    @run_on_executor
    def cancel_update_job(self, cluster, role, environment, jobname, jobspec=None):
        logger.info("entered ThreadAuroraExecutor::cancel_update_job")

        return self.delegate.cancel_update_job(cluster, role, environment, jobname, jobspec)

    @run_on_executor
    def restart_job(self, cluster, role, environment, jobname, jobspec=None, instances=[]):
        logger.info("entered ThreadAuroraExecutor::restart_job")

        return self.delegate.restart_job(cluster, role, environment, jobname, jobspec, instances)

    @run_on_executor
    def delete_job(self, cluster, role, environment, jobname, jobspec=None, instances=[]):
        logger.info("entered ThreadAuroraExecutor::delete_job")

        return self.delegate.delete_job(cluster, role, environment, jobname, jobspec, instances)

# factory --------------------------------------------------------------

def create(executor, thread_pool=None, io_loop=None, max_workers=0):
    """Factory function for Thread-based Aurora executor objects"""

    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    io_loop     = io_loop or IOLoop.instance()
    thread_pool = thread_pool or ThreadPoolExecutor(max_workers)

    return ThreadAuroraExecutor(executor, thread_pool, io_loop)
