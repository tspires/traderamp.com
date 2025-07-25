"""Constants for TradeRamp infrastructure."""

from enum import Enum
from typing import List, Tuple


class NetworkCIDR(str, Enum):
    """Network CIDR blocks."""
    
    VPC = "10.0.0.0/16"
    PUBLIC_SUBNET_1 = "10.0.1.0/24"
    PUBLIC_SUBNET_2 = "10.0.2.0/24"
    PRIVATE_SUBNET_1 = "10.0.10.0/24"
    PRIVATE_SUBNET_2 = "10.0.11.0/24"
    INTERNET = "0.0.0.0/0"


class Port(int, Enum):
    """Common network ports."""
    
    HTTP = 80
    HTTPS = 443
    SSH = 22
    POSTGRESQL = 5432
    MYSQL = 3306
    REDIS = 6379


class Protocol(str, Enum):
    """Network protocols."""
    
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ALL = "-1"


class TargetType(str, Enum):
    """ALB target types."""
    
    INSTANCE = "instance"
    IP = "ip"
    LAMBDA = "lambda"


class HealthCheckProtocol(str, Enum):
    """Health check protocols."""
    
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    TCP = "TCP"


class ECSLaunchType(str, Enum):
    """ECS launch types."""
    
    FARGATE = "FARGATE"
    EC2 = "EC2"
    FARGATE_SPOT = "FARGATE_SPOT"


class ECSNetworkMode(str, Enum):
    """ECS network modes."""
    
    AWSVPC = "awsvpc"
    BRIDGE = "bridge"
    HOST = "host"
    NONE = "none"


class LogDriver(str, Enum):
    """Container log drivers."""
    
    AWSLOGS = "awslogs"
    JSON_FILE = "json-file"
    SYSLOG = "syslog"
    FLUENTD = "fluentd"
    NONE = "none"


class MetricType(str, Enum):
    """Auto-scaling metric types."""
    
    CPU = "ECSServiceAverageCPUUtilization"
    MEMORY = "ECSServiceAverageMemoryUtilization"
    REQUEST_COUNT = "ALBRequestCountPerTarget"


class DeploymentController(str, Enum):
    """ECS deployment controllers."""
    
    ECS = "ECS"
    CODE_DEPLOY = "CODE_DEPLOY"
    EXTERNAL = "EXTERNAL"


# AWS Service Limits and Constraints
class FargateConstraints:
    """AWS Fargate resource constraints."""
    
    # CPU to memory mappings (CPU: (min_memory, max_memory))
    CPU_MEMORY_COMBINATIONS: dict[int, Tuple[int, int]] = {
        256: (512, 2048),
        512: (1024, 4096),
        1024: (2048, 8192),
        2048: (4096, 16384),
        4096: (8192, 30720)
    }
    
    VALID_CPU_VALUES: List[int] = list(CPU_MEMORY_COMBINATIONS.keys())
    
    @classmethod
    def get_memory_range(cls, cpu: int) -> Tuple[int, int]:
        """Get valid memory range for given CPU."""
        if cpu not in cls.CPU_MEMORY_COMBINATIONS:
            raise ValueError(f"Invalid CPU value: {cpu}")
        return cls.CPU_MEMORY_COMBINATIONS[cpu]
    
    @classmethod
    def is_valid_combination(cls, cpu: int, memory: int) -> bool:
        """Check if CPU/memory combination is valid."""
        if cpu not in cls.CPU_MEMORY_COMBINATIONS:
            return False
        min_mem, max_mem = cls.CPU_MEMORY_COMBINATIONS[cpu]
        return min_mem <= memory <= max_mem


# Default values
class Defaults:
    """Default configuration values."""
    
    # Container defaults
    CONTAINER_CPU = 256
    CONTAINER_MEMORY = 512
    
    # Scaling defaults
    DESIRED_COUNT = 2
    MIN_CAPACITY = 1
    MAX_CAPACITY = 4
    CPU_TARGET = 70.0
    MEMORY_TARGET = 70.0
    SCALE_IN_COOLDOWN = 300
    SCALE_OUT_COOLDOWN = 60
    
    # Health check defaults
    HEALTH_CHECK_PATH = "/health"
    HEALTH_CHECK_INTERVAL = 30
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_HEALTHY_THRESHOLD = 2
    HEALTH_CHECK_UNHEALTHY_THRESHOLD = 3
    HEALTH_CHECK_GRACE_PERIOD = 60
    
    # Deployment defaults
    DEPLOYMENT_MAX_PERCENT = 200
    DEPLOYMENT_MIN_HEALTHY_PERCENT = 100
    DEREGISTRATION_DELAY = 30
    
    # Logging defaults
    LOG_RETENTION_DAYS = 30
    LOG_STREAM_PREFIX = "ecs"
    
    # Network defaults
    AVAILABILITY_ZONES = 2


# AWS resource limits
class AWSLimits:
    """AWS service limits."""
    
    # ECS limits
    MAX_TASKS_PER_SERVICE = 1000
    MAX_SERVICES_PER_CLUSTER = 2000
    MAX_CONTAINER_INSTANCES_PER_CLUSTER = 2000
    
    # ALB limits
    MAX_TARGETS_PER_TARGET_GROUP = 1000
    MAX_RULES_PER_LISTENER = 100
    MAX_TARGET_GROUPS_PER_ALB = 100
    
    # CloudWatch logs limits
    MAX_LOG_GROUP_NAME_LENGTH = 512
    MAX_LOG_STREAM_NAME_LENGTH = 512
    MAX_METRIC_FILTERS_PER_LOG_GROUP = 100
    
    # Tag limits
    MAX_TAGS_PER_RESOURCE = 50
    MAX_TAG_KEY_LENGTH = 128
    MAX_TAG_VALUE_LENGTH = 256


# Common tag keys
class TagKeys:
    """Standard tag keys."""
    
    PROJECT = "Project"
    ENVIRONMENT = "Environment"
    MANAGED_BY = "ManagedBy"
    OWNER = "Owner"
    COST_CENTER = "CostCenter"
    CREATED_BY = "CreatedBy"
    CREATED_AT = "CreatedAt"
    PURPOSE = "Purpose"
    VERSION = "Version"