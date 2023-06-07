import boto3
import logging
from botocore.exceptions import ClientError
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityGroupWrapper:
    """Encapsulates Amazon Elastic Compute Cloud (Amazon EC2) security group actions."""
    def __init__(self, ec2_resource, security_group=None):
        """
        :param ec2_resource: A Boto3 Amazon EC2 resource. This high-level resource
                             is used to create additional high-level objects
                             that wrap low-level Amazon EC2 service actions.
        :param security_group: A Boto3 SecurityGroup object. This is a high-level object that
                               wraps security group actions.
        """
        self.ec2_resource = ec2_resource
        self.security_group = security_group

    @classmethod
    def from_resource(cls):
        ec2_resource = boto3.resource('ec2')
        return cls(ec2_resource)

    def create(self, group_name, group_description):
        """
        Creates a security group in the default virtual private cloud (VPC) of the
        current account.

        :param group_name: The name of the security group to create.
        :param group_description: The description of the security group to create.
        :return: A Boto3 SecurityGroup object that represents the newly created security group.
        """
        try:
            self.security_group = self.ec2_resource.create_security_group(
                GroupName=group_name, Description=group_description)
            
            # Define the inbound rules
            self.security_group.authorize_ingress(
                IpProtocol='tcp',
                FromPort=22,
                ToPort=22,
                CidrIp='0.0.0.0/0'  # Allow SSH from any IP address
            )
            self.security_group.authorize_ingress(
                IpProtocol='tcp',
                FromPort=80,
                ToPort=80,
                CidrIp='0.0.0.0/0'  # Allow HTTP from any IP address
            )
            self.security_group.authorize_ingress(
                IpProtocol='tcp',
                FromPort=443,
                ToPort=443,
                CidrIp='0.0.0.0/0'  # Allow HTTPS from any IP address
            )
            self.security_group.authorize_ingress(
                IpProtocol='tcp',
                FromPort=8080,
                ToPort=8080,
                CidrIp='0.0.0.0/0'  # Allow custom port 8080 from any IP address
            )
            
        except ClientError as err:
            logger.error(
                "Couldn't create security group %s. Here's why: %s: %s", group_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return self.security_group
