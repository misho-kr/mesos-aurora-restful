Design notes for Simple REST service for Apache Aurora
======================================================

__Note: work in progress__

The [main document](README.md) explained the purpose of this project and
gave instructions about how to build and start the server. Here the 
internal design is presented in detail.

## Design and Implementation

This REST service is "simple" wrapper around the functionality provided
by the Aurora client library (which is used by the Aurora client tool).
It does not add or modify any features on top of it.

Furthermore, in this initial version not all commands available through
the command-line tool are exposed.

The server is built with the [Tornado framework](http://www.tornadoweb.org/en/stable/index.html)
which offers the following advantages:

* It is written in Python like the Aurora command-line client
* It can process requests in non-blocking mode that can help the service to
scale up

The Tornado web server accepts REST API calls and delegates them
either to the Aurora client code or (external) client tool. The simultaneous
execution of multiple requests is implemented with threads or
external processes managed with [concurrent.futures](http://pythonhosted.org//futures).
These options are chosen when the server is started by passing the
appropriate command-line swithes and arguments.

#### Start the REST server

The command below shows the recommended arguments to start the Aurora
RESTful server. The parameters that are passed to the executable will
have the following effect:

- The server will listen for requests on port __8888__
- All requests will be executed by __direct calls to the Aurora client code__
- Every request will be handled by __separate thread running in the same process__
- At most __4 threads__ will be spawned to process API calls

```
$ aurora_rest --port=8888 --executor=internal --application=thread --parallel=4
```

## Execution Modes

This section explain in details the different execution modes to process and
execute in parallel many requsts that are supported by the RESTful server.

The reason for making these options available is due to the fact that the
Aurora client libraries are not designed to be multi-threaded (MT) safe.
It was not known in advance how the code would behave when the Tornado
framework runs multiple threads in the same process -- as they enter critical
section that may lead to corrupted and invaid data. On the other hand a REST
service that serializes the request execution is not going to be that useful,
so such restriction had to be resolved or worked-around. It is these design
goals -- reasonable performance and MT-safety led to the implemention of
several different ways to accept and delegate REST API calls to the Aurora
scheduler.

The REST service can be started in one of several execution modes, and
that mode can not be changed after the server has started. Some modes allow
the service to scale up and handle multiple requests simultaneously, at 
the risk that runtime errors may occur due simultaneous access and
modification to data that not protected by MT-primitives to ensure it
does not get corrupted and is always in correct state. Others modes
guarantee that no such errors will occur but do not provide the same
level of parallelism and runtime performance. There is even one that is
useful only for troubleshooting problems in the code of the REST service
so it will be used rarely.

The recommended execution mode is __asynchronous execution with multiple threads__
as the example above demonstrated.

All execution modes are categorized into two groups as described below.
This picture illustrates all available execution modes and how they can be
combined to provide the desired service operation.

TBC __add picture here__ TBC

### A. Command execution modes

The defining feature of this group is how requests are handled by the
application code __after__ they were accepted and dispatched by the Tornado
web-handling code.

#### A.1 Aurora API calls

The preferred execution mode to handle requests for the Aurora scheduler
is by directly calling the Aurora client code. In order to enable this
the REST service imports the same Python modules that the Aurora client uses
and simply calls the right methods.

Potential problem with this execution mode is the chance that the Aurora
client code may not be multithread-safe (MT-safe). As the Tornado server
acceptes simultaneous requests and handles them asynchronously, if there
are such issues they may lead to incorrect results or disruption of service.

#### A.2 External command

The alternative, and probably safer but slower, execution mode is when
requests are handled by delegating to an external command to run the
command line tool that the implements
[all sorts of query and management commands](https://github.com/apache/incubator-aurora/blob/master/docs/client-commands.md).
In this mode the Aurora client code is executed by a new process in
single-threaded mode just as the Aurora client command line tool does. 

### B. Request handling modes

The execution modes in this group are different from each other
by how the web requests are handled inside the server -- after the requests
are accepted and before they are delegated to the Aurora client code.

Regardless of the choice of how Aurora commands are actually executed,
the REST service can handle requests synchronously or asynchronousely,
one at a time or in parallel.

#### B.1 Multithreaded mode

Multiple threads managed with [ThreadPool](http://pythonhosted.org//futures/#threadpoolexecutor-objects)
are used to provide simultaneous execution of RESTful calls. 

#### B.2 Multiprocess mode

Similar to the previous mode but, instead of threads, external processes that are
managed with [ProcessPool](http://pythonhosted.org//futures/#processpoolexecutor-objects)
are used to execute the RESTful calls simultaneously.

#### B.3 Function calls

This is the simplest execution mode from code perspective. There is nothing
complicated here -- the Tornado request handler calls directly the code
that handles the execution of Aurora commands. The result is a __synchronous__
processing of RESTful calls that are handled one at a time. The execution
will block for every request and will wait until it is completed, during which
time the service is unavailable to accept and process new requests.

#### B.4 Coroutines

This is an internal execution mode that enables, together with a thread or
process pool, to process RESTful calls *asynchornously*. When this mode is
combined with either multiple threads or processes that makes possible to
process requests in parallel.
