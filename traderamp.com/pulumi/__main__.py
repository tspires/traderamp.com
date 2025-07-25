"""
TradeRamp Infrastructure Entry Point

This module initializes the complete TradeRamp infrastructure using clean,
modular components and proper error handling.
"""

import sys
from typing import NoReturn
import pulumi

from config.settings import InfrastructureConfig
from stacks.traderamp_stack import TradeRampStack
from utils.errors import ConfigurationError, InfrastructureError


def validate_environment() -> None:
    """
    Validate the deployment environment and prerequisites.
    
    Raises:
        ConfigurationError: If environment validation fails
    """
    try:
        # Verify Pulumi context
        stack_name = pulumi.get_stack()
        project_name = pulumi.get_project()
        
        if not stack_name:
            raise ConfigurationError(
                message="No Pulumi stack specified. Use 'pulumi stack select' to choose a stack."
            )
        
        if not project_name:
            raise ConfigurationError(
                message="No Pulumi project found. Ensure you're in a Pulumi project directory."
            )
        
        pulumi.log.info(f"Deploying project '{project_name}' to stack '{stack_name}'")
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(
            message=f"Environment validation failed: {str(e)}"
        ) from e


def main() -> None:
    """
    Main entry point for TradeRamp infrastructure deployment.
    
    This function:
    1. Validates the environment
    2. Loads and validates configuration
    3. Creates the infrastructure stack
    4. Handles any errors gracefully
    """
    try:
        # Validate environment first
        validate_environment()
        
        # Load and validate configuration
        pulumi.log.info("Loading infrastructure configuration...")
        config = InfrastructureConfig.from_pulumi_config()
        
        # Log configuration summary
        pulumi.log.info(
            f"Configuration loaded - Project: {config.project_name}, "
            f"Environment: {config.environment}, "
            f"Region: {config.aws_region}"
        )
        
        if config.domain.has_domain:
            pulumi.log.info(f"Domain configured: {config.domain.apex_domain}")
        
        # Create infrastructure stack
        pulumi.log.info("Creating TradeRamp infrastructure stack...")
        stack = TradeRampStack(config)
        
        # Log successful deployment initiation
        pulumi.log.info(
            f"Successfully initiated TradeRamp infrastructure deployment "
            f"for {config.environment} environment"
        )
        
        # Log stack information for debugging
        stack_info = stack.get_stack_info()
        pulumi.log.info(f"Stack info: {stack_info}")
        
    except ConfigurationError as e:
        pulumi.log.error(f"Configuration error: {e}")
        sys.exit(1)
        
    except InfrastructureError as e:
        pulumi.log.error(f"Infrastructure error: {e}")
        sys.exit(1)
        
    except Exception as e:
        pulumi.log.error(f"Unexpected error during deployment: {str(e)}")
        # Re-raise for Pulumi to handle
        raise


if __name__ == "__main__":
    main()