# ----------------------------------------------------------------------
#
#                  Tornado Synchronous Request Handlers
#
# Request handlers that implement synchronous, blocking execution of
# RESTful calls. Only one request can be processed at a time, so while
# one is being executed all other requests are queued up and serviced
# in the order they were received.
#
# ----------------------------------------------------------------------

import logging
import httplib
import tornado.web

logger = logging.getLogger("tornado.access")

# basic handlers -------------------------------------------------------

class VersionHandler(tornado.web.RequestHandler):
    """Request handler reporting the version of the REST service"""

    def get(self):
        self.write({
            "status":       "success",
            "version":      "0.1"
        })

# aurora interface handlers --------------------------------------------

class ListJobsHandler(tornado.web.RequestHandler):
    """Request handler to list all Aurora jobs matching a search criteria"""

    def get(self, cluster, role):
        logger.info("entered ListJobsHandler::GET")

        (jobkey, jobs, errors) = self.application.get_executor().list_jobs(
                                                            cluster, role)
        if errors is None:
            logger.info("no errors")
            # no jobs were found to terminate, not an error
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

class JobHandler(tornado.web.RequestHandler):
    """Request handler to create and kill Aurora jobs

    1. HTTP PUT method to create jobs
    2. HTTP DELETE method to kill jobs, optionally with _shards_ parameter(s)
       to specify which instances should be killed
    """

    def put(self, cluster, role, environment, jobname):
        logger.info("entered JobHandler::PUT")

        (jobkey, errors) = self.application.get_executor().create_job(
                                    cluster, role, environment, jobname,
                                    self.request.body)
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

    def delete(self, cluster, role, environment, jobname):
        logger.info("entered JobHandler::DELETE")

        jobspec = None
        if self.request.body is not None and len(self.request.body) > 0:
            jobspec = self.request.body
        shards = self.get_query_arguments("shards")

        (jobkey, jobs, errors) = self.application.get_executor().delete_job(
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

    def put(self, cluster, role, environment, jobname):
        logger.info("entered UpdateJobHandler::PUT")

        shards = self.get_query_arguments("shards")
        (jobkey, errors) = self.application.get_executor().update_job(
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

    def delete(self, cluster, role, environment, jobname):
        logger.info("entered UpdateJobHandler::DELETE")

        jobspec = None
        if self.request.body is not None and len(self.request.body) > 0:
            jobspec = self.request.body

        (jobkey, errors) = self.application.get_executor().cancel_update_job(
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

    def put(self, cluster, role, environment, jobname):
        logger.info("entered RestartJobHandler::PUT")

        jobspec = None
        if self.request.body is not None and len(self.request.body) > 0:
            jobspec = self.request.body
        shards = self.get_query_arguments("shards")

        (jobkey, errors) = self.application.get_executor().restart_job(
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

class AuroraSyncApplication(tornado.web.Application):
    """Tornado synchronous application implementing Aurora REST service points

    Requests are processed one at a time in blocking mode. When one
    request is being executed Tornado guarantees that all other requests
    are queued up for service in the order they were received.

    Note: the synchronous execution implemented by this class can be
    replicated by coupling AuroraAsyncApplication with CoroutineAuroraExecutor.
    Therfore after the initial development phase this class may be marked as
    obsolete.
    """

    def __init__(self, prefix, executor=None, **settings):
        logging.info("Tornado sync application created")

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

        super(AuroraSyncApplication, self).__init__(handlers, **settings)

    def get_executor(self): return self.executor

    def make_app_handlers(self, url_prefix, handlers):
        return [ ("/" + url_prefix + "/" + url.lstrip('/'), handler)
                    for url, handler in handlers ]

# factory --------------------------------------------------------------

def create(url_prefix, executor=None, **settings):
    """Factory function for Tornado Applications implementing synchronous processing"""

    return AuroraSyncApplication(url_prefix, executor=executor, **settings)
