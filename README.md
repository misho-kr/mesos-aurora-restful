Simple REST service for Apache Aurora
=====================================

__Note: work in progress__

RESTful server exposing API to interact with the [Apache Aurora scheduler](https://github.com/apache/incubator-aurora).

You may also want to look at this [Review Request #23741](https://reviews.apache.org/r/23741)
which enables REST calls to the service points of the Aurora scheduler that
were available only through the Thrift protocol.

## Purpose

Aurora includes a powerful command-line tool that is used to send
[all sorts of query and management commands](https://github.com/apache/incubator-aurora/blob/master/docs/client-commands.md)
to the scheduler. Users can start, stop and monitor jobs that are controlled
by the Aurora Scheduler.

However this command-line tool requires users to build and install the
Aurora client libraries and binaries on their machine, or to login to
server that has everything already set up.

The REST service provides remote access to the Aurora Scheduler without
prerequisites. Any REST client, or the __curl__ command, can be used to call
the REST API.

## Implementation

This is a brief description, for more detailed presentation look at the [design document](DESIGN.md).

This REST service is "simple" because it is just a wrapper around the
functionality provided by the Aurora client library (the same one that
is used by the Aurora client tool):

* REST API interface implemented with [Tornado framework](http://www.tornadoweb.org/en/stable/index.html)
* Simple Python code to map the JSON documents to calls to the Aurora client code

## Build Instructions

Ideally this repo would be a standalone source tree that can be downloaded,
built and installed. That is not possible because the Aurora client libraries
are not packaged and published to a public repository. For that reason the
build requires the presense of the Apache Aurora source code.

The workaround that is applied here is to downlad the that code, then stick
in the code of this server inside at some location, and then build it as
if it was part of the Apache Aurora source code tree.

It is a sort of hack, but it is an experiment and project to learn.
[Git submodules](http://git-scm.com/book/en/v2/Git-Tools-Submodules)
may be useful here to implement the same "hack", it is in the TODO list.

Follow the steps below to build the RESTful server.

#### Step 1: Apache Aurora source code

Use __git-clone__ or __curl__ to bring in the Apache Aurora source code.

```bash
$ git clone git@github.com:apache/incubator-aurora.git
$ cd incubator-aurora
$ ./pants
Bootstrapping pants @ 0.0.24
+ VIRTUALENV_VERSION=1.11.6
+ which python2.7
...
Cleaning up...
Pants 0.0.24 https://pypi.python.org/pypi/pantsbuild.pants/0.0.24

Usage:
  ./pants goal [option ...] [goal ...] [target...]  Attempt the specified goals.
  ./pants goal help                                 Get help.
  ./pants goal help [goal]                          Get help for the specified goal.
  ./pants goal goals                                List all installed goals.
...
```

Make sure the [pants build tool](http://pantsbuild.github.io/) managed to
bootstrap itself and finished with success. 

#### Step 2: Simple RESTful server source code

Do the same for this repository.

```bash
$ pushd src/main/python/apache/aurora/
$ git clone git@github.com:misho-kr/mesos-aurora-restful.git
$ mv mesos-aurora-restful rest
$ popd
```

#### Step 3: Execute the build

Execute the following command which will produce executable file __dist/aurora_rest.pex__

```bash
$ ./pants build src/main/python/apache/aurora/rest/bin:
Build operating on top level addresses: ...
...
Wrote dist/aurora_rest.pex
$ dist/aurora_rest.pex --help 
Usage: dist/aurora_rest.pex [OPTIONS]
...
```

## Start the REST server

The command below will start the Aurora REST service. The paramters that are passed to
the executable will have the following effect:

- The server will listen for requests on port __8888__
- All requests will be executed by __direct calls to the Aurora client code__
- Every request will be handled by __separate thread running in the same process__
- At most __4 threads__ will be spawned to process API calls

```
$ dist/aurora_rest.pex --port=8888 --executor=internal --application=thread --parallel=4
```

These parameters and their effects are explained in the [design document](DESIGN.md).

## REST API

* [GET /alpha/jobs/{cluster}/{role}](#get-alphajobsclusterrole): List all jobs
* [PUT /alpha/job/{cluster}/{role}/{environment}/{jobname}](#put-alphajobclusterroleenvironmentjobname): Create job
* [PUT /alpha/job/{cluster}/{role}/{environment}/{jobname}/update?shards={X}](#put-alphajobclusterroleenvironmentjobnameupdateshardsx): Update job
* [DELETE /alpha/job/{cluster}/{role}/{environment}/{jobname}/update](#delete-alphajobclusterroleenvironmentjobnameupdate): Cancel update
* [PUT /alpha/job/{cluster}/{role}/{environment}/{jobname}/restart?shards={X}](#put-alphajobclusterroleenvironmentjobnamerestartshardsx): Restart job
* [DELETE /alpha/job/{cluster}/{role}/{environment}/{jobname}?shards={X}](#delete-alphajobclusterroleenvironmentjobnameshardsx): Kill Aurora job
* [GET /alpha/version](#get-alphaversion): Query service version

#### `GET` /alpha/jobs/{cluster}/{role}

```
HTTP/1.1 200 OK
Content-Type: application/json
Server: TornadoServer/3.2.1
```
```json
{
    "count": 3,
    "jobs": {
        "1": "paas-aurora/mkrastev/devel/rhel59_world2",
        "2": "paas-aurora/mkrastev/devel/kraken_app",
        "3": "paas-aurora/mkrastev/devel/rhel59_world"
    },
    "key": "paas-aurora/mkrastev",
    "status": "success"
}
```

#### `PUT` /alpha/job/{cluster}/{role}/{environment}/{jobname}

```bash
$ curl -s -X PUT --data-binary @rhel59_world2.aurora \
  "http://localhost:8888/alpha/jobs/paas-aurora/mkrastev/devel/rhel59_world2" | \
  python -m json.tool
```

**Response:**
```
HTTP/1.1 201 Created
Content-Type: application/json
Server: TornadoServer/3.2.1
```
```json
{
    "count": 1,
    "job": "paas-aurora/mkrastev/devel/rhel59_world2",
    "key": "paas-aurora/mkrastev/devel/rhel59_world2",
    "status": "success"
}
```

#### `PUT` /alpha/job/{cluster}/{role}/{environment}/{jobname}/update?shards={X}

```bash
$ curl -s -X PUT --data-binary @rhel59_world2.aurora \
  "http://localhost:8888/alpha/jobs/paas-aurora/mkrastev/devel/rhel59_world2?shards=1" | \
  python -m json.tool
```

**Response:**
```
HTTP/1.1 202 Accepted
Content-Type: application/json
Server: TornadoServer/3.2.1
```
```json
{
    "count": 1,
    "job": "paas-aurora/mkrastev/devel/rhel59_world2",
    "key": "paas-aurora/mkrastev/devel/rhel59_world2",
    "status": "success"
}
```

#### `DELETE` /alpha/job/{cluster}/{role}/{environment}/{jobname}/update

```
HTTP/1.1 202 Accepted
Content-Type: application/json
Server: TornadoServer/3.2.1
```
```json
{
    "count": 1,
    "job": "paas-aurora/mkrastev/devel/rhel59_world2",
    "key": "paas-aurora/mkrastev/devel/rhel59_world2",
    "status": "success"
}
```

#### `PUT` /alpha/job/{cluster}/{role}/{environment}/{jobname}/restart?shards={X}

```
HTTP/1.1 202 Accepted
Content-Type: application/json
Server: TornadoServer/3.2.1
```
```json
{
    "count": 1,
    "job": "paas-aurora/mkrastev/devel/rhel59_world2",
    "key": "paas-aurora/mkrastev/devel/rhel59_world2",
    "status": "success"
}
```

#### `DELETE` /alpha/job/{cluster}/{role}/{environment}/{jobname}?shards={X}

```bash
$ curl -s -X \
  DELETE "http://localhost:8888/alpha/jobs/paas-aurora/mkrastev/devel/rhel59_world2?shards=2" | \
  python -m json.tool
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Server: TornadoServer/3.2.1
```
````json
{
    "count": 1,
    "job": "paas-aurora/mkrastev/devel/rhel59_world2",
    "key": "paas-aurora/mkrastev/devel/rhel59_world2",
    "status": "success"
}
```

#### `GET` /alpha/version

```
HTTP/1.1 200 OK
Content-Type: application/json
Server: TornadoServer/3.2.1
```
```json
{
    "status": "success",
    "version": "0.1"
}
```
