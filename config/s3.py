import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BucketWrapper:
    """Encapsulates S3 bucket actions."""
    def __init__(self, bucket):
        """
        :param bucket: A Boto3 Bucket resource. This is a high-level resource in Boto3
                    that wraps bucket actions in a class-like structure.
        """
        self.bucket = bucket
        self.name = bucket.name

    def create(self, region_override=None):
        """
        Create an Amazon S3 bucket in the default Region for the account or in the
        specified Region.

        :param region_override: The Region in which to create the bucket. If this is
                                not specified, the Region configured in your shared
                                credentials is used.
        """
        if region_override is not None:
            region = region_override
        else:
            region = self.bucket.meta.client.meta.region_name
        try:
            if region == 'us-east-1':
                self.bucket.create()
            else:
                self.bucket.create(
                    CreateBucketConfiguration={'LocationConstraint': region})

            self.bucket.wait_until_exists()
            logger.info(
                "Created bucket '%s' in region=%s", self.bucket.name, region)
        except ClientError as error:
            logger.exception(
                "Couldn't create bucket named '%s' in region=%s.",
                self.bucket.name, region)
            raise error
    
    def create_folder(self, folder_name):
        """
        Create a "folder" in the bucket by uploading an empty object with a key that
        ends with a '/'.

        :param folder_name: The name of the "folder" to create.
        """
        try:
            self.bucket.put_object(Key=f'{folder_name}/')
            logger.info("Created 'folder' named '%s' in bucket '%s'.", folder_name, self.bucket.name)
        except ClientError:
            logger.exception("Couldn't create 'folder' named '%s' in bucket '%s'.", folder_name, self.bucket.name)
            raise


    def put_cors(self, cors_rules):
        """
        Apply CORS rules to the bucket. CORS rules specify the HTTP actions that are
        allowed from other domains.

        :param cors_rules: The CORS rules to apply.
        """
        try:
            self.bucket.Cors().put(CORSConfiguration={'CORSRules': cors_rules})
            logger.info(
                "Put CORS rules %s for bucket '%s'.", cors_rules, self.bucket.name)
        except ClientError:
            logger.exception("Couldn't put CORS rules for bucket %s.", self.bucket.name)
            raise
    
    def disable_public_access_block(self):
        """
        Disable all public access block settings for the bucket.
    """
        try:
            self.bucket.meta.client.put_public_access_block(
                Bucket=self.bucket.name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            logger.info("Disabled public access block for bucket '%s'.", self.bucket.name)
        except ClientError:
            logger.exception("Couldn't disable public access block for bucket %s.", self.bucket.name)
            raise