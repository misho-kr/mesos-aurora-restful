#!/usr/bin/env python
# ----------------------------------------------------------------------
#  REST service exposing API interface to Aurora client commands
# ----------------------------------------------------------------------

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.process

from tornado.options import define, options

from apache.aurora.rest.apps import (
    application,
    application_async
)

from apache.aurora.rest.executors import (
    external_executor,
    internal_executor,
    coroutine_executor,
    mt_executor,
    mp_executor
)

import logging
logger = logging.getLogger("tornado.access")

# The REST service does not have any CPU-intensive tasks to speak of
# therefore each CPU should be able to handle multiple requests
NCPUs = tornado.process.cpu_count()
REQUESTS_PER_CPU = 16

define("port", 		default=8888, 		help="run on the given port", type=int)
define("executor", 	default="internal", 	help="Type of Aurora command executor", type=str)
define("concurrency", 	default="process", 	help="Type of concurrent execution", type=str)
define("parallel", 	default=NCPUs*REQUESTS_PER_CPU, help="max number of simultaneous requests", type=int)

def proxy_main():
    """Main function to prepare the Tornado web server to process Aurora REST API calls

    Tornado web server can process requests in one of several ways:

      1. Asynchronously by spawning new process or thread for each requests,
         managed by ProcessPool or ThreadPool respectively)
      2. Synchronously by executing requests one at a time, blocking new
         requests until the current one is completed

    Aurora client commands can be executed either by:

      1. Spawning external process to invoke the Aurora command-line client
      2. Calling directly the Aurora client code

    """

    tornado.options.parse_command_line()

    if options.executor == "external":
        client = external_executor.create()
    elif options.executor == "internal":
        client = internal_executor.create()
    else:
        logger.error("invalid executor: %s, exiting!" % options.executor)
        return

    if options.concurrency == "coroutine":
        app = application_async.create("alpha", executor=coroutine_executor.create(client))
    elif options.concurrency == "thread":
        executor = mt_executor.create(client, max_workers=options.parallel)
        app = application_async.create("alpha", executor=executor)
    elif options.concurrency == "process":
        executor = mp_executor.create(client, max_procs=options.parallel)
        app = application_async.create("alpha", executor=executor)
    else:
        app = application.create("alpha", executor=client)

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)

    tornado.ioloop.IOLoop.instance().start()
