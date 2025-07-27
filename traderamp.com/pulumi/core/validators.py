"""
Validators following Single Responsibility Principle.

Each validator has one reason to change.
"""

from typing import Any, List, Tuple, Optional
from abc import ABC, abstractmethod


class IValidator(ABC):
    """Base interface for validators."""
    
    @abstractmethod
    def validate(self, value: Any) -> None:
        """
        Validate a value.
        
        Args:
            value: Value to validate
            
        Raises:
            ValueError: If validation fails
        """
        pass


class RangeValidator(IValidator):
    """Validates numeric values are within a range."""
    
    def __init__(self, min_value: float, max_value: float, name: str):
        """
        Initialize range validator.
        
        Args:
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            name: Name of the value being validated
        """
        self.min_value = min_value
        self.max_value = max_value
        self.name = name
    
    def validate(self, value: Any) -> None:
        """Validate value is within range."""
        if not isinstance(value, (int, float)):
            raise ValueError(f"{self.name} must be numeric")
        
        if not self.min_value <= value <= self.max_value:
            raise ValueError(
                f"{self.name} must be between {self.min_value} and {self.max_value}, "
                f"got {value}"
            )


class StringPatternValidator(IValidator):
    """Validates strings match a pattern."""
    
    def __init__(self, pattern: str, name: str):
        """
        Initialize pattern validator.
        
        Args:
            pattern: Regular expression pattern
            name: Name of the value being validated
        """
        import re
        self.pattern = re.compile(pattern)
        self.name = name
    
    def validate(self, value: Any) -> None:
        """Validate value matches pattern."""
        if not isinstance(value, str):
            raise ValueError(f"{self.name} must be a string")
        
        if not self.pattern.match(value):
            raise ValueError(
                f"{self.name} does not match required pattern: {self.pattern.pattern}"
            )


class ListLengthValidator(IValidator):
    """Validates list length constraints."""
    
    def __init__(self, min_length: int, max_length: Optional[int], name: str):
        """
        Initialize list length validator.
        
        Args:
            min_length: Minimum list length
            max_length: Maximum list length (None for unlimited)
            name: Name of the list being validated
        """
        self.min_length = min_length
        self.max_length = max_length
        self.name = name
    
    def validate(self, value: Any) -> None:
        """Validate list length."""
        if not isinstance(value, list):
            raise ValueError(f"{self.name} must be a list")
        
        length = len(value)
        
        if length < self.min_length:
            raise ValueError(
                f"{self.name} must have at least {self.min_length} items, "
                f"got {length}"
            )
        
        if self.max_length is not None and length > self.max_length:
            raise ValueError(
                f"{self.name} must have at most {self.max_length} items, "
                f"got {length}"
            )


class FargateResourceValidator(IValidator):
    """Validates AWS Fargate resource combinations."""
    
    # Valid CPU/memory combinations for Fargate
    VALID_COMBINATIONS = {
        256: range(512, 2049, 512),      # 512, 1024, 1536, 2048
        512: range(1024, 4097, 1024),    # 1024, 2048, 3072, 4096
        1024: range(2048, 8193, 1024),   # 2048-8192 in 1GB increments
        2048: range(4096, 16385, 1024),  # 4096-16384 in 1GB increments
        4096: range(8192, 30721, 1024),  # 8192-30720 in 1GB increments
    }
    
    def validate(self, value: Any) -> None:
        """
        Validate Fargate CPU/memory combination.
        
        Args:
            value: Tuple of (cpu, memory)
        """
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError("Value must be a tuple of (cpu, memory)")
        
        cpu, memory = value
        
        if cpu not in self.VALID_COMBINATIONS:
            raise ValueError(
                f"Invalid CPU value: {cpu}. "
                f"Valid values: {list(self.VALID_COMBINATIONS.keys())}"
            )
        
        valid_memory_range = self.VALID_COMBINATIONS[cpu]
        if memory not in valid_memory_range:
            raise ValueError(
                f"Invalid memory {memory}MB for {cpu} CPU units. "
                f"Valid range: {valid_memory_range.start}-{valid_memory_range.stop-1}MB"
            )


class CompositeValidator(IValidator):
    """Combines multiple validators."""
    
    def __init__(self, validators: List[IValidator]):
        """
        Initialize composite validator.
        
        Args:
            validators: List of validators to apply
        """
        self.validators = validators
    
    def validate(self, value: Any) -> None:
        """Apply all validators."""
        for validator in self.validators:
            validator.validate(value)


class ValidationContext:
    """Context for managing validations - follows Open/Closed Principle."""
    
    def __init__(self):
        """Initialize validation context."""
        self._validators: List[Tuple[str, IValidator, Any]] = []
    
    def add_validation(self, name: str, validator: IValidator, value: Any) -> 'ValidationContext':
        """
        Add a validation to the context.
        
        Args:
            name: Name of the validation
            validator: Validator to use
            value: Value to validate
            
        Returns:
            Self for chaining
        """
        self._validators.append((name, validator, value))
        return self
    
    def validate_all(self) -> None:
        """
        Run all validations.
        
        Raises:
            ValueError: If any validation fails
        """
        errors = []
        
        for name, validator, value in self._validators:
            try:
                validator.validate(value)
            except ValueError as e:
                errors.append(f"{name}: {str(e)}")
        
        if errors:
            raise ValueError("Validation failed:\n" + "\n".join(errors))