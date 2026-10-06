output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_task_definition_arn" {
  value = aws_ecs_task_definition.app.arn
}

output "ecs_task_execution_role_arn" {
  value = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}

output "ecs_service_name" {
  value = var.create_ecs_service ? aws_ecs_service.app[0].name : null
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.requests.name
}

output "vpc_id" {
  value = var.create_network ? aws_vpc.main[0].id : null
}

output "public_subnet_ids" {
  value = var.create_network ? [
    aws_subnet.public_a[0].id,
    aws_subnet.public_b[0].id,
  ] : []
}

output "alb_dns_name" {
  value = var.create_alb ? aws_lb.app[0].dns_name : null
}