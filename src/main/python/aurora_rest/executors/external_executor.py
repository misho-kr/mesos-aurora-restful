# ----------------------------------------------------------------------
#                       Aurora External Command Executor
# ----------------------------------------------------------------------

import logging
import tempfile
import subprocess

from apache.aurora.common.aurora_job_key import AuroraJobKey

logger = logging.getLogger("tornado.application")

DEFAULT_AURORA_CMD      = "/home/mkrastev/projects/Mesos/incubator-aurora.git/dist/aurora_client.pex"
AURORA_SUCCESS_RESPONSE = r"Response from scheduler: OK"

# basic handlers -------------------------------------------------------

class AuroraExternalCommandExecutor():
    """Executor for Aurora commands that spawns Aurora V1 client

    Commands for the Aurora Scheduler are executed by delegating the
    requests to external process to run the Aurora command-line client
    with the appropriate arguments.

    This is safer, albeit slower, execution mode in which the Aurora client
    code is executed by a new process in single-threaded mode.
    """

    def __init__(self, aurora_cmd):
        logger.info("aurora -- external executor created")

        self.aurora_cmd = aurora_cmd

    def make_job_key(self, cluster, role):
        return cluster + "/" + role

    def make_jobspec_file(self, jobspec):
        """Write jobspec string to file"""

        if jobspec is None or len(jobspec) == 0:
            logger.info("job spec not provided")
            return(None)

        logger.info("job spec:")
        lineno = 1
        for l in jobspec.splitlines():
            logger.info("  %3d: %s" % (lineno, l))
            lineno += 1

        file = tempfile.NamedTemporaryFile(suffix=".aurora")
        file.write(jobspec)
        file.flush()

        return(file)

    def pack_instance_list(self, instances):
        """Convert list/array of Aurora instances (shards) into single element"""

        if instances is None or len(instances) == 0:
            logger.info("shard(s) are not specified, that means all instances")
            return(None)
        else:
            packed_list = ",".join(instances)
            logger.info("list of shards: [%s]" % packed_list)
            return(packed_list)

    def is_aurora_command_successful(self, cmd_output):
        """Test for success in the aurora command output

        Over-simplified test for success in the Aurora response that looks
        for specific string to decide if the status of the Aurora command
        was success, if no match is found then it is assumed to be failure.
        """

        cmd_success_status = False
        for s in cmd_output.splitlines():
            logger.info("  > %s" % s)
            if AURORA_SUCCESS_RESPONSE in s:
                cmd_success_status = True

        return(cmd_success_status)

    def list_jobs(self, cluster, role):
        """Method to execute [ aurora list_jobs cluster/role command ]"""

        jobkey = self.make_job_key(cluster, role)
        logger.info("request to list jobs = %s" % jobkey)

        try:
            with open("/dev/null") as dev_null:
                cmd_output = subprocess.check_output(
                                [ self.aurora_cmd, "list_jobs", jobkey ],
                                stderr=dev_null)

                jobs = cmd_output.splitlines()
                if len(jobs) == 0:
                    logger.info("no jobs found for key = %s" % jobkey)
                for s in jobs:
                    logger.info("> %s" % s )

                return(jobkey, jobs, None)

        except subprocess.CalledProcessError as e:
            logger.exception("Failed to list Aurora jobs")
            return(jobkey, [], ["Exception when listing aurora jobs"] + [e.msg])

    def create_job(self, cluster, role, environment, jobname, jobspec):
        """Method to create aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to create => %s", job_key.to_path())

        cmd_output = ""
        try:
            # aurora client requires jobspec be passed as file, no reading from STDIN
            jobspec_file = self.make_jobspec_file(jobspec)
            if jobspec_file is None:
                logger.warning("can not proceed with request, job configuration is missing")
                return(job_key.to_path(), ["Failed to create Aurora job",
                                           "Can not create job configuration object because",
                                           "Job configuration is missing (not provided)!"])

            cmd_args = [job_key.to_path(),jobspec_file.name]
            cmd_output = subprocess.check_output(
                [self.aurora_cmd, "create"] + cmd_args, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            logger.warning("aurora client exit status: %d, details follow" % e.returncode)
            for s in e.output.splitlines():
                logger.warning("> %s" % s)
            logger.warning("----------------------------------------")

            return(job_key.to_path(), ["Error reported by aurora client:"] + e.output.splitlines())

        finally:
            if jobspec_file: jobspec_file.close()


        if self.is_aurora_command_successful(cmd_output):
            logger.info("aurora -- create job successful")
            return(job_key.to_path(), None)
        else:
            logger.warning("aurora -- create job failed")
            return(job_key.to_path(), ["Error reported by aurora client:"] + cmd_output.splitlines())

    def update_job(self, cluster, role, environment, jobname, jobspec, instances=[]):
        """Method to update aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to update = %s", job_key.to_path())

        instances = self.pack_instance_list(instances)
        cmd_output = ""
        try:
            # aurora client requires jobspec be passed as file, no reading from STDIN
            jobspec_file = self.make_jobspec_file(jobspec)
            if jobspec_file is None:
                logger.warning("can not proceed with request, job configuration is missing")
                return(job_key.to_path(), ["Failed to update Aurora job",
                                           "Can not create job configuration object because",
                                           "Job configuration is missing (not provided)!"])

            cmd_args = [job_key.to_path(), jobspec_file.name]
            if instances is not None:
                cmd_args = ["--shards=" + instances] + cmd_args

            cmd_output = subprocess.check_output(
                [self.aurora_cmd, "update"] + cmd_args, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            logger.warning("aurora client exit status: %d, details follow" % e.returncode)
            for s in e.output.splitlines():
                logger.warning("> %s" % s)
            logger.warning("----------------------------------------")

            return(job_key.to_path(), ["Error reported by aurora client:"] + e.output.splitlines())

        finally:
            if jobspec_file: jobspec_file.close()

        if self.is_aurora_command_successful(cmd_output):
            logger.info("aurora -- update job successful")
            return(job_key.to_path(), None)
        else:
            logger.warning("aurora -- update job failed")
            return(job_key.to_path(), ["Error reported by aurora client:"] + cmd_output.splitlines())

    def cancel_update_job(self, cluster, role, environment, jobname, jobspec=None):
        """Method to cancel an update of aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to cancel update of => %s", job_key.to_path())

        cmd_output = ""
        try:
            cmd_args = [job_key.to_path(),]

            # aurora client requires jobspec be passed as file, no reading from STDIN
            jobspec_file = self.make_jobspec_file(jobspec)
            if jobspec_file is not None:
                cmd_args.append(jobspec_file.name)

            cmd_output = subprocess.check_output(
                [self.aurora_cmd, "cancel_update"] + cmd_args, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            logger.warning("aurora client exit status: %d, details follow" % e.returncode)
            for s in e.output.splitlines():
                logger.warning("> %s" % s)
            logger.warning("----------------------------------------")

            return(job_key.to_path(), ["Error reported by aurora client:"] + e.output.splitlines())

        finally:
            if jobspec_file: jobspec_file.close()

        if self.is_aurora_command_successful(cmd_output):
            logger.info("aurora -- cancel update successful")
            return(job_key.to_path(), None)
        else:
            logger.warning("aurora -- cancel update job")
            return(job_key.to_path(), ["Error reported by aurora client:"] + cmd_output.splitlines())

    def delete_job(self, cluster, role, environment, jobname, jobspec=None, instances=[]):
        """Method to delete aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to delete => %s", job_key.to_path())

        instances = self.pack_instance_list(instances)
        cmd_output = ""
        try:
            cmd_args = [job_key.to_path(),]

            # aurora client requires jobspec be passed as file, no reading from STDIN
            jobspec_file = self.make_jobspec_file(jobspec)
            if jobspec_file is not None:
                cmd_args.append(jobspec_file.name)

            if instances is not None:
                cmd = "kill"
                cmd_args = ["--shards=" + instances] + cmd_args
            else:
                cmd = "killall"

            cmd_output = subprocess.check_output(
                [self.aurora_cmd, cmd] + cmd_args, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            logger.warning("aurora client exit status: %d, details follow" % e.returncode)
            for s in e.output.splitlines():
                logger.warning("> %s" % s)
            logger.warning("----------------------------------------")

            return(job_key.to_path(), [], ["Error reported by aurora client"] + e.output.splitlines())

        finally:
            if jobspec_file: jobspec_file.close()

        if self.is_aurora_command_successful(cmd_output):
            logger.info("aurora -- delete job successful")
            return(job_key.to_path(), [job_key.to_path()], None)
        else:
            logger.warning("aurora -- delete job failed")
            return(job_key.to_path(), [], ["Error reported by aurora client"] + cmd_output.splitlines())

    def restart_job(self, cluster, role, environment, jobname, jobspec=None, instances=[]):
        """Method to restart aurora job"""

        job_key = AuroraJobKey(cluster, role, environment, jobname)
        logger.info("request to restart => %s", job_key.to_path())

        instances = self.pack_instance_list(instances)
        cmd_output = ""
        try:
            cmd_args = [job_key.to_path(),]

            # aurora client requires jobspec be passed as file, no reading from STDIN
            jobspec_file = self.make_jobspec_file(jobspec)
            if jobspec_file is not None:
                cmd_args.append(jobspec_file.name)
            if instances is not None:
                cmd_args = ["--shards=" + instances] + cmd_args

            cmd_output = subprocess.check_output(
                [self.aurora_cmd, "restart"] + cmd_args, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            logger.warning("aurora client exit status: %d, details follow" % e.returncode)
            for s in e.output.splitlines():
                logger.warning("> %s" % s)
            logger.warning("----------------------------------------")

            return(job_key.to_path(), ["Error reported by aurora client:"] + e.output.splitlines())

        finally:
            if jobspec_file: jobspec_file.close()

        if self.is_aurora_command_successful(cmd_output):
            logger.info("aurora -- restart job successful")
            return(job_key.to_path(), None)
        else:
            logger.warning("aurora -- restart job failed")
            return(job_key.to_path(), ["Error reported by aurora client:"] + cmd_output.splitlines())

# factory --------------------------------------------------------------

def create(aurora_cmd=DEFAULT_AURORA_CMD):
    """Factory function for executor objects that spanw Aurora command-line client"""

    return AuroraExternalCommandExecutor(aurora_cmd)
