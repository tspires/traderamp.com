"""TradeRamp AWS Fargate Infrastructure using Pulumi"""

import json
import pulumi
import pulumi_aws as aws
import pulumi_docker as docker
from pulumi import Config, Output, export

# Get configuration
config = Config()
environment = config.get("environment") or "production"
domain_name = config.get("domain") or "traderamp.com"
project_name = "traderamp"

# Container configuration
container_cpu = config.get_int("container_cpu") or 256
container_memory = config.get_int("container_memory") or 512
desired_count = config.get_int("desired_count") or 2
min_capacity = config.get_int("min_capacity") or 1
max_capacity = config.get_int("max_capacity") or 4

# Create tags
default_tags = {
    "Project": "TradeRamp",
    "Environment": environment,
    "ManagedBy": "Pulumi"
}

# Get availability zones
azs = aws.get_availability_zones(state="available")

# Create VPC
vpc = aws.ec2.Vpc(
    f"{project_name}-{environment}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**default_tags, "Name": f"{project_name}-{environment}-vpc"}
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway(
    f"{project_name}-{environment}-igw",
    vpc_id=vpc.id,
    tags={**default_tags, "Name": f"{project_name}-{environment}-igw"}
)

# Create public subnets
public_subnets = []
for i in range(2):
    subnet = aws.ec2.Subnet(
        f"{project_name}-{environment}-public-{i+1}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i+1}.0/24",
        availability_zone=azs.names[i],
        map_public_ip_on_launch=True,
        tags={**default_tags, "Name": f"{project_name}-{environment}-public-{i+1}"}
    )
    public_subnets.append(subnet)

# Create route table
public_rt = aws.ec2.RouteTable(
    f"{project_name}-{environment}-public-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id
    }],
    tags={**default_tags, "Name": f"{project_name}-{environment}-public-rt"}
)

# Associate subnets with route table
for i, subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(
        f"{project_name}-{environment}-rta-{i+1}",
        subnet_id=subnet.id,
        route_table_id=public_rt.id
    )

# Security Groups
alb_sg = aws.ec2.SecurityGroup(
    f"{project_name}-{environment}-alb-sg",
    vpc_id=vpc.id,
    description="Security group for ALB",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"]
        },
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["0.0.0.0/0"]
        }
    ],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={**default_tags, "Name": f"{project_name}-{environment}-alb-sg"}
)

ecs_sg = aws.ec2.SecurityGroup(
    f"{project_name}-{environment}-ecs-sg",
    vpc_id=vpc.id,
    description="Security group for ECS tasks",
    ingress=[{
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "security_groups": [alb_sg.id]
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={**default_tags, "Name": f"{project_name}-{environment}-ecs-sg"}
)

# Application Load Balancer
alb = aws.lb.LoadBalancer(
    f"{project_name}-{environment}-alb",
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[subnet.id for subnet in public_subnets],
    enable_deletion_protection=False,
    enable_http2=True,
    tags={**default_tags, "Name": f"{project_name}-{environment}-alb"}
)

# Target Group
target_group = aws.lb.TargetGroup(
    f"{project_name}-{environment}-tg",
    port=80,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check={
        "enabled": True,
        "healthy_threshold": 2,
        "interval": 30,
        "matcher": "200",
        "path": "/health",
        "port": "traffic-port",
        "protocol": "HTTP",
        "timeout": 5,
        "unhealthy_threshold": 3
    },
    deregistration_delay=30,
    tags={**default_tags, "Name": f"{project_name}-{environment}-tg"}
)

# HTTP Listener (redirect to HTTPS)
http_listener = aws.lb.Listener(
    f"{project_name}-{environment}-http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[{
        "type": "redirect",
        "redirect": {
            "port": "443",
            "protocol": "HTTPS",
            "status_code": "HTTP_301"
        }
    }]
)

# Get Route53 hosted zone (if domain is configured)
try:
    hosted_zone = aws.route53.get_zone(name=domain_name)
    create_dns = True
except:
    create_dns = False
    hosted_zone = None

