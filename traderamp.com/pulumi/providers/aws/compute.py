"""
AWS Fargate compute components following clean code principles.
"""

from typing import Dict, List, Optional, Any
import json
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Output, Input

from core.base_component import BaseInfrastructureComponent
from core.interfaces import ContainerSpec, ScalingSpec
from core.validators import ValidationContext, RangeValidator


class FargateServiceComponent(BaseInfrastructureComponent):
    """
    ECS Fargate service component.
    
    Manages ECS cluster, service, task definition, and auto-scaling.
    """
    
    def __init__(
        self,
        name: str,
        vpc_id: Input[str],
        subnet_ids: List[Input[str]],
        security_group_ids: List[Input[str]],
        container_spec: ContainerSpec,
        scaling_spec: ScalingSpec,
        enable_container_insights: bool = True,
        log_retention_days: int = 30,
        target_group_arn: Optional[Input[str]] = None,
        **kwargs
    ):
        """Initialize Fargate service component."""
        self.vpc_id = vpc_id
        self.subnet_ids = subnet_ids
        self.security_group_ids = security_group_ids
        self.container_spec = container_spec
        self.scaling_spec = scaling_spec
        self.enable_container_insights = enable_container_insights
        self.log_retention_days = log_retention_days
        self.target_group_arn = target_group_arn
        
        super().__init__(
            "traderamp:aws:compute:FargateService",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate Fargate configuration."""
        context = ValidationContext()
        
        context.add_validation(
            "log_retention_days",
            RangeValidator(1, 3653, "Log retention"),
            self.log_retention_days
        )
        
        # Validate specifications
        self.container_spec.validate()
        self.scaling_spec.validate()
        
        context.validate_all()
    
    def create_resources(self) -> None:
        """Create Fargate resources."""
        # Create IAM roles
        execution_role = self._create_execution_role()
        task_role = self._create_task_role()
        
        # Create CloudWatch log group
        log_group = self._create_log_group()
        
        # Create ECS cluster
        cluster = self._create_cluster()
        
        # Create task definition
        task_definition = self._create_task_definition(
            execution_role, task_role, log_group
        )
        
        # Create ECS service
        service = self._create_service(cluster, task_definition)
        
        # Set up auto-scaling
        self._setup_auto_scaling(cluster, service)
        
        # Store key resources
        self.add_resource("cluster", cluster)
        self.add_resource("service", service)
        self.add_resource("task_definition", task_definition)
        self.add_resource("log_group", log_group)
    
    def _create_execution_role(self) -> aws.iam.Role:
        """Create IAM role for task execution."""
        role = aws.iam.Role(
            f"{self.name}-execution-role",
            assume_role_policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }),
            tags=self.get_tags("IAMRole", f"{self.name}-execution-role"),
            opts=ResourceOptions(parent=self)
        )
        
        # Attach AWS managed policy
        aws.iam.RolePolicyAttachment(
            f"{self.name}-execution-policy",
            role=role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
            opts=ResourceOptions(parent=self)
        )
        
        return role
    
    def _create_task_role(self) -> aws.iam.Role:
        """Create IAM role for task containers."""
        return aws.iam.Role(
            f"{self.name}-task-role",
            assume_role_policy=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }),
            tags=self.get_tags("IAMRole", f"{self.name}-task-role"),
            opts=ResourceOptions(parent=self)
        )
    
    def _create_log_group(self) -> aws.cloudwatch.LogGroup:
        """Create CloudWatch log group."""
        return aws.cloudwatch.LogGroup(
            f"{self.name}-logs",
            name=f"/ecs/{self.name}",
            retention_in_days=self.log_retention_days,
            tags=self.get_tags("LogGroup", f"{self.name}-logs"),
            opts=ResourceOptions(parent=self)
        )
    
    def _create_cluster(self) -> aws.ecs.Cluster:
        """Create ECS cluster."""
        settings = []
        if self.enable_container_insights:
            settings.append({
                "name": "containerInsights",
                "value": "enabled"
            })
        
        return aws.ecs.Cluster(
            f"{self.name}-cluster",
            name=self.name,
            settings=settings,
            tags=self.get_tags("ECSCluster", f"{self.name}-cluster"),
            opts=ResourceOptions(parent=self)
        )
    
    def _create_task_definition(
        self,
        execution_role: aws.iam.Role,
        task_role: aws.iam.Role,
        log_group: aws.cloudwatch.LogGroup
    ) -> aws.ecs.TaskDefinition:
        """Create ECS task definition."""
        # Prepare environment variables
        environment = [
            {"name": k, "value": v}
            for k, v in self.container_spec.environment_variables.items()
        ]
        
        # Container definition
        container_def = {
            "name": self.name,
            "image": self.container_spec.image,
            "cpu": self.container_spec.cpu_units,
            "memory": self.container_spec.memory_mb,
            "essential": True,
            "portMappings": [{
                "containerPort": self.container_spec.port,
                "protocol": "tcp"
            }],
            "environment": environment,
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
            }
        }
        
        return aws.ecs.TaskDefinition(
            f"{self.name}-task",
            family=self.name,
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            cpu=str(self.container_spec.cpu_units),
            memory=str(self.container_spec.memory_mb),
            execution_role_arn=execution_role.arn,
            task_role_arn=task_role.arn,
            container_definitions=Output.json_dumps([container_def]),
            tags=self.get_tags("TaskDefinition", f"{self.name}-task"),
            opts=ResourceOptions(parent=self)
        )
    
    def _create_service(
        self,
        cluster: aws.ecs.Cluster,
        task_definition: aws.ecs.TaskDefinition
    ) -> aws.ecs.Service:
        """Create ECS service."""
        service_config = {
            "name": self.name,
            "cluster": cluster.arn,
            "task_definition": task_definition.arn,
            "desired_count": self.scaling_spec.min_instances,
            "launch_type": "FARGATE",
            "platform_version": "LATEST",
            "deployment_controller": {"type": "ECS"},
            "deployment_maximum_percent": 200,
            "deployment_minimum_healthy_percent": 100,
            "deployment_circuit_breaker": {
                "enable": True,
                "rollback": True
            },
            "network_configuration": {
                "subnets": self.subnet_ids,
                "security_groups": self.security_group_ids,
                "assign_public_ip": True
            },
            "health_check_grace_period_seconds": 60,
            "enable_execute_command": True,
            "propagate_tags": "TASK_DEFINITION",
            "tags": self.get_tags("ECSService", f"{self.name}-service")
        }
        
        # Add load balancer configuration if target group is set
        if self.target_group_arn:
            service_config["load_balancers"] = [{
                "target_group_arn": self.target_group_arn,
                "container_name": self.name,
                "container_port": self.container_spec.port
            }]
        
        return aws.ecs.Service(
            f"{self.name}-service",
            **service_config,
            opts=ResourceOptions(parent=self, depends_on=[task_definition])
        )
    
    def register_with_target_group(self, target_group_arn: Input[str]) -> None:
        """Register service with load balancer target group."""
        self.target_group_arn = target_group_arn
        
        # If service already exists, we need to update it
        service = self.get_resource("service")
        if service:
            # Note: In a real implementation, you'd need to handle service updates
            pulumi.log.info("Service needs to be recreated to register with target group")
    
    def _setup_auto_scaling(
        self,
        cluster: aws.ecs.Cluster,
        service: aws.ecs.Service
    ) -> None:
        """Set up auto-scaling for the service."""
        # Create scaling target
        scaling_target = aws.appautoscaling.Target(
            f"{self.name}-scaling",
            max_capacity=self.scaling_spec.max_instances,
            min_capacity=self.scaling_spec.min_instances,
            resource_id=Output.concat(
                "service/",
                cluster.name,
                "/",
                service.name
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
                "target_value": self.scaling_spec.target_cpu_percent,
                "scale_in_cooldown": self.scaling_spec.scale_down_cooldown_seconds,
                "scale_out_cooldown": self.scaling_spec.scale_up_cooldown_seconds
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
                "target_value": self.scaling_spec.target_memory_percent,
                "scale_in_cooldown": self.scaling_spec.scale_down_cooldown_seconds,
                "scale_out_cooldown": self.scaling_spec.scale_up_cooldown_seconds
            },
            opts=ResourceOptions(parent=self)
        )
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        cluster = self.get_resource("cluster")
        service = self.get_resource("service")
        
        return {
            "cluster_name": cluster.name,
            "cluster_arn": cluster.arn,
            "service_name": service.name,
            "service_arn": service.id
        }