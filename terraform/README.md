# OmniRoute Terraform

This directory contains the AWS infrastructure foundation for OmniRoute Cloud.

The Terraform configuration currently defines:

- Amazon ECR repository
- Amazon ECS cluster
- ECS Fargate task definition
- optional ECS Fargate service
- ECS task execution IAM role
- ECS application IAM role
- CloudWatch log group
- encrypted DynamoDB request table
- optional VPC
- two public subnets
- Internet Gateway
- public route table
- Application Load Balancer
- ALB security group
- ECS security group
- ALB target group
- HTTP listener

## Safety

Infrastructure creation is intentionally disabled by default where practical.

The following variables default to `false`:

```text
create_network
create_alb
create_ecs_service