# ACM Certificate (if using custom domain)
if create_dns and hosted_zone:
    certificate = aws.acm.Certificate(
        f"{project_name}-{environment}-cert",
        domain_name=domain_name,
        subject_alternative_names=[f"www.{domain_name}"],
        validation_method="DNS",
        tags={**default_tags, "Name": f"{project_name}-{environment}-cert"}
    )
    
    # Certificate validation
    cert_validation_record = aws.route53.Record(
        f"{project_name}-{environment}-cert-validation",
        zone_id=hosted_zone.zone_id,
        name=certificate.domain_validation_options[0].resource_record_name,
        type=certificate.domain_validation_options[0].resource_record_type,
        ttl=60,
        records=[certificate.domain_validation_options[0].resource_record_value],
        allow_overwrite=True
    )
    
    cert_validation = aws.acm.CertificateValidation(
        f"{project_name}-{environment}-cert-validation",
        certificate_arn=certificate.arn,
        validation_record_fqdns=[cert_validation_record.fqdn]
    )
    
    # HTTPS Listener
    https_listener = aws.lb.Listener(
        f"{project_name}-{environment}-https-listener",
        load_balancer_arn=alb.arn,
        port=443,
        protocol="HTTPS",
        ssl_policy="ELBSecurityPolicy-TLS-1-2-2017-01",
        certificate_arn=cert_validation.certificate_arn,
        default_actions=[{
            "type": "forward",
            "target_group_arn": target_group.arn
        }]
    )
    
    # DNS Records
    aws.route53.Record(
        f"{project_name}-{environment}-dns",
        zone_id=hosted_zone.zone_id,
        name=domain_name,
        type="A",
        aliases=[{
            "name": alb.dns_name,
            "zone_id": alb.zone_id,
            "evaluate_target_health": True
        }]
    )
    
    aws.route53.Record(
        f"{project_name}-{environment}-www-dns",
        zone_id=hosted_zone.zone_id,
        name=f"www.{domain_name}",
        type="A",
        aliases=[{
            "name": alb.dns_name,
            "zone_id": alb.zone_id,
            "evaluate_target_health": True
        }]
    )

# ECR Repository
ecr_repo = aws.ecr.Repository(
    f"{project_name}-{environment}-ecr",
    name=f"{project_name}-{environment}",
    image_tag_mutability="MUTABLE",
    image_scanning_configuration={
        "scan_on_push": True
    },
    tags={**default_tags, "Name": f"{project_name}-{environment}-ecr"}
)

# ECR Lifecycle Policy
ecr_lifecycle = aws.ecr.LifecyclePolicy(
    f"{project_name}-{environment}-ecr-lifecycle",
    repository=ecr_repo.name,
    policy=json.dumps({
        "rules": [
            {
                "rulePriority": 1,
                "description": "Keep last 10 images",
                "selection": {
                    "tagStatus": "tagged",
                    "tagPrefixList": ["v"],
                    "countType": "imageCountMoreThan",
                    "countNumber": 10
                },
                "action": {"type": "expire"}
            },
            {
                "rulePriority": 2,
                "description": "Remove untagged images after 7 days",
                "selection": {
                    "tagStatus": "untagged",
                    "countType": "sinceImagePushed",
                    "countUnit": "days",
                    "countNumber": 7
                },
                "action": {"type": "expire"}
            }
        ]
    })
)

# CloudWatch Log Group
log_group = aws.cloudwatch.LogGroup(
    f"{project_name}-{environment}-logs",
    name=f"/ecs/{project_name}-{environment}",
    retention_in_days=30,
    tags={**default_tags, "Name": f"{project_name}-{environment}-logs"}
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    f"{project_name}-{environment}-cluster",
    name=f"{project_name}-{environment}-cluster",
    settings=[{
        "name": "containerInsights",
        "value": "enabled"
    }],
    tags={**default_tags, "Name": f"{project_name}-{environment}-cluster"}
)

# IAM Roles
task_execution_role = aws.iam.Role(
    f"{project_name}-{environment}-task-exec-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"}
        }]
    }),
    tags={**default_tags, "Name": f"{project_name}-{environment}-task-exec-role"}
)

