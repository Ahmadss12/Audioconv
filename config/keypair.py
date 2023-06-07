import boto3
import logging
from botocore.exceptions import ClientError
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class KeyPairWrapper:
    """Encapsulates Amazon Elastic Compute Cloud (Amazon EC2) key pair actions."""
    def __init__(self, ec2_resource, key_pair=None):
        """
        :param ec2_resource: A Boto3 Amazon EC2 resource. This high-level resource
                             is used to create additional high-level objects
                             that wrap low-level Amazon EC2 service actions.
        :param key_pair: A Boto3 KeyPair object. This is a high-level object that
                         wraps key pair actions.
        """
        self.ec2_resource = ec2_resource
        self.key_pair = key_pair

    @classmethod
    def from_resource(cls):
        ec2_resource = boto3.resource('ec2')
        return cls(ec2_resource)

    def create(self, key_name):
        """
        Creates a key pair that can be used to securely connect to an EC2 instance.
        The returned key pair contains private key information that cannot be retrieved
        again. The private key data is stored as a .pem file.

        :param key_name: The name of the key pair to create.
        :return: A Boto3 KeyPair object that represents the newly created key pair.
        """
        try:
            self.key_pair = self.ec2_resource.create_key_pair(KeyName=key_name)
            with open(f'{key_name}.pem', 'w') as key_file:
                key_file.write(self.key_pair.key_material)
            os.chmod(f'{key_name}.pem', 0o400)
        except ClientError as err:
            logger.error(
                "Couldn't create key %s. Here's why: %s: %s", key_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return self.key_pair