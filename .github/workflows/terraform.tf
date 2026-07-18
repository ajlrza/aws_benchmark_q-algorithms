terraform { 
  required_providers { 
    aws = { 
      source  = "hashicorp/aws" 
      version = "~> 5.0" 
    } 
  } 
} 

provider "aws" { 
  region = "us-east-1" 
} 

# 1. EC2 Instance
resource "aws_instance" "experiment_instance" { 
  ami           = "ami-0c7217cdde317cfec" # Sample AMI
  instance_type = "t2.micro" 
  
  tags = { 
    Environment = "Development" 
  } 
} 

output "instance_id" {
  value       = aws_instance.experiment_instance.id
  description = "The ID of the EC2 instance for resource attachments."
}

output "instance_public_ip" {
  value       = aws_instance.experiment_instance.public_ip
  description = "The public IP address for SSH access and verification."
}

output "instance_private_ip" {
  value       = aws_instance.experiment_instance.private_ip
  description = "The internal IP address for private network routing."
}

# 2. S3 Bucket
resource "aws_s3_bucket" "experiment_bucket" {
  # Bucket names must use hyphens, not underscores, and be globally unique.
  # Consider adding a random string or your account ID to the end of this name.
  bucket = "my-quantum-experiment-bucket-12345" 

  tags = {
    Name        = "Experiment Bucket"
    Environment = "Development"
  }
}

output "s3_bucket_domain" { 
  # Fixed reference to the correct bucket resource
  value       = aws_s3_bucket.experiment_bucket.bucket_domain_name 
  description = "AWS S3 bucket domain name for the experiment" 
} 

# 3. IAM Role for AWS Braket
resource "aws_iam_role" "braket_role" { 
  name = "braket_role" 
  
  assume_role_policy = jsonencode({ 
    Version = "2012-10-17" 
    Statement = [ 
      { 
        Action    = "sts:AssumeRole" 
        Effect    = "Allow" 
        Principal = { 
          # Fixed the malformed service principal
          Service = "braket.amazonaws.com" 
        } 
      } 
    ] 
  }) 

  tags = { 
    Environment = "Development" 
  } 
} 

output "braket_role_arn" { 
  value       = aws_iam_role.braket_role.arn 
  description = "AWS Braket role ARN" 
}
