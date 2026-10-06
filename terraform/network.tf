data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  count = var.create_network ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = local.name
  }
}

resource "aws_internet_gateway" "main" {
  count = var.create_network ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  tags = {
    Name = "${local.name}-igw"
  }
}

resource "aws_subnet" "public_a" {
  count = var.create_network ? 1 : 0

  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.public_subnet_a_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name}-public-a"
  }
}

resource "aws_subnet" "public_b" {
  count = var.create_network ? 1 : 0

  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.public_subnet_b_cidr
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name}-public-b"
  }
}

resource "aws_route_table" "public" {
  count = var.create_network ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = {
    Name = "${local.name}-public"
  }
}

resource "aws_route_table_association" "public_a" {
  count = var.create_network ? 1 : 0

  subnet_id      = aws_subnet.public_a[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "public_b" {
  count = var.create_network ? 1 : 0

  subnet_id      = aws_subnet.public_b[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_security_group" "alb" {
  count = var.create_network ? 1 : 0

  name        = "${local.name}-alb"
  description = "Allow HTTP traffic to OmniRoute ALB"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name}-alb"
  }
}

resource "aws_security_group" "ecs" {
  count = var.create_network ? 1 : 0

  name        = "${local.name}-ecs"
  description = "Allow OmniRoute traffic from ALB"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    description     = "OmniRoute application traffic"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name}-ecs"
  }
}

resource "aws_lb" "app" {
  count = var.create_alb ? 1 : 0

  name               = local.name
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    aws_security_group.alb[0].id,
  ]

  subnets = [
    aws_subnet.public_a[0].id,
    aws_subnet.public_b[0].id,
  ]

  lifecycle {
    precondition {
      condition     = var.create_network
      error_message = "create_network must be true when create_alb is true."
    }
  }

  tags = {
    Name = local.name
  }
}

resource "aws_lb_target_group" "app" {
  count = var.create_alb ? 1 : 0

  name        = local.name
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main[0].id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  count = var.create_alb ? 1 : 0

  load_balancer_arn = aws_lb.app[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app[0].arn
  }
}