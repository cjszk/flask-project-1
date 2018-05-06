####################################################################
######          Copyright (c)  2015-2017 OpenSCG          ##########
####################################################################
import os
from salt.cloud import CloudClient
from salt.client import LocalClient
import json
import sys

from util import get_credentials_by_type

PGC_HOME = os.getenv("PGC_HOME", "")
devops_lib_path = os.path.join(PGC_HOME, "pgdevops", "lib")
if os.path.exists(devops_lib_path):
    if devops_lib_path not in sys.path:
        sys.path.append(devops_lib_path)
    
cloud_file = os.path.join(PGC_HOME, "data", "etc", "cloud")

drivers = {
  'aws': 'ec2'
}

log_file = os.path.join(PGC_HOME, "data", "logs", "salt", "salt.log")
pki_dir = os.path.join(PGC_HOME, "data", "etc", "minion")


class ComputeNodes(object):

    def __init__(self, cloud="aws"):
        cred_json = get_credentials_by_type(cloud_type=cloud)
        if len(cred_json) > 0:
            credentials = cred_json[0]['credentials'] if 'credentials' in cred_json[0] else {}
        else:
            raise IOError("please add credentials for %s."%cloud)
        if cloud == "aws":
            if not set(("access_key_id", "secret_access_key")).issubset(credentials):
                raise IOError("access_key_id and secret_access_key  are required in credentials for %s." % cloud)
            provider_dict = {}
            provider_dict['driver'] = "ec2"
            provider_dict['id'] = str(credentials["access_key_id"])
            provider_dict['key'] = str(credentials["secret_access_key"])
            self.provider_opts = provider_dict
        self.provider = "bigsql-provider"
        self.cloud = cloud
        self.header_keys = ['region', 'name', 'type', 'public_ips', 'private_ips', 'state']
        self.header_titles = ['Region', 'Name', 'Instance Type', 'Public Ips', 'Private Ips', 'state']

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
        if self.cloud=="aws":
            if region:
                self.provider_opts['location'] = region
            opts['providers'] = {
                self.provider: {
                    'ec2': self.provider_opts
                }
            }
        return opts

    def get_aws_instance_info(self, vm_obj):
        # TODO: Need to implement getting the addtional info of aws
        vm = {}
        return vm

    def get_list(self, filter_params={}):
        vms = []
        driver_name = drivers.get(self.cloud)
        p_instance = filter_params.get("instance", "")
        opts = self.get_opts()
        cloud_client = CloudClient(opts=opts)
        kwargs = dict()
        if 'region' in filter_params and self.cloud in ("aws"):
            kwargs['location'] = filter_params['region']
        if p_instance:
            list_nodes = cloud_client.action(fun="show_instance", instance=p_instance, kwargs = kwargs)
        else:
            list_nodes = cloud_client.action(fun="list_nodes_full", provider=self.provider, kwargs = kwargs)

        providers_nodes_list = list_nodes.get(self.provider)

        if providers_nodes_list and providers_nodes_list.get(driver_name):
            nodes = providers_nodes_list.get(driver_name)
            for name in nodes:
                vm_obj = nodes.get(name)
                vm = {}
                vm['id'] = vm_obj.get("id")
                vm['name'] = vm_obj.get("name")
                vm['region'] = vm_obj.get("location")
                vm['type'] = vm_obj.get("size")
                vm['state'] = vm_obj.get("state")
                vm['public_ips'] = vm_obj.get("public_ips")
                vm['private_ips'] = vm_obj.get("private_ips")
                vms.append(vm)
        return vms

    def create_node(self, create_params):
      from salt.log import setup_logfile_logger
      setup_logfile_logger(log_file, log_level="debug")
      result = {}
      if self.cloud=="aws":
        result = self.create_aws_vm(create_params=create_params)
      return result

    def create_aws_vm(self, create_params):
        response = {
            'state' : 'complete',
            'msg' : 'Instance created successfully.'
        }
        opts = self.get_opts()
        cloud_client = CloudClient(opts=opts)
        for params in create_params:
            computer_name = params["computer_name"]
            cpus = params.get("num_cpus",1)

            result = dict()
            args = {
                "provider":self.provider,
                "names":[computer_name],
                "num_cpus":cpus,
                "public_ip":True,
                "securitygroup":params["security_group"],
                "keyname":params["keyname"],
                "size":params["instance_type"],
                "image":params["image_id"],
                "deploy":False
            }

            result = cloud_client.create(**args)
            if computer_name in result and len(result[computer_name]) == 1 and 'Error' in result[computer_name]:
                response['state'] = 'failed'
                response['msg'] = result[computer_name]['Error']
                return response
            return response

    def storage_accounts(self, group):
        result = []
        opts = self.get_opts(group=group)
        cloud_client = CloudClient(opts=opts)
        driver_name = drivers.get(self.cloud)
        response = cloud_client.action(fun="list_storage_accounts", provider=self.provider)
        accounts_response = response.get(self.provider)

        if accounts_response.get(driver_name):
            accounts = accounts_response.get(driver_name)
            for account in accounts:
                storage_account = accounts.get(account)
                resp = {}
                resp['name'] = storage_account.get('name')
                resp['location'] = storage_account.get('location')
                result.append(resp)
        return result

    def get_instance_types(self, region):
        result = []
        opts = self.get_opts(region=region)
        cloud_client = CloudClient(opts=opts)
        driver_name = drivers.get(self.cloud)
        response = cloud_client.action(fun="avail_sizes", provider=self.provider)
        sizes_response = response.get(self.provider)
        if sizes_response.get(driver_name):
            sizes = sizes_response.get(driver_name)
            for size in sizes:
                result.append(sizes[size])
        return result

    def list_networks(self, group):
        result = []
        opts = self.get_opts(group=group)
        cloud_client = CloudClient(opts=opts)
        driver_name = drivers.get(self.cloud)
        response = cloud_client.action(fun="list_networks", provider=self.provider, kwargs={'group':group})
        nw_response = response.get(self.provider)
        if nw_response.get(driver_name):
            nws = nw_response.get(driver_name)
            for nw in nws:
                resp = {}
                resp['name'] = nw
                result.append(resp)
        return result

    def subnet_groups(self, res_group=None):
        result = []
        opts = self.get_opts()
        cloud_client = CloudClient(opts=opts)
        driver_name = drivers.get(self.cloud)
        response = cloud_client.action(fun="list_networks", provider=self.provider, kwargs={'group':res_group})
        network_response = response.get(self.provider)
        if network_response.get(driver_name):
            networks = network_response.get(driver_name)
            for network in networks:
                nw_response = {}
                nw_response['vpc'] = network
                #nw_response['subnet_group'] = []
                for subnet in networks[network].get('subnets'):
                    nw_response['subnet_group'] = subnet
                result.append(nw_response)
        return result

    def key_pairs(self, region = None):
        result = []
        opts = self.get_opts(region = region)
        cloud_client = CloudClient(opts=opts)
        driver_name = drivers.get(self.cloud)
        res = cloud_client.action(fun='describe_keypairs',provider = self.provider)
        response = res.get(self.provider)
        if response.get(driver_name):
            keys = response.get(driver_name)
            for key in keys[0]:
                result.append(key)
        return result

    def security_groups(self, region = None):
        result = []
        opts = self.get_opts(region = region)
        cloud_client = CloudClient(opts=opts)
        driver_name = drivers.get(self.cloud)
        res = cloud_client.action(fun='describe_securitygroups',provider = self.provider)
        response = res.get(self.provider)
        if response.get(driver_name):
            groups = response.get(driver_name)
            for grp in groups:
                result.append(grp)
        return result
