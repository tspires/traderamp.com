"""
AWS Certificate Manager components following clean code principles.
"""

from typing import Dict, Optional, Any, List
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Output

from core.base_component import BaseInfrastructureComponent


class CertificateComponent(BaseInfrastructureComponent):
    """
    ACM Certificate component.
    
    Manages SSL/TLS certificates with DNS validation.
    """
    
    def __init__(
        self,
        name: str,
        domain_name: str,
        include_www: bool = True,
        validation_method: str = "DNS",
        **kwargs
    ):
        """Initialize certificate component."""
        self.domain_name = domain_name
        self.include_www = include_www
        self.validation_method = validation_method
        
        super().__init__(
            "traderamp:aws:certificates:Certificate",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate certificate configuration."""
        if not self.domain_name:
            raise ValueError("domain_name is required")
        
        if self.validation_method not in ["DNS", "EMAIL"]:
            raise ValueError("validation_method must be DNS or EMAIL")
    
    def create_resources(self) -> None:
        """Create certificate resources."""
        # Prepare domain names
        domain_names = [self.domain_name]
        if self.include_www and not self.domain_name.startswith("www."):
            domain_names.append(f"www.{self.domain_name}")
        
        # Create certificate
        certificate = aws.acm.Certificate(
            f"{self.name}-cert",
            domain_name=domain_names[0],
            subject_alternative_names=domain_names[1:] if len(domain_names) > 1 else [],
            validation_method=self.validation_method,
            tags=self.get_tags("Certificate", f"{self.name}-cert"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("certificate", certificate)
        
        # Handle DNS validation
        if self.validation_method == "DNS":
            self._setup_dns_validation(certificate)
    
    def _setup_dns_validation(self, certificate: aws.acm.Certificate) -> None:
        """Set up DNS validation for the certificate."""
        try:
            # Get hosted zone
            hosted_zone = aws.route53.get_zone(
                name=self._get_apex_domain(),
                private_zone=False
            )
            
            # Create validation records
            validation_records = []
            for i in range(len([self.domain_name] + (
                [f"www.{self.domain_name}"] if self.include_www else []
            ))):
                record = aws.route53.Record(
                    f"{self.name}-validation-{i}",
                    zone_id=hosted_zone.id,
                    name=certificate.domain_validation_options[i].resource_record_name,
                    type=certificate.domain_validation_options[i].resource_record_type,
                    ttl=60,
                    records=[certificate.domain_validation_options[i].resource_record_value],
                    allow_overwrite=True,
                    opts=ResourceOptions(parent=self)
                )
                validation_records.append(record)
            
            # Wait for validation
            validation = aws.acm.CertificateValidation(
                f"{self.name}-validation",
                certificate_arn=certificate.arn,
                validation_record_fqdns=[r.fqdn for r in validation_records],
                opts=ResourceOptions(parent=self, depends_on=validation_records)
            )
            self.add_resource("validation", validation)
            
        except Exception as e:
            pulumi.log.warn(
                f"Could not set up DNS validation for {self.domain_name}: {e}. "
                "You'll need to validate the certificate manually."
            )
    
    def _get_apex_domain(self) -> str:
        """Get apex domain from full domain name."""
        parts = self.domain_name.split(".")
        if len(parts) > 2:
            # Handle subdomains
            return ".".join(parts[-2:])
        return self.domain_name
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        certificate = self.get_resource("certificate")
        outputs = {
            "certificate_arn": certificate.arn,
            "domain_name": certificate.domain_name
        }
        
        validation = self.get_resource("validation")
        if validation:
            outputs["certificate_status"] = validation.certificate_arn
        
        return outputs