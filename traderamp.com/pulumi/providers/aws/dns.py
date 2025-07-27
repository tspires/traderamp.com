"""
AWS Route53 DNS components following clean code principles.
"""

from typing import Dict, Optional, Any
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Output, Input

from core.base_component import BaseInfrastructureComponent


class DNSComponent(BaseInfrastructureComponent):
    """
    Route53 DNS component.
    
    Manages DNS records for the application.
    """
    
    def __init__(
        self,
        name: str,
        domain_name: str,
        create_apex_record: bool = True,
        create_www_record: bool = True,
        **kwargs
    ):
        """Initialize DNS component."""
        self.domain_name = domain_name
        self.create_apex_record = create_apex_record
        self.create_www_record = create_www_record
        self.hosted_zone = None
        
        super().__init__(
            "traderamp:aws:dns:DNS",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate DNS configuration."""
        if not self.domain_name:
            raise ValueError("domain_name is required")
    
    def create_resources(self) -> None:
        """Create DNS resources."""
        try:
            # Get hosted zone
            self.hosted_zone = aws.route53.get_zone(
                name=self._get_apex_domain(),
                private_zone=False
            )
            self.add_resource("hosted_zone_id", self.hosted_zone.id)
            
        except Exception as e:
            pulumi.log.error(
                f"Could not find Route53 hosted zone for {self.domain_name}: {e}"
            )
            raise
    
    def create_alias_record(
        self,
        record_name: str,
        alias_name: Input[str],
        alias_zone_id: Input[str],
        record_type: str = "A",
        is_cloudfront: bool = False
    ) -> aws.route53.Record:
        """
        Create an alias record pointing to an AWS resource.
        
        Args:
            record_name: DNS record name
            alias_name: Target resource DNS name (e.g., ALB DNS)
            alias_zone_id: Target resource zone ID
            record_type: Record type (A or AAAA)
        """
        if not self.hosted_zone:
            raise ValueError("No hosted zone available")
        
        record = aws.route53.Record(
            f"{self.name}-{record_name.replace('.', '-')}",
            zone_id=self.hosted_zone.id,
            name=record_name,
            type=record_type,
            aliases=[{
                "name": alias_name,
                "zone_id": alias_zone_id,
                "evaluate_target_health": True
            }],
            opts=ResourceOptions(parent=self)
        )
        
        self.add_resource(f"record-{record_name}", record)
        return record
    
    def create_cname_record(
        self,
        record_name: str,
        target: str,
        ttl: int = 300
    ) -> aws.route53.Record:
        """
        Create a CNAME record.
        
        Args:
            record_name: DNS record name
            target: Target hostname
            ttl: Time to live in seconds
        """
        if not self.hosted_zone:
            raise ValueError("No hosted zone available")
        
        record = aws.route53.Record(
            f"{self.name}-{record_name.replace('.', '-')}",
            zone_id=self.hosted_zone.id,
            name=record_name,
            type="CNAME",
            ttl=ttl,
            records=[target],
            opts=ResourceOptions(parent=self)
        )
        
        self.add_resource(f"record-{record_name}", record)
        return record
    
    def _get_apex_domain(self) -> str:
        """Get apex domain from full domain name."""
        parts = self.domain_name.split(".")
        if len(parts) > 2 and parts[0] == "www":
            # Remove www prefix
            return ".".join(parts[1:])
        elif len(parts) > 2:
            # Handle other subdomains
            return ".".join(parts[-2:])
        return self.domain_name
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        outputs = {
            "domain_name": self.domain_name,
            "apex_domain": self._get_apex_domain()
        }
        
        if self.hosted_zone:
            outputs["hosted_zone_id"] = self.hosted_zone.id
        
        return outputs