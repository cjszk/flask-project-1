import os, sys

from salt.cloud import CloudClient
from salt.client import LocalClient

PGC_HOME = os.getenv("PGC_HOME", "")
devops_lib_path = os.path.join(PGC_HOME, "pgdevops", "lib")
if os.path.exists(devops_lib_path):
    if devops_lib_path not in sys.path:
        sys.path.append(devops_lib_path)

cloud_file = os.path.join(PGC_HOME, "data", "etc", "cloud")
log_file = os.path.join(PGC_HOME, "data", "logs", "salt", "salt.log")
pki_dir = os.path.join(PGC_HOME, "data", "etc", "minion")


class TestConnection(object):

    def __init__(self, cloud=None, credentials=None):
        self.cloud = cloud
        self.credentials = credentials
        self.provider = "bigsql-provider"

    def get_opts(self,region=None, group=None):
        if not os.path.exists("/tmp/salt/"):
            os.mkdir("/tmp/salt/")
        if not os.path.exists("/tmp/salt/cache"):
            os.mkdir("/tmp/salt/cache")
        if not os.path.exists("/tmp/salt/run"):
            os.mkdir("/tmp/salt/run")
        if not os.path.exists("/tmp/salt/run/master"):
            os.mkdir("/tmp/salt/run/master")
        mopts = {}
        mopts["cachedir"] = "/tmp/salt/cache"
        mopts["sock_dir"] = "/tmp/salt/run/master"
        mopts["transport"] = "zeromq"
        mopts["extension_modules"] = ""
        mopts["file_roots"] = {}
        lc = LocalClient(mopts=mopts)
        opts = lc.opts
        opts["parallel"] = True
        opts["pki_dir"] = pki_dir
        opts["extension_modules"] = ""
        opts["cachedir"] = "/tmp/salt/cloud"
        opts['log_level'] = "debug"
        opts['log_level_logfile'] = "debug"
        opts["log_file"] = log_file
        opts["update_cachedir"] = False
        opts["log_file"] = log_file
        opts["log_level_logfile"] = "debug"
        opts["log_file"] = log_file

        opts['providers'] = {}

        return opts

    def aws(self):
        response = {
            "code": 0,
            "msg": "Valid Credentials"
        }
        import boto3
        available_rds_regions = boto3.session.Session().get_available_regions("rds")
        try:
            boto_client = boto3.client('rds', aws_access_key_id=self.credentials['aws_access_key_id'],
                                       aws_secret_access_key=self.credentials["aws_secret_access_key"],
                                       region_name=available_rds_regions[0])
            boto_client.describe_db_instances()
        except Exception as ex:
            response["code"] = 1
            response["msg"] = "Invalid Credentials"
        return response
