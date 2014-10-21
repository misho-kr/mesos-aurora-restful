# ----------------------------------------------------------------------
#                      Aurora Internal API Executor
# ----------------------------------------------------------------------

import tempfile
import logging

from apache.aurora.common.aurora_job_key import AuroraJobKey
from apache.aurora.client.commands.core import get_job_config

from apache.aurora.client.factory import make_client
from gen.apache.aurora.api.ttypes import ResponseCode
from apache.aurora.client.api.updater_util import UpdaterConfig

logger = logging.getLogger("tornado.application")

# basic handlers -------------------------------------------------------

# TODO: Is this still needed, and where?
def caller_list_jobs(obj, cluster, role):
    return obj.list_jobs(cluster, role)

class AuroraInternalApiExecutor():
    """Executor for Aurora commands that calls directly Aurora client API

    Preferred executor to process requests for the Aurora Scheduler which
    uses the Aurora client API.

    Potential problem with this executor is the chance that the Aurora
    client code may not be multithread-safe (MT-safe). As the Tornado server
    acceptes simultaneous requests and handles them asynchronously, if
    there are such issues they may lead to incorrect results or disruption
    of service.
    """

    def __init__(self):
        logger.info("aurora -- internal executor created")

    def make_job_key(self, cluster, role):
        return cluster + "/" + role

    def make_job_config(self, job_key, jobspec):
        """Write jobspec string to file"""

        if jobspec is None or len(jobspec) == 0:
            logger.info("job spec not provided")
            return(None)

        logger.info("job spec:")
        lineno = 1
        for l in jobspec.splitlines():
            logger.info("  %3d: %s" % (lineno, l))
            lineno += 1

        with tempfile.NamedTemporaryFile(suffix=".aurora") as config_file:
            config_file.write(jobspec)
            config_file.flush()
            try:
                options = { 'json': False, 'bindings': () }
                return get_job_config(job_key.to_path(), config_file.name, options)
            except ValueError as e:
                logger.exception("Failed to process job configuration")
                logger.warning("----------------------------------------")
                raise e
            except NameError as e:
                logger.exception("Failed to parse job configuration")
                logger.warning("----------------------------------------")
                raise e

    def pack_instance_list(self, instances):
        """Convert list/array of Aurora instances (shards) into single element"""

        def list_from_single_or_range(x):
            r = x.split("-")
            if len(r) == 1:
                return [int(r[0]),]
            else:
                return range(int(r[0]), int(r[1])+1)

        if instances is None or len(instances) == 0:
            logger.info("shard(s) are not specified, that means all instances")
            return(None)
        else:
            packed_list = []
            [[ packed_list.extend(list_from_single_or_range(x))
                                        for x in instance.split(",")]
                                            for instance in instances ]
            logger.info("list of shards: %s" % packed_list)
            return(packed_list)

    def response_string(self, resp):
        return('Response from scheduler: %s (message: %s)'
            % (ResponseCode._VALUES_TO_NAMES[resp.responseCode], resp.messageDEPRECATED))
                                                    # yes, this is the actual attribute name

    def list_jobs(self, cluster, role):
        """Method to execute [ aurora list_jobs cluster/role command ]"""

        def job_string(cluster, job):
            return '{0}/{1.key.role}/{1.key.environment}/{1.key.name}'.format(cluster, job)

        jobkey = self.make_job_key(cluster, role)
        logger.info("request to list jobs = %s" % jobkey)

        api = make_client(cluster)
        resp = api.get_jobs(role)
        if resp.responseCode != ResponseCode.OK:
            logger.warning("Failed to list Aurora jobs")
            responseStr = self.response_string(resp)
            logger.warning(responseStr)
            return(jobkey, [], ["Failed to list Aurora jobs", responseStr])

        jobs = [ job_string(cluster, job) for job in resp.result.getJobsResult.configs ]
        if len(jobs) == 0:
            logger.info("no jobs found for key = %s" % jobkey)
        for s in jobs:
            logger.info("> %s" % s )

        return(jobkey, jobs, None)

    def create_job(self, cluster, role, environment, jobname, jobspec):
        """Method to create aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to create job = %s", job_key.to_path())

        try:
            config = self.make_job_config(job_key, jobspec)
        except Exception as e:
            return(job_key.to_path(), ["Failed to create Aurora job",
                                       "Can not create job configuration object because", str(e)])

        api = make_client(job_key.cluster)
        resp = api.create_job(config)
        if resp.responseCode != ResponseCode.OK:
            logger.warning("aurora -- create job failed")
            responseStr = self.response_string(resp)
            logger.warning(responseStr)
            return(job_key.to_path(), ["Error reported by aurora client:", responseStr])

        logger.info("aurora -- create job successful")
        return(job_key.to_path(), None)

    def update_job(self, cluster, role, environment, jobname, jobspec, instances=[]):
        """Method to update aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to update => %s", job_key.to_path())

        instances = self.pack_instance_list(instances)
        try:
            config = self.make_job_config(job_key, jobspec)
        except Exception as e:
            return(job_key.to_path(), ["Failed to update Aurora job",
                                       "Can not create job configuration object because", str(e)])

        api = make_client(cluster)
        resp = api.update_job(config, instances=instances)
        if resp.responseCode != ResponseCode.OK:
            logger.warning("aurora -- update job failed")
            responseStr = self.response_string(resp)
            logger.warning(responseStr)
            return(job_key.to_path(), ["Error reported by aurora client:", responseStr])

        logger.info("aurora -- update job successful")
        return(job_key.to_path(), None)

    def cancel_update_job(self, cluster, role, environment, jobname, jobspec=None):
        """Method to cancel an update of aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to cancel update of => %s", job_key.to_path())

        try:
            config = self.make_job_config(job_key, jobspec)
        except Exception as e:
            return(job_key.to_path(), ["Failed to cancel update of Aurora job",
                                       "Can not create job configuration object because", str(e)])

        api = make_client(cluster)
        resp = api.cancel_update(job_key, config=config)
        if resp.responseCode != ResponseCode.OK:
            logger.warning("aurora -- cancel the update of job failed")
            responseStr = self.response_string(resp)
            logger.warning(responseStr)
            return(job_key.to_path(), ["Error reported by aurora client:", responseStr])

        logger.info("aurora -- cancel of update job successful")
        return(job_key.to_path(), None)

    def restart_job(self, cluster, role, environment, jobname, jobspec=None, instances=[]):
        """Method to restart aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to restart => %s", job_key.to_path())

        instances = self.pack_instance_list(instances)
        try:
            config = self.make_job_config(job_key, jobspec)
        except Exception as e:
            return(job_key.to_path(), ["Failed to restart Aurora job",
                                       "Can not create job configuration object because", str(e)])

        # these are the default values from apache.aurora.client.commands.core.restart()
        updater_config = UpdaterConfig(
            1,          # options.batch_size
            60,         # options.restart_threshold
            30,         # options.watch_secs
            0,          # options.max_per_shard_failures
            0           # options.max_total_failures
        )

        api = make_client(job_key.cluster)
        # instances = all shards, health check = 3 sec
        resp = api.restart(job_key, instances, updater_config, 3, config=config)
        if resp.responseCode != ResponseCode.OK:
            logger.warning("aurora -- restart job failed")
            responseStr = self.response_string(resp)
            logger.warning(responseStr)
            return(job_key.to_path(), ["Error reported by aurora client:", responseStr])

        logger.info("aurora -- restart job successful")
        return(job_key.to_path(), None)

    def delete_job(self, cluster, role, environment, jobname, jobspec=None, instances=[]):
        """Method to delete aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to delete => %s", job_key.to_path())

        instances = self.pack_instance_list(instances)
        try:
            config = self.make_job_config(job_key, jobspec)
        except Exception as e:
            return(job_key.to_path(), ["Failed to delete Aurora job",
                                       "Can not create job configuration object because", str(e)])

        api = make_client(job_key.cluster)
        resp = api.kill_job(job_key, config=config, instances=instances)
        if resp.responseCode != ResponseCode.OK:
            logger.warning("aurora -- kill job failed")
            responseStr = self.response_string(resp)
            logger.warning(responseStr)
            return(job_key.to_path(), [], ["Error reported by aurora client:", responseStr])

        logger.info("aurora -- kill job successful")
        return(job_key.to_path(), [job_key.to_path()], None)

# factory --------------------------------------------------------------

def create():
    """Factory function for executor objects that call directly Aurora client API"""

    return AuroraInternalApiExecutor()
