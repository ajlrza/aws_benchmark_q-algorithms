import boto3

ec2_client = boto3.client("ec2")

test_instance = ec2_client.run_instances(
    ImageId='ami-0123456789abcdef0',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    MetadataOptions={
        'HttpTokens': 'required',       
        'HttpEndpoint': 'enabled',     
        'HttpPutResponseHopLimit': 2   
    }
)