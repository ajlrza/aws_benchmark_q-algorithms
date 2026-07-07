terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

resource "random_pet" "hello" {
  length    = 2
  separator = "-"
}

output "hello_world" {
  value = "Hello, world from Terraform!"
}
