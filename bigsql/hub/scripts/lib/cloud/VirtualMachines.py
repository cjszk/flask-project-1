####################################################################
#########      Copyright (c) 2016-2017 BigSQL           ############
####################################################################
from common import convert_tz, get_obj_value, convert
from cloud_mapping import vm_list_dict
import datetime


class VirtualMachine(object):

    def __init__(self):
        self.id = ""
        self.name = ""
        self.type = ""
        self.region = ""
        self.state = ""
        self.public_ips = ""
        self.private_ips = ""

    def get_common_attr(self, vm_object):
        self.id = vm_object.get("id")
        self.name = vm_object.get("name")
        self.region = vm_object.get("location")
        self.type = vm_object.get("size")
        self.state = vm_object.get("state")
        self.public_ips = vm_object.get("public_ips")
        self.private_ips = vm_object.get("private_ips")


class AwsVM(VirtualMachine):

    def __init__(self, vm_object, info=False):
        VirtualMachine.__init__(self)
        self.type = vm_object.get('InstanceType')
        self.id = vm_object.get("InstanceId")
        self.name = ""
        self.private_ips = vm_object.get("PrivateIpAddress")
        self.public_ips = vm_object.get("PublicIpAddress")
        self.state = vm_object.get("State").get("Name")
        if vm_object.get('Tags'):
            for tag in vm_object.get('Tags'):
                if tag['Key'] == "Name":
                    self.name = tag['Value']
                    break

    def set_extra_info(self, vm_object, cloud_type="aws"):
        for k in vm_list_dict.keys():
            if hasattr(self, k):
                continue
            param = vm_list_dict.get(k)
            param_value = ""
            if param.get(cloud_type):
                cloud_keys = param.get(cloud_type)['key']
                if len(cloud_keys)>0:
                    param_value = get_obj_value(vm_object, cloud_keys)
                    if isinstance(param_value, datetime.datetime):
                        try:
                            param_value = convert_tz(str(param_value))
                        except Exception as e:
                            param_value = ""
                    if k == "security_groups":
                        new_list_value = []
                        for p in param_value:
                            new_param_dict = {}
                            new_param_dict["group_name"] = p.get("GroupName")
                            new_param_dict["group_id"] = p.get("GroupId")
                            new_list_value.append(new_param_dict)
                        param_value=new_list_value
                    if k == "tags":
                        new_list_value = []
                        for p in param_value:
                            new_list_value.append(p.get("Value"))
                        param_value = new_list_value

                if not hasattr(self, k):
                    setattr(self, k, param_value)