# Attach policies to execution role
aws.iam.RolePolicyAttachment(
    f"{project_name}-{environment}-task-exec-policy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# ECR policy for task execution role
aws.iam.RolePolicy(
    f"{project_name}-{environment}-ecr-policy",
    role=task_execution_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }]
    })
)

# Task role
task_role = aws.iam.Role(
    f"{project_name}-{environment}-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"}
        }]
    }),
    tags={**default_tags, "Name": f"{project_name}-{environment}-task-role"}
)

# Task Definition
container_name = f"{project_name}-{environment}"
task_definition = aws.ecs.TaskDefinition(
    f"{project_name}-{environment}-task",
    family=f"{project_name}-{environment}",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    cpu=str(container_cpu),
    memory=str(container_memory),
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=Output.json_dumps([{
        "name": container_name,
        "image": ecr_repo.repository_url.apply(lambda url: f"{url}:latest"),
        "portMappings": [{
            "containerPort": 80,
            "protocol": "tcp"
        }],
        "environment": [
            {"name": "ENVIRONMENT", "value": environment}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": log_group.name,
                "awslogs-region": aws.get_region().name,
                "awslogs-stream-prefix": "ecs"
            }
        },
        "healthCheck": {
            "command": ["CMD-SHELL", "curl -f http://localhost/health || exit 1"],
            "interval": 30,
            "timeout": 5,
            "retries": 3,
            "startPeriod": 60
        },
        "essential": True
    }]),
    tags={**default_tags, "Name": f"{project_name}-{environment}-task"}
)

# ECS Service
ecs_service = aws.ecs.Service(
    f"{project_name}-{environment}-service",
    name=f"{project_name}-{environment}",
    cluster=ecs_cluster.id,
    task_definition=task_definition.arn,
    desired_count=desired_count,
    launch_type="FARGATE",
    network_configuration={
        "security_groups": [ecs_sg.id],
        "subnets": [subnet.id for subnet in public_subnets],
        "assign_public_ip": True
    },
    load_balancers=[{
        "target_group_arn": target_group.arn,
        "container_name": container_name,
        "container_port": 80
    }],
    health_check_grace_period_seconds=60,
    deployment_configuration={
        "maximum_percent": 200,
        "minimum_healthy_percent": 100
    },
    tags={**default_tags, "Name": f"{project_name}-{environment}-service"}
)

# Auto Scaling
scaling_target = aws.appautoscaling.Target(
    f"{project_name}-{environment}-scaling-target",
    max_capacity=max_capacity,
    min_capacity=min_capacity,
    resource_id=Output.concat("service/", ecs_cluster.name, "/", ecs_service.name),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs"
)

# CPU scaling policy
cpu_scaling_policy = aws.appautoscaling.Policy(
    f"{project_name}-{environment}-cpu-scaling",
    name=f"{project_name}-{environment}-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=scaling_target.resource_id,
    scalable_dimension=scaling_target.scalable_dimension,
    service_namespace=scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration={
        "predefined_metric_specification": {
            "predefined_metric_type": "ECSServiceAverageCPUUtilization"
        },
        "target_value": 70.0,
        "scale_in_cooldown": 300,
        "scale_out_cooldown": 60
    }
)

# Memory scaling policy
memory_scaling_policy = aws.appautoscaling.Policy(
    f"{project_name}-{environment}-memory-scaling",
    name=f"{project_name}-{environment}-memory-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=scaling_target.resource_id,
    scalable_dimension=scaling_target.scalable_dimension,
    service_namespace=scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration={
        "predefined_metric_specification": {
            "predefined_metric_type": "ECSServiceAverageMemoryUtilization"
        },
        "target_value": 70.0,
        "scale_in_cooldown": 300,
        "scale_out_cooldown": 60
    }
)

# Exports
export("vpc_id", vpc.id)
export("alb_dns_name", alb.dns_name)
export("ecr_repository_url", ecr_repo.repository_url)
export("ecs_cluster_name", ecs_cluster.name)
export("ecs_service_name", ecs_service.name)
export("log_group_name", log_group.name)
export("website_url", f"https://{domain_name}" if create_dns else alb.dns_name.apply(lambda dns: f"http://{dns}"))