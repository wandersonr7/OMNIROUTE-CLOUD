data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.name}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
}

data "aws_iam_policy_document" "ecs_task" {
  statement {
    sid    = "DynamoDBRequests"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
    ]

    resources = [
      aws_dynamodb_table.requests.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ecs_task" {
  name   = "${local.name}-task-policy"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task.json
}

locals {
  container_image = (
    var.container_image != ""
    ? var.container_image
    : "${aws_ecr_repository.app.repository_url}:latest"
  )

  ecs_subnet_ids = (
    var.create_network
    ? [
      aws_subnet.public_a[0].id,
      aws_subnet.public_b[0].id,
    ]
    : var.ecs_subnet_ids
  )

  ecs_security_group_ids = (
    var.create_network
    ? [aws_security_group.ecs[0].id]
    : var.ecs_security_group_ids
  )

  ecs_assign_public_ip = (
    var.create_network
    ? true
    : var.ecs_assign_public_ip
  )
}

resource "aws_ecs_task_definition" "app" {
  family                   = local.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = var.ecs_task_cpu
  memory = var.ecs_task_memory

  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "omniroute"
      image     = local.container_image
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "OMNIROUTE_DEFAULT_PROVIDER"
          value = "mock"
        },
        {
          name  = "OMNIROUTE_PROVIDER_TIMEOUT_SECONDS"
          value = tostring(var.provider_timeout_seconds)
        },
        {
          name  = "OMNIROUTE_PROVIDER_MAX_RETRIES"
          value = tostring(var.provider_max_retries)
        },
        {
          name  = "OMNIROUTE_PROVIDER_RETRY_BACKOFF_SECONDS"
          value = tostring(var.provider_retry_backoff_seconds)
        },
        {
          name  = "OMNIROUTE_CIRCUIT_BREAKER_FAILURE_THRESHOLD"
          value = tostring(var.circuit_breaker_failure_threshold)
        },
        {
          name  = "OMNIROUTE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS"
          value = tostring(var.circuit_breaker_recovery_timeout_seconds)
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "omniroute"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${var.container_port}/health', timeout=2)\" || exit 1"
        ]

        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  count = var.create_ecs_service ? 1 : 0

  name            = local.name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn

  desired_count = var.ecs_desired_count
  launch_type   = "FARGATE"

  network_configuration {
    subnets          = local.ecs_subnet_ids
    security_groups  = local.ecs_security_group_ids
    assign_public_ip = local.ecs_assign_public_ip
  }

  dynamic "load_balancer" {
    for_each = var.create_alb ? [1] : []

    content {
      target_group_arn = aws_lb_target_group.app[0].arn
      container_name   = "omniroute"
      container_port   = var.container_port
    }
  }

  lifecycle {
    precondition {
      condition     = length(local.ecs_subnet_ids) > 0
      error_message = "ECS requires at least one subnet."
    }

    precondition {
      condition     = length(local.ecs_security_group_ids) > 0
      error_message = "ECS requires at least one security group."
    }
  }

  depends_on = [
    aws_lb_listener.http,
  ]
}