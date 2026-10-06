variable "aws_region" {
  description = "AWS region for OmniRoute resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Container image URI for OmniRoute. Empty uses the project ECR repository with the latest tag."
  type        = string
  default     = ""
}

variable "container_port" {
  description = "Port exposed by the OmniRoute container"
  type        = number
  default     = 8000
}

variable "ecs_task_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 256
}

variable "ecs_task_memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "create_ecs_service" {
  description = "Create the ECS Fargate service"
  type        = bool
  default     = false
}

variable "create_network" {
  description = "Create the OmniRoute VPC and public networking"
  type        = bool
  default     = false
}

variable "create_alb" {
  description = "Create the Application Load Balancer"
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "CIDR block for the OmniRoute VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet A"
  type        = string
  default     = "10.20.1.0/24"
}

variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet B"
  type        = string
  default     = "10.20.2.0/24"
}

variable "ecs_subnet_ids" {
  description = "Existing subnet IDs used by ECS when create_network is false"
  type        = list(string)
  default     = []
}

variable "ecs_security_group_ids" {
  description = "Existing security group IDs used by ECS when create_network is false"
  type        = list(string)
  default     = []
}

variable "ecs_assign_public_ip" {
  description = "Assign a public IP to ECS tasks when using external networking"
  type        = bool
  default     = false
}

variable "provider_timeout_seconds" {
  description = "Timeout for upstream AI provider requests"
  type        = number
  default     = 30
}

variable "provider_max_retries" {
  description = "Maximum retries for upstream provider requests"
  type        = number
  default     = 2
}

variable "provider_retry_backoff_seconds" {
  description = "Initial retry backoff duration"
  type        = number
  default     = 0.5
}

variable "circuit_breaker_failure_threshold" {
  description = "Provider failures required before opening the circuit breaker"
  type        = number
  default     = 3
}

variable "circuit_breaker_recovery_timeout_seconds" {
  description = "Seconds before an open provider circuit may recover"
  type        = number
  default     = 30
}