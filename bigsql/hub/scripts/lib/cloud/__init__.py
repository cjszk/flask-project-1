####################################################################
#########      Copyright (c) 2016-2018 BigSQL           ############
####################################################################

import os
import sys

devops_lib_path = os.path.join(os.getenv("PGC_HOME"), "pgdevops", "lib")
if os.path.exists(devops_lib_path):
    if devops_lib_path not in sys.path:
        sys.path.append(devops_lib_path)

from awscloud import AwsConnection

class_mapping = {
    'aws': AwsConnection
}


class CloudConnection(object):

    def __init__(self, cloud=None):
        self.cloud = cloud
        pass

    def get_client(self, instance_type=None, region=None):
        if region:
            return class_mapping.get(self.cloud)(instance_type=instance_type, region=region)
        else:
            return class_mapping.get(self.cloud)(instance_type=instance_type)

