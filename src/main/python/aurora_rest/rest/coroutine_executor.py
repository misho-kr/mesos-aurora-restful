# ----------------------------------------------------------------------
#           Aurora Command Executor using Coroutines
# ----------------------------------------------------------------------

import logging

from tornado.concurrent import return_future

logger = logging.getLogger("tornado.access")

# coroutine executor --------------------------------------------------

class CoroutineAuroraExecutor():
    """Executor that can be combine Tornado Async Application with blocking executor

    Implementation of Decorator design pattern.

    This executor makes possible to use another executor object that
    run in synchronous mode to Tornado Async Application that use
    coroutines and futures for asynchronous execution of requests.

    This executor will delegate commands to another synchronous executor
    and then invoke the callback. Therefore the execution of Aurora commands
    is still synchronous.

    Note: this a test class to experiment with Tornado async operations.
    """

    #TODO: What will happen when this executor is coupled with non-blocking executor

    def __init__(self, executor):
        logger.info("CoroutineAuroraExecutor created")

        self.executor = executor

    @return_future
    def list_jobs(self, cluster, role, callback=None):
        logger.info("entered CoroutineAuroraExecutor::list_jobs")

        result = self.executor.list_jobs(cluster, role)
        callback(result)

    @return_future
    def create_job(self, cluster, role, environment, jobname, jobspec, callback=None):
        logger.info("entered CoroutineAuroraExecutor::create_job")

        result = self.executor.create_job(cluster, role, environment, jobname, jobspec)
        callback(result)

    @return_future
    def update_job(self, cluster, role, environment, jobname, jobspec, instances=[], callback=None):
        logger.info("entered CoroutineAuroraExecutor::update_job")

        result = self.executor.update_job(cluster, role, environment, jobname, jobspec, instances)
        callback(result)

    @return_future
    def cancel_update_job(self, cluster, role, environment, jobname, jobspec=None, callback=None):
        logger.info("entered CoroutineAuroraExecutor::cancel_update_job")

        result = self.executor.cancel_update_job(cluster, role, environment, jobname, jobspec)
        callback(result)

    @return_future
    def restart_job(self, cluster, role, environment, jobname, jobspec=None, instances=[], callback=None):
        logger.info("entered CoroutineAuroraExecutor::restart_job")

        result = self.executor.restart_job(cluster, role, environment, jobname, jobspec, instances)
        callback(result)

    @return_future
    def delete_job(self, cluster, role, environment, jobname, jobspec=None, instances=[], callback=None):
        logger.info("entered CoroutineAuroraExecutor::delete_job")

        result = self.executor.delete_job(cluster, role, environment, jobname, jobspec, instances)
        callback(result)

# factory --------------------------------------------------------------

def create(executor=None):
    """Factory function for Coroutine-based Aurora executor objects"""

    return CoroutineAuroraExecutor(executor=executor)
