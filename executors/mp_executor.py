# ----------------------------------------------------------------------
#           Aurora Command Executor using ProcessPool
# ----------------------------------------------------------------------

import logging
import multiprocessing

from functools import partial   # , wraps

from tornado.ioloop import IOLoop
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger("tornado.access")

# thread-pool executor ------------------------------------------------

def call_by_name(method_name, obj, *args, **kwargs):
    """Helper function to enable ProcessPoolExecutor to call object's method"""

    method = getattr(obj, method_name)
    return method(*args, **kwargs)

class ProcessAuroraExecutor():
    """Aurora Command Executor that spawns multiple processes to execute requests concurrently

    Multiple processes managed with concurrent.futures.ProcessPoolExecutor
    are used to provide simultaneous execution of Aurora commands.
    """

    def __init__(self, delegate, process_pool, io_loop):
        logger.info("ProcessAuroraExecutor(procs=%s) created" %
            (str(process_pool._max_workers) if process_pool._max_workers else "unlimited"))

        self.delegate = delegate
        self.executor = process_pool
        self.io_loop  = io_loop

    def run_on_executor(self, method_name, obj, *args, **kwargs):
        """Helper method to enable ProcessPoolExecutor to call object's method"""

        logger.info("ProcessAuroraExecutor delegated method: %s" % method_name)

        return self.executor.submit(call_by_name, method_name, obj, *args, **kwargs)

    delegated_methods = [
        "list_jobs",
        "create_job",
        "update_job",
        "cancel_update_job",
        "restart_job",
        "delete_job",
    ]

    def __getattr__(self, name):
        if name in self.delegated_methods:
            logger.info("ProcessAuroraExecutor lookup method: %s" % name)
            return partial(self.run_on_executor, name, self.delegate)
        else:
            raise AttributeError("Instance does not have attribute: %s" % name)

# factory --------------------------------------------------------------

def create(executor, process_pool=None, io_loop=None, max_procs=0):
    """Factory function for Process-based Aurora executor objects"""

    if max_procs is None:
        max_procs = multiprocessing.cpu_count()

    io_loop     = io_loop or IOLoop.instance()
    process_pool = process_pool or ProcessPoolExecutor(max_procs)

    return ProcessAuroraExecutor(executor, process_pool, io_loop)
