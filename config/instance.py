import boto3
import logging
from botocore.exceptions import ClientError
import os
from keypair import KeyPairWrapper
from security_group import SecurityGroupWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstanceWrapper:
    """Encapsulates Amazon Elastic Compute Cloud (Amazon EC2) instance actions."""
    def __init__(self, ec2_resource, instance=None):
        """
        :param ec2_resource: A Boto3 Amazon EC2 resource. This high-level resource
        is used to create additional high-level objects
        that wrap low-level Amazon EC2 service actions.
        :param instance: A Boto3 Instance object. This is a high-level object that
                         wraps instance actions.
        """
        self.ec2_resource = ec2_resource
        self.instance = instance

    @classmethod
    def from_resource(cls):
        ec2_resource = boto3.resource('ec2')
        return cls(ec2_resource)
    
    def create(
            self, image_id, instance_type, key_pair_name, security_group_ids=None):
        """
        Creates a new EC2 instance. The instance starts immediately after
        it is created.

        The instance is created in the default VPC of the current account.

        :param image_id: The ID of the Amazon Machine Image (AMI) that defines attributes of the instance that is created. The AMI defines things like the kind of operating system and the type of storage used by the instance.
        :param instance_type: The type of instance to create, such as 't2.micro'. The instance type defines things like the number of CPUs and the amount of memory.
        :param key_pair_name: The name of the key pair that is used to secure connections to the instance.
        :param security_group_ids: A list of security group IDs that are used to grant access to the instance. When no security groups are specified, the default security group of the VPC is used.
        :return: A Boto3 Instance object that represents the newly created instance.
        """
        try:
            instance_params = {
                'ImageId': image_id,
                'InstanceType': instance_type,
                'KeyName': key_pair_name,
                'MinCount': 1,
                'MaxCount': 1
            }
            if security_group_ids is not None:
                instance_params['SecurityGroupIds'] = security_group_ids
            self.instance = self.ec2_resource.create_instances(**instance_params)[0]
            self.instance.wait_until_running()
            self.instance.load()
        except ClientError as err:
            logger.error(
                "Couldn't create instance with image %s, instance type %s, and key %s. "
                "Here's why: %s: %s", image_id, instance_type, key_pair_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return self.instance