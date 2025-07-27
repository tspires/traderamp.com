"""
TradeRamp Infrastructure Entry Point - Refactored for Clean Code.

This module demonstrates:
- Separation of concerns
- Single responsibility
- Proper error handling
- Clear function names
"""

import sys
import pulumi

from stacks.traderamp_stack import TradeRampStack


def validate_pulumi_context() -> None:
    """
    Validate that we're in a proper Pulumi context.
    
    Raises:
        SystemExit: If validation fails
    """
    try:
        stack_name = pulumi.get_stack()
        project_name = pulumi.get_project()
        
        if not stack_name:
            raise ValueError("No Pulumi stack selected")
        
        if not project_name:
            raise ValueError("No Pulumi project found")
        
        pulumi.log.info(f"Deploying {project_name} to stack {stack_name}")
        
    except Exception as error:
        pulumi.log.error(f"Pulumi context validation failed: {error}")
        sys.exit(1)


def create_infrastructure() -> None:
    """
    Create the TradeRamp infrastructure.
    
    Raises:
        SystemExit: If infrastructure creation fails
    """
    try:
        # Create the stack
        stack = TradeRampStack()
        
        pulumi.log.info("Infrastructure creation completed successfully")
        
    except ValueError as error:
        pulumi.log.error(f"Configuration error: {error}")
        sys.exit(1)
        
    except Exception as error:
        pulumi.log.error(f"Infrastructure creation failed: {error}")
        raise  # Let Pulumi handle the error


def main() -> None:
    """Main entry point."""
    validate_pulumi_context()
    create_infrastructure()


if __name__ == "__main__":
    main()