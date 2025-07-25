"""ECS Service component for TradeRamp infrastructure."""

from typing import Dict, List, Optional, Any
import json
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions, Output, Input

from config.constants import (
    ECSLaunchType, ECSNetworkMode, DeploymentController,
    Defaults, FargateConstraints
)
from config.settings import ContainerConfig, ScalingConfig


class ECSServiceComponent(ComponentResource):
    """
    ECS Service component with auto-scaling.
    
    This component creates:
    - ECS Task Definition
    - ECS Service with load balancer integration
    - Auto-scaling configuration
    - IAM roles and policies
    """
    
    def __init__(
        self,
        name: str,
        cluster_arn: Input[str],
        container_image: Input[str],
        container_config: ContainerConfig,
        scaling_config: ScalingConfig,
        vpc_subnets: List[Input[str]],
        security_groups: List[Input[str]],
        target_group_arn: Input[str],
        log_configuration: Dict[str, Any],
        environment_variables: Optional[Dict[str, str]] = None,
        secrets: Optional[Dict[str, str]] = None,
        health_check_grace_period: int = 60,
        enable_execute_command: bool = False,
        tags: Dict[str, str] = None,
        opts: ResourceOptions = None
    ) -> None:
        """
        Initialize ECS Service component.
        
        Args:
            name: Service name
            cluster_arn: ECS cluster ARN
            container_image: Container image URL
            container_config: Container resource configuration
            scaling_config: Auto-scaling configuration
            vpc_subnets: List of subnet IDs for tasks
            security_groups: List of security group IDs
            target_group_arn: Target group ARN for load balancer
            log_configuration: CloudWatch logs configuration
            environment_variables: Environment variables for container
            secrets: Secrets from Secrets Manager or Parameter Store
            health_check_grace_period: Health check grace period in seconds
            enable_execute_command: Enable ECS Exec for debugging
            tags: Resource tags
            opts: Pulumi resource options
        """
        super().__init__("traderamp:compute:ECSService", name, None, opts)
        
        self.name = name
        self.cluster_arn = cluster_arn
        self.container_image = container_image
        self.container_config = container_config
        self.scaling_config = scaling_config
        self.vpc_subnets = vpc_subnets
        self.security_groups = security_groups
        self.target_group_arn = target_group_arn
        self.log_configuration = log_configuration
        self.environment_variables = environment_variables or {}
        self.secrets = secrets or {}
        self.health_check_grace_period = health_check_grace_period
        self.enable_execute_command = enable_execute_command
        self.tags = tags or {}
        
        # Create IAM roles
        self.task_execution_role = self._create_task_execution_role()
        self.task_role = self._create_task_role()
        
        # Create task definition
        self.task_definition = self._create_task_definition()
        
        # Create service
        self.service = self._create_service()
        
        # Set up auto-scaling
        self._setup_auto_scaling()
        
        # Register outputs
        self.register_outputs({
            "service_name": self.service.name,
            "service_arn": self.service.id,
            "task_definition_arn": self.task_definition.arn,
            "task_definition_family": self.task_definition.family,
            "task_execution_role_arn": self.task_execution_role.arn,
            "task_role_arn": self.task_role.arn
        })
    
    def _create_task_execution_role(self) -> aws.iam.Role:
        """Create IAM role for task execution."""
        role = aws.iam.Role(
            f"{self.name}-task-execution-role",
            assume_role_policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }),
            tags={
                **self.tags,
                "Name": f"{self.name}-task-execution-role"
            },
            opts=ResourceOptions(parent=self)
        )
        
        # Attach AWS managed policy
        aws.iam.RolePolicyAttachment(
            f"{self.name}-task-execution-policy",
            role=role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
            opts=ResourceOptions(parent=self)
        )
        
        # Add policy for secrets if needed
        if self.secrets:
            aws.iam.RolePolicy(
                f"{self.name}-secrets-policy",
                role=role.id,
                policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "secretsmanager:GetSecretValue",
                            "ssm:GetParameters",
                            "ssm:GetParameter"
                        ],
                        "Resource": list(self.secrets.values())
                    }]
                }),
                opts=ResourceOptions(parent=self)
            )
        
        return role
    
    def _create_task_role(self) -> aws.iam.Role:
        """Create IAM role for task containers."""
        role = aws.iam.Role(
            f"{self.name}-task-role",
            assume_role_policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }),
            tags={
                **self.tags,
                "Name": f"{self.name}-task-role"
            },
            opts=ResourceOptions(parent=self)
        )
        
        # Add ECS Exec policy if enabled
        if self.enable_execute_command:
            aws.iam.RolePolicy(
                f"{self.name}-exec-policy",
                role=role.id,
                policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "ssmmessages:CreateControlChannel",
                            "ssmmessages:CreateDataChannel",
                            "ssmmessages:OpenControlChannel",
                            "ssmmessages:OpenDataChannel"
                        ],
                        "Resource": "*"
                    }]
                }),
                opts=ResourceOptions(parent=self)
            )
        
        return role
    
    def _create_task_definition(self) -> aws.ecs.TaskDefinition:
        """Create ECS task definition."""
        # Prepare environment variables
        environment = [
            {"name": k, "value": v} 
            for k, v in self.environment_variables.items()
        ]
        
        # Prepare secrets
        secrets_list = [
            {"name": k, "valueFrom": v}
            for k, v in self.secrets.items()
        ]
        
        # Container definition
        container_def = {
            "name": self.name,
            "image": self.container_image,
            "cpu": self.container_config.cpu,
            "memory": self.container_config.memory,
            "essential": True,
            "portMappings": [{
                "containerPort": 80,
                "protocol": "tcp"
            }],
            "environment": environment,
            "secrets": secrets_list,
            "logConfiguration": self.log_configuration,
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
        
        return aws.ecs.TaskDefinition(
            f"{self.name}-task",
            family=self.name,
            network_mode=ECSNetworkMode.AWSVPC.value,
            requires_compatibilities=[ECSLaunchType.FARGATE.value],
            cpu=str(self.container_config.cpu),
            memory=str(self.container_config.memory),
            execution_role_arn=self.task_execution_role.arn,
            task_role_arn=self.task_role.arn,
            container_definitions=Output.json_dumps([container_def]),
            tags={
                **self.tags,
                "Name": f"{self.name}-task"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_service(self) -> aws.ecs.Service:
        """Create ECS service."""
        return aws.ecs.Service(
            f"{self.name}-service",
            name=self.name,
            cluster=self.cluster_arn,
            task_definition=self.task_definition.arn,
            desired_count=self.scaling_config.desired_count,
            launch_type=ECSLaunchType.FARGATE.value,
            platform_version="LATEST",
            deployment_controller={
                "type": DeploymentController.ECS.value
            },
            deployment_configuration={
                "maximum_percent": Defaults.DEPLOYMENT_MAX_PERCENT,
                "minimum_healthy_percent": Defaults.DEPLOYMENT_MIN_HEALTHY_PERCENT,
                "deployment_circuit_breaker": {
                    "enable": True,
                    "rollback": True
                }
            },
            network_configuration={
                "subnets": self.vpc_subnets,
                "security_groups": self.security_groups,
                "assign_public_ip": True  # Required for Fargate in public subnets
            },
            load_balancers=[{
                "target_group_arn": self.target_group_arn,
                "container_name": self.name,
                "container_port": 80
            }],
            health_check_grace_period_seconds=self.health_check_grace_period,
            enable_execute_command=self.enable_execute_command,
            propagate_tags="TASK_DEFINITION",
            tags={
                **self.tags,
                "Name": f"{self.name}-service"
            },
            opts=ResourceOptions(parent=self, depends_on=[self.task_definition])
        )
    
    def _setup_auto_scaling(self) -> None:
        """Set up auto-scaling for the service."""
        # Create scaling target
        scaling_target = aws.appautoscaling.Target(
            f"{self.name}-scaling-target",
            max_capacity=self.scaling_config.max_capacity,
            min_capacity=self.scaling_config.min_capacity,
            resource_id=Output.concat("service/", 
                self.cluster_arn.apply(lambda arn: arn.split("/")[-1]), 
                "/", self.service.name
            ),
            scalable_dimension="ecs:service:DesiredCount",
            service_namespace="ecs",
            opts=ResourceOptions(parent=self)
        )
        
        # CPU scaling policy
        aws.appautoscaling.Policy(
            f"{self.name}-cpu-scaling",
            name=f"{self.name}-cpu-scaling",
            policy_type="TargetTrackingScaling",
            resource_id=scaling_target.resource_id,
            scalable_dimension=scaling_target.scalable_dimension,
            service_namespace=scaling_target.service_namespace,
            target_tracking_scaling_policy_configuration={
                "predefined_metric_specification": {
                    "predefined_metric_type": "ECSServiceAverageCPUUtilization"
                },
                "target_value": self.scaling_config.cpu_target,
                "scale_in_cooldown": self.scaling_config.scale_in_cooldown,
                "scale_out_cooldown": self.scaling_config.scale_out_cooldown
            },
            opts=ResourceOptions(parent=self)
        )
        
        # Memory scaling policy
        aws.appautoscaling.Policy(
            f"{self.name}-memory-scaling",
            name=f"{self.name}-memory-scaling",
            policy_type="TargetTrackingScaling",
            resource_id=scaling_target.resource_id,
            scalable_dimension=scaling_target.scalable_dimension,
            service_namespace=scaling_target.service_namespace,
            target_tracking_scaling_policy_configuration={
                "predefined_metric_specification": {
                    "predefined_metric_type": "ECSServiceAverageMemoryUtilization"
                },
                "target_value": self.scaling_config.memory_target,
                "scale_in_cooldown": self.scaling_config.scale_in_cooldown,
                "scale_out_cooldown": self.scaling_config.scale_out_cooldown
            },
            opts=ResourceOptions(parent=self)
        )