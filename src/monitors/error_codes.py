import threading

def RequestDelayerV1(request: object):
    timer = threading.Timer(2.0, request)
    timer.start()

def RequestDelayerV2(request: object):
    timer = threading.Timer(100.0, request)
    timer.start()


error_codes = {
    # --- Throttling & Rate Limits ---
    "LimitExceededException": "Reached account or resource limits.",
    "Throttling": RequestDelayerV1,
    "ThrottlingException": RequestDelayerV2,
    "RequestLimitExceeded": RequestDelayerV2,
    "ProvisionedThroughputExceededException": "Exceeded provisioned capacity (common in DynamoDB).",
    "TooManyRequestsException": "API gateway or service-specific rate limit hit.",
    "SlowDown": "S3 or the storage service requires you to reduce request frequency.",

    # --- Authentication & Access ---
    "AccessDenied": "Explicitly blocked by IAM or resource policies.",
    "AccessDeniedException": "Insufficient permissions to perform this action.",
    "UnrecognizedClientException": "Invalid, unknown, or malformed AWS access keys.",
    "InvalidSignatureException": "Signature mismatch or temporary credentials expired.",
    "ExpiredToken": "The temporary session token has expired.",

    # --- Resources & Validation ---
    "ResourceNotFoundException": "The requested AWS entity or resource does not exist.",
    "NoSuchKey": "The requested S3 object key does not exist.",
    "NoSuchBucket": "The specified S3 bucket does not exist.",
    "ResourceInUseException": "Resource cannot be modified because it is currently busy.",
    "InvalidParameterValue": "Passed an argument with an invalid value or format.",
    "ValidationException": "Input parameters failed to match service schema constraints.",
    "EntityAlreadyExists": "An identical resource or IAM entity already exists.",

    # --- Server Failures ---
    "InternalFailure": "Internal AWS server-side error. Retry the operation.",
    "InternalServerError": "Standard internal service bottleneck or crash.",
    "ServiceUnavailable": "The AWS service is temporarily down or overloaded.",

    # --- Internal Botocore Exceptions (Client-Side) ---
    "ParamValidationError": "Client-side validation failed before sending the request.",
    "NoCredentialsError": "Boto3 could not locate AWS credentials locally.",
    "NoRegionError": "No AWS region was specified in your configuration.",
    "EndpointConnectionError": "Network failure or unable to resolve AWS endpoint URL.",
    "ReadTimeoutError": "The AWS server took too long to return data.",
    "ConnectionError": "General network layer disconnect occurred.",
    "ConfigParseError": "Your local AWS config or credentials file is malformed."
}
