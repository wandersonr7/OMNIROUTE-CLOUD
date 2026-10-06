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
  description = "Create the ECS service after networking is supplied"
  type        = bool
  default     = false
}

variable "ecs_subnet_ids" {
  description = "Subnet IDs used by the ECS Fargate service"
  type        = list(string)
  default     = []
}

variable "ecs_security_group_ids" {
  description = "Security group IDs used by the ECS Fargate service"
  type        = list(string)
  default     = []
}

variable "ecs_assign_public_ip" {
  description = "Assign a public IP to ECS tasks"
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