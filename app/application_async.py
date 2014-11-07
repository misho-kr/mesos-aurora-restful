# ----------------------------------------------------------------------
#
#                  Tornado Asynchronous Request Handlers
#
# Request handlers that enable asynchronous, non-blocking execution of
# RESTful calls. To implement simultaneous execution of multiple
# requests the executor object that is used by the handlers must not
# block the execution, but instead it must somehow start the execution
# in background and report the completion status later using futures.
#
# ----------------------------------------------------------------------

import logging
import httplib

import tornado.web
from tornado import gen

logger = logging.getLogger("tornado.access")

# basic handlers -------------------------------------------------------

class VersionHandler(tornado.web.RequestHandler):
    """Request handler reporting the version of the REST service"""

    def get(self):
        logger.info("entered VersionHandler::GET")
        self.write({
            "status":       "success",
            "version":      "0.1"
        })

# aurora interface handlers --------------------------------------------

class ListJobsHandler(tornado.web.RequestHandler):
    """Request handler to list all Aurora jobs matching a search criteria"""

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, cluster, role):
        logger.info("entered ListJobsHandler::GET")

        (jobkey, jobs, errors) = \
            yield self.application.get_executor().list_jobs(cluster, role)
        if errors is None:
            logger.info("no errors")
            # no jobs were found to termminate, not an error
            if len(jobs) == 0:
                logger.info("nothing found")
                self.set_status(httplib.NOT_FOUND)
            self.write({
                "status":       "success",
                "key":          jobkey,
                "count":        len(jobs),
                "jobs":         dict(enumerate(jobs, start=1))
            })

        else:
            logger.info("internal error")
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({
                "status":       "failure",
                "key":          jobkey,
                "errors":       errors,
                "count":        0,
                "jobs":         {}
            })

        logger.info("exiting ListJobsHandler::GET")
        self.finish()

class JobHandler(tornado.web.RequestHandler):
    """Request handler to create and kill Aurora jobs

    1. HTTP PUT method to create jobs
    2. HTTP DELETE method to kill jobs, optionally with _shards_ parameter(s)
       to specify which instances should be killed
    """

    @tornado.web.asynchronous
    @gen.coroutine
    def put(self, cluster, role, environment, jobname):
        logger.info("entered JobHandler::PUT")

        (jobkey, errors) = \
            yield self.application.get_executor().create_job(
                            cluster, role, environment, jobname, self.request.body)
        if errors is None:
            self.set_status(httplib.CREATED)
            self.write({
                "status":       "success",
                "key":          jobkey,
                "count":        1,
                "job":          jobkey
            })

        else:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({
                "status":       "failure",
                "key":          jobkey,
                "count":        0,
                "job":          [],
                "errors":       errors
            })

    @tornado.web.asynchronous
    @gen.coroutine
    def delete(self, cluster, role, environment, jobname):
        logger.info("entered JobHandler::DELETE")

        jobspec = None
        if self.request.body is not None and len(self.request.body) > 0:
            jobspec = self.request.body
        shards = self.get_query_arguments("shards")

        (jobkey, jobs, errors) = \
            yield self.application.get_executor().delete_job(
                            cluster, role, environment, jobname,
                            jobspec=jobspec, instances=shards)
        if errors is None:
            # no jobs were found to terminate, not an error
            if len(jobs) == 0:
                self.set_status(httplib.NOT_FOUND)
            self.write({
                "status":       "success",
                "key":          jobkey,
                "count":        len(jobs),
                "job":          jobs[0] if len(jobs) > 0 else ""
            })

        else:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({
                "status":       "failure",
                "key":          jobkey,
                "count":        0,
                "job":          [],
                "errors":       errors
            })

