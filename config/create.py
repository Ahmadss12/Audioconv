import boto3
from s3 import *
from dynamodb import *
from instance import *
from keypair import *
from security_group import *
from ip_elastic import *



def main():
    #s3 session
    """Exercise BucketWrapper."""
    s3 = boto3.resource('s3')
    bucket_name = 'converter12'
    bucket = s3.Bucket(bucket_name)
    wrapper = BucketWrapper(bucket)
    wrapper.create()

    wrapper.create_folder('video')
    wrapper.create_folder('audio')


    # Define and apply CORS rules
    cors_rules = [{
        'AllowedOrigins': ['*'],
        'AllowedMethods': ['GET', 'PUT'],
        'AllowedHeaders': ['*']
    }]
    wrapper.put_cors(cors_rules)

    # Disable public access block
    wrapper.disable_public_access_block()


    #security_group session
    ec2_resource = boto3.resource('ec2')

    security_group_wrapper = SecurityGroupWrapper(ec2_resource)
    group_name = 'MySecurityGroup122'
    group_description = 'My security group description'
    security_group = security_group_wrapper.create(group_name, group_description)
    print(f"Created new security group {security_group.group_name} with ID {security_group.id}.")

    #keypair session
    wrapper = KeyPairWrapper.from_resource()
    key_name = 'MyKeyPair'
    key_pair = wrapper.create(key_name)
    print(f"Created new key pair {key_pair.name} with fingerprint {key_pair.key_fingerprint}.")

    #instance session
    wrapper = InstanceWrapper.from_resource()
    image_id = 'ami-053b0d53c279acc90'
    instance_type = 't2.micro'
    key_pair_name = 'MyKeyPair'
    security_group_ids = [security_group.id]
    instance = wrapper.create(image_id, instance_type, key_pair_name, security_group_ids)
    print(f"Created new EC2 instance {instance.id} with public IP {instance.public_ip_address}.")

    #ip_elastic session

    elastic_ip_wrapper = ElasticIpWrapper(ec2_resource)
    elastic_ip = elastic_ip_wrapper.allocate()
    print(f"Allocated new Elastic IP {elastic_ip.public_ip} with ID {elastic_ip.allocation_id}.")

    # Replace with your instance ID
    instance_id = instance.id
    instance = ec2_resource.Instance(instance_id)
    response = elastic_ip_wrapper.associate(instance)
    print(f"Associated Elastic IP {elastic_ip.public_ip} with instance {instance.id}. Association ID: {response['AssociationId']}")

    
    #dynamodb session
    dynamodb_wrapper = DynamoDBWrapper.from_client()

    # Create a new table
    table_name = 'converter12'
    attribute_definitions = [
        {
            'AttributeName': 'audio_filename',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 's3_file_name',
            'AttributeType': 'S'
        }
    ]
    key_schema = [
        {
            'AttributeName': 'audio_filename',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 's3_file_name',
            'KeyType': 'RANGE'
        }
    ]
    provisioned_throughput = {
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1
    }
    table_description = dynamodb_wrapper.create_table(
        table_name, attribute_definitions, key_schema, provisioned_throughput)
    print(f"Created new table {table_description['TableName']} with Arn {table_description['TableArn']}")



if __name__ == '__main__':
    main()