import boto3
from botocore.exceptions import ClientError
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamoDBWrapper:
    """Encapsulates Amazon DynamoDB operations."""
    def __init__(self, dynamodb_client):
        """
        :param dynamodb_client: A Boto3 Amazon DynamoDB client.
        """
        self.dynamodb_client = dynamodb_client

    @classmethod
    def from_client(cls):
        dynamodb_client = boto3.client('dynamodb')
        return cls(dynamodb_client)

    def create_table(self, table_name, attribute_definitions, key_schema,
                     provisioned_throughput):
        """
        Creates an Amazon DynamoDB table.

        :param table_name: The name of the table to create.
        :param attribute_definitions: A list of dictionaries that define the attributes
                                      of the table.
        :param key_schema: A list of dictionaries that define the key schema of the table.
        :param provisioned_throughput: A dictionary that defines the provisioned throughput
                                       of the table.
        :return: The newly created table description.
        """
        try:
            response = self.dynamodb_client.create_table(
                TableName=table_name,
                AttributeDefinitions=attribute_definitions,
                KeySchema=key_schema,
                ProvisionedThroughput=provisioned_throughput
            )
            table_description = response['TableDescription']
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return table_description