class UpdateJobHandler(tornado.web.RequestHandler):
    """Request handlers to update Aurora jobs, or cancel the update of

    1. HTTP PUT method to update jobs, optionally with _shards_ query parameter
    2. HTTP DELETE method to cancel the job update
    """

    @tornado.web.asynchronous
    @gen.coroutine
    def put(self, cluster, role, environment, jobname):
        logger.info("entered UpdateJobHandler::PUT")

        shards = self.get_query_arguments("shards")
        (jobkey, errors) = \
            yield self.application.get_executor().update_job(
                            cluster, role, environment, jobname,
                            jobspec=self.request.body, instances=shards)
        if errors is None:
            self.set_status(httplib.ACCEPTED)
            self.write({
                "status":       "success",
                "key":          jobkey,
                "count":        1,
                "job":          jobkey
            })

        else:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({
                "status":       "failure",
                "key":          jobkey,
                "count":        0,
                "job":          [],
                "errors":       errors
            })

    @tornado.web.asynchronous
    @gen.coroutine
    def delete(self, cluster, role, environment, jobname):
        logger.info("entered UpdateJobHandler::DELETE")

        jobspec = None
        if self.request.body is not None and len(self.request.body) > 0:
            jobspec = self.request.body

        (jobkey, errors) = \
            yield self.application.get_executor().cancel_update_job(
                            cluster, role, environment, jobname, jobspec)
        if errors is None:
            self.set_status(httplib.ACCEPTED)
            self.write({
                "status":       "success",
                "key":          jobkey,
                "count":        1,
                "job":          jobkey
            })

        else:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({
                "status":       "failure",
                "key":          jobkey,
                "count":        0,
                "job":          [],
                "errors":       errors
            })

class RestartJobHandler(tornado.web.RequestHandler):
    """Request handler to restart Aurora jobs

    1. HTTP PUT method to restart job, optionally with _shards_ query parameter
    """

    @tornado.web.asynchronous
    @gen.coroutine
    def put(self, cluster, role, environment, jobname):
        logger.info("entered RestartJobHandler::PUT")

        jobspec = None
        if self.request.body is not None and len(self.request.body) > 0:
            jobspec = self.request.body
        shards = self.get_query_arguments("shards")

        (jobkey, errors) = \
            yield self.application.get_executor().restart_job(
                            cluster, role, environment, jobname,
                            jobspec=jobspec, instances=shards)
        if errors is None:
            self.set_status(httplib.ACCEPTED)
            self.write({
                "status":       "success",
                "key":          jobkey,
                "count":        1,
                "job":          jobkey
            })

        else:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({
                "status":       "failure",
                "key":          jobkey,
                "count":        0,
                "job":          [],
                "errors":       errors
            })

# application ----------------------------------------------------------

class AuroraAsyncApplication(tornado.web.Application):
    """Tornado asynchronous application implementing Aurora REST service points

    Requests can be processed in non-blocking mode provided the executor
    object can carry out the execution in the background and report the
    completion status later by using futures.
    """

    def __init__(self, prefix, executor=None, **settings):
        logging.info("Tornado async application created")

        self.url_prefix = prefix.lstrip('/').rstrip('/')
        self.executor   = executor

        # TODO: remove this or make it optional and controlled by cli switch
        settings["debug"] = True
        handlers = self.make_app_handlers(self.url_prefix, [
            (r"/version",                           VersionHandler),
            (r"/jobs/(.+)/(.+)/(.+)/(.+)/restart",  RestartJobHandler),
            (r"/jobs/(.+)/(.+)/(.+)/(.+)/update",   UpdateJobHandler),
            (r"/jobs/(.+)/(.+)/(.+)/(.+)",          JobHandler),
            (r"/jobs/(.+)/(.+)",                    ListJobsHandler)
        ])

        super(AuroraAsyncApplication, self).__init__(handlers, **settings)

    def get_executor(self): return self.executor

    def make_app_handlers(self, url_prefix, handlers):
        return [ ("/" + url_prefix + "/" + url.lstrip('/'), handler)
                    for url, handler in handlers ]

# factory --------------------------------------------------------------

def create(url_prefix, executor=None, **settings):
    """Factory function for Tornado Applications implementing asynchronous processing"""

    return AuroraAsyncApplication(url_prefix, executor=executor, **settings)
