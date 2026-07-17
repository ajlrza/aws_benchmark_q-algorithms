import threading
import boto3
from boto3.s3.transfer import TransferConfig

def RequestDelayerV1(request: object):
    timer = threading.Timer(2.0, request)
    timer.start()

def RequestDelayerV2(request: object):
    timer = threading.Timer(100.0, request)
    timer.start()

def ApplyS3Constraint(max_concurrency=1, disable_multithreading=False):
    config = TransferConfig(
    max_concurrency=max_concurrency,       
    use_threads=disable_multithreading       
    )

def AttachResourcePolicy(user_policy=False, role_policy=False, group_policy=False):
    client = boto3.client("IAM")
    
    for policy in [user_policy, role_policy, group_policy]:

        if policy:

            policy_name = f"{policy=}".split('=')[0]

            slice_policy_name = policy_name.rsplit("_")
            target = slice_policy_name[0].capitalize()

            ask_user_for_name = input(f"Please input the {target}Name")
            ask_user_for_policy_arn = input(f"Please input the PolicyArn")

            args = {f"{target}Name": ask_user_for_name, "PolicyArn": ask_user_for_policy_arn}

            target_policy = f"attach_{policy}"
            boto_attach_policy_method = getattr(client, target_policy)

            attach_policy = boto_attach_policy_method(
                **args
            )

error_codes = {
    # Throttling & Rate Limits 
    "LimitExceededException": "Reached account or resource limits.",
    "Throttling": RequestDelayerV1,
    "ThrottlingException": RequestDelayerV2,
    "RequestLimitExceeded": RequestDelayerV2,
    "ProvisionedThroughputExceededException": "Exceeded provisioned capacity (common in DynamoDB).",
    "TooManyRequestsException": RequestDelayerV2,
    "SlowDown": ApplyS3Constraint,

    # Authentication & Access 
    "AccessDenied": AttachResourcePolicy,
    "AccessDeniedException": "Insufficient permissions to perform this action.",
    "UnrecognizedClientException": "Invalid, unknown, or malformed AWS access keys.",
    "InvalidSignatureException": "Signature mismatch or temporary credentials expired.",
    "ExpiredToken": "The temporary session token has expired.",

    # Resources & Validation 
    "ResourceNotFoundException": "The requested AWS entity or resource does not exist.",
    "NoSuchKey": "The requested S3 object key does not exist.",
    "NoSuchBucket": "The specified S3 bucket does not exist.",
    "ResourceInUseException": "Resource cannot be modified because it is currently busy.",
    "InvalidParameterValue": "Passed an argument with an invalid value or format.",
    "ValidationException": "Input parameters failed to match service schema constraints.",
    "EntityAlreadyExists": "An identical resource or IAM entity already exists.",

    # Server Failures 
    "InternalFailure": "Internal AWS server-side error. Retry the operation.",
    "InternalServerError": "Standard internal service bottleneck or crash.",
    "ServiceUnavailable": "The AWS service is temporarily down or overloaded.",

    # Internal Botocore Exceptions (Client-Side) 
    "ParamValidationError": "Client-side validation failed before sending the request.",
    "NoCredentialsError": "Boto3 could not locate AWS credentials locally.",
    "NoRegionError": "No AWS region was specified in your configuration.",
    "EndpointConnectionError": "Network failure or unable to resolve AWS endpoint URL.",
    "ReadTimeoutError": "The AWS server took too long to return data.",
    "ConnectionError": "General network layer disconnect occurred.",
    "ConfigParseError": "Your local AWS config or credentials file is malformed."
}
