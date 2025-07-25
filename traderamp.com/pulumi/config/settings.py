"""Configuration management for TradeRamp infrastructure."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pulumi
from pulumi import Config


@dataclass
class ContainerConfig:
    """Container resource configuration."""
    
    cpu: int = 256
    memory: int = 512
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate container configuration."""
        valid_cpu_values = [256, 512, 1024, 2048, 4096]
        if self.cpu not in valid_cpu_values:
            raise ValueError(
                f"Invalid CPU value: {self.cpu}. "
                f"Must be one of {valid_cpu_values}"
            )
        
        if self.memory < 512:
            raise ValueError(f"Memory must be at least 512MB, got {self.memory}")
        
        # Fargate memory constraints based on CPU
        memory_constraints = {
            256: (512, 2048),
            512: (1024, 4096),
            1024: (2048, 8192),
            2048: (4096, 16384),
            4096: (8192, 30720)
        }
        
        min_memory, max_memory = memory_constraints[self.cpu]
        if not min_memory <= self.memory <= max_memory:
            raise ValueError(
                f"Memory {self.memory}MB is invalid for {self.cpu} CPU. "
                f"Must be between {min_memory}MB and {max_memory}MB"
            )


@dataclass
class ScalingConfig:
    """Auto-scaling configuration."""
    
    desired_count: int = 2
    min_capacity: int = 1
    max_capacity: int = 4
    cpu_target: float = 70.0
    memory_target: float = 70.0
    scale_in_cooldown: int = 300
    scale_out_cooldown: int = 60
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate scaling configuration."""
        if self.min_capacity < 1:
            raise ValueError("min_capacity must be at least 1")
        
        if self.min_capacity > self.max_capacity:
            raise ValueError(
                f"min_capacity ({self.min_capacity}) cannot be greater than "
                f"max_capacity ({self.max_capacity})"
            )
        
        if not self.min_capacity <= self.desired_count <= self.max_capacity:
            raise ValueError(
                f"desired_count ({self.desired_count}) must be between "
                f"min_capacity ({self.min_capacity}) and "
                f"max_capacity ({self.max_capacity})"
            )
        
        if not 0 < self.cpu_target <= 100:
            raise ValueError(f"cpu_target must be between 0 and 100, got {self.cpu_target}")
        
        if not 0 < self.memory_target <= 100:
            raise ValueError(f"memory_target must be between 0 and 100, got {self.memory_target}")


@dataclass
class HealthCheckConfig:
    """Health check configuration."""
    
    path: str = "/health"
    interval: int = 30
    timeout: int = 5
    healthy_threshold: int = 2
    unhealthy_threshold: int = 3
    grace_period: int = 60
    
    def validate(self) -> None:
        """Validate health check configuration."""
        if self.timeout >= self.interval:
            raise ValueError("timeout must be less than interval")
        
        if self.healthy_threshold < 1:
            raise ValueError("healthy_threshold must be at least 1")
        
        if self.unhealthy_threshold < 1:
            raise ValueError("unhealthy_threshold must be at least 1")


@dataclass
class DomainConfig:
    """Domain and SSL configuration."""
    
    domain_name: Optional[str] = None
    create_dns_records: bool = True
    ssl_policy: str = "ELBSecurityPolicy-TLS13-1-2-2021-06"
    
    @property
    def has_domain(self) -> bool:
        """Check if domain is configured."""
        return bool(self.domain_name)
    
    @property
    def apex_domain(self) -> str:
        """Get apex domain without www."""
        if not self.domain_name:
            return ""
        return self.domain_name.replace("www.", "")
    
    @property
    def www_domain(self) -> str:
        """Get www subdomain."""
        apex = self.apex_domain
        return f"www.{apex}" if apex and not apex.startswith("www.") else apex


@dataclass
class InfrastructureConfig:
    """Main infrastructure configuration."""
    
    # Basic settings
    project_name: str
    environment: str
    aws_region: str
    
    # Component configurations
    container: ContainerConfig = field(default_factory=ContainerConfig)
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    domain: DomainConfig = field(default_factory=DomainConfig)
    
    # Additional settings
    enable_container_insights: bool = True
    log_retention_days: int = 30
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize and validate configuration."""
        # Set default tags
        self.tags = {
            "Project": self.project_name,
            "Environment": self.environment,
            "ManagedBy": "Pulumi",
            **self.tags  # Allow custom tags to override defaults
        }
        self.validate()
    
    def validate(self) -> None:
        """Validate all configuration."""
        # Validate sub-configurations
        self.container.validate()
        self.scaling.validate()
        self.health_check.validate()
        
        # Validate environment name
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            pulumi.log.warn(
                f"Environment '{self.environment}' is not standard. "
                f"Consider using one of {valid_environments}"
            )
        
        # Validate log retention
        valid_retention_days = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]
        if self.log_retention_days not in valid_retention_days:
            raise ValueError(
                f"Invalid log_retention_days: {self.log_retention_days}. "
                f"Must be one of {valid_retention_days}"
            )
    
    @classmethod
    def from_pulumi_config(cls) -> "InfrastructureConfig":
        """Load configuration from Pulumi config."""
        config = Config()
        
        # Load basic settings
        project_name = config.get("project_name") or "traderamp"
        environment = config.get("environment") or "production"
        aws_region = config.get("aws:region") or "us-east-1"
        
        # Load container config
        container_config = ContainerConfig(
            cpu=config.get_int("container_cpu") or 256,
            memory=config.get_int("container_memory") or 512
        )
        
        # Load scaling config
        scaling_config = ScalingConfig(
            desired_count=config.get_int("desired_count") or 2,
            min_capacity=config.get_int("min_capacity") or 1,
            max_capacity=config.get_int("max_capacity") or 4,
            cpu_target=config.get_float("cpu_target") or 70.0,
            memory_target=config.get_float("memory_target") or 70.0,
            scale_in_cooldown=config.get_int("scale_in_cooldown") or 300,
            scale_out_cooldown=config.get_int("scale_out_cooldown") or 60
        )
        
        # Load health check config
        health_check_config = HealthCheckConfig(
            path=config.get("health_check_path") or "/health",
            interval=config.get_int("health_check_interval") or 30,
            timeout=config.get_int("health_check_timeout") or 5,
            healthy_threshold=config.get_int("health_check_healthy_threshold") or 2,
            unhealthy_threshold=config.get_int("health_check_unhealthy_threshold") or 3,
            grace_period=config.get_int("health_check_grace_period") or 60
        )
        
        # Load domain config
        domain_config = DomainConfig(
            domain_name=config.get("domain_name"),
            create_dns_records=config.get_bool("create_dns_records") or True,
            ssl_policy=config.get("ssl_policy") or "ELBSecurityPolicy-TLS13-1-2-2021-06"
        )
        
        # Load additional settings
        enable_container_insights = config.get_bool("enable_container_insights")
        if enable_container_insights is None:
            enable_container_insights = True
        
        log_retention_days = config.get_int("log_retention_days") or 30
        
        # Load custom tags
        custom_tags = {}
        tags_json = config.get("tags")
        if tags_json:
            import json
            try:
                custom_tags = json.loads(tags_json)
            except json.JSONDecodeError:
                pulumi.log.warn(f"Failed to parse custom tags: {tags_json}")
        
        return cls(
            project_name=project_name,
            environment=environment,
            aws_region=aws_region,
            container=container_config,
            scaling=scaling_config,
            health_check=health_check_config,
            domain=domain_config,
            enable_container_insights=enable_container_insights,
            log_retention_days=log_retention_days,
            tags=custom_tags
        )
    
    @property
    def name_prefix(self) -> str:
        """Get resource name prefix."""
        return f"{self.project_name}-{self.environment}"
    
    def get_resource_name(self, resource_type: str) -> str:
        """Get consistent resource name."""
        return f"{self.name_prefix}-{resource_type}"