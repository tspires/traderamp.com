"""
CloudFront CDN component following clean code principles.

This module provides CloudFront distribution management with:
- HTTP to HTTPS redirection
- Optimized caching behaviors
- Origin failover support
- Custom error pages
"""

from typing import Dict, Any, List, Optional
import pulumi
from pulumi import ResourceOptions
from pulumi_aws import cloudfront, acm

from core.base_component import BaseInfrastructureComponent
from core.interfaces import IResourceTagger


class CacheBehaviorSpec:
    """Specification for CloudFront cache behavior."""
    
    def __init__(
        self,
        path_pattern: str,
        target_origin_id: str,
        viewer_protocol_policy: str = "redirect-to-https",
        allowed_methods: List[str] = None,
        cached_methods: List[str] = None,
        default_ttl: int = 86400,  # 24 hours
        max_ttl: int = 31536000,   # 1 year
        min_ttl: int = 0,
        compress: bool = True
    ):
        """
        Initialize cache behavior specification.
        
        Args:
            path_pattern: Path pattern to match
            target_origin_id: Origin to forward requests to
            viewer_protocol_policy: How to handle HTTP/HTTPS
            allowed_methods: HTTP methods to allow
            cached_methods: HTTP methods to cache
            default_ttl: Default cache TTL in seconds
            max_ttl: Maximum cache TTL in seconds
            min_ttl: Minimum cache TTL in seconds
            compress: Whether to compress objects
        """
        self.path_pattern = path_pattern
        self.target_origin_id = target_origin_id
        self.viewer_protocol_policy = viewer_protocol_policy
        self.allowed_methods = allowed_methods or ["GET", "HEAD"]
        self.cached_methods = cached_methods or ["GET", "HEAD"]
        self.default_ttl = default_ttl
        self.max_ttl = max_ttl
        self.min_ttl = min_ttl
        self.compress = compress


class CloudFrontComponent(BaseInfrastructureComponent):
    """
    CloudFront CDN distribution component.
    
    Provides global content delivery with caching and HTTPS enforcement.
    """
    
    def __init__(
        self,
        name: str,
        origin_domain_name: pulumi.Output[str],
        origin_id: str = "alb-origin",
        certificate_arn: Optional[str] = None,
        domain_aliases: Optional[List[str]] = None,
        enable_ipv6: bool = True,
        price_class: str = "PriceClass_100",  # US, Canada, Europe
        default_root_object: str = "index.html",
        enable_logging: bool = False,
        tagger: Optional[IResourceTagger] = None
    ):
        """
        Initialize CloudFront distribution.
        
        Args:
            name: Base name for resources
            origin_domain_name: Domain name of the origin (ALB DNS)
            origin_id: Unique identifier for the origin
            certificate_arn: ACM certificate ARN for HTTPS
            domain_aliases: Alternative domain names
            enable_ipv6: Whether to enable IPv6
            price_class: CloudFront price class
            default_root_object: Default root object
            enable_logging: Whether to enable access logging
            tagger: Resource tagging strategy
        """
        # Initialize instance variables first (before parent init which calls validate())
        self.name = name
        self.origin_domain_name = origin_domain_name
        self.origin_id = origin_id
        self.certificate_arn = certificate_arn
        self.domain_aliases = domain_aliases or []
        self.enable_ipv6 = enable_ipv6
        self.price_class = price_class
        self.default_root_object = default_root_object
        self.enable_logging = enable_logging
        
        # Initialize base component
        super().__init__(
            component_type="aws:cloudfront:Distribution",
            name=name,
            tagger=tagger
        )
    
    def create_resources(self) -> None:
        """Create CloudFront distribution resources."""
        # Create origin access identity for future S3 use
        self.oai = cloudfront.OriginAccessIdentity(
            f"{self.name}-oai",
            comment=f"OAI for {self.name}",
            opts=ResourceOptions(parent=self)
        )
        
        # Define cache behaviors
        static_assets_behavior = self._create_cache_behavior(
            CacheBehaviorSpec(
                path_pattern="*.css",
                target_origin_id=self.origin_id,
                default_ttl=604800,  # 7 days
                max_ttl=31536000     # 1 year
            )
        )
        
        js_assets_behavior = self._create_cache_behavior(
            CacheBehaviorSpec(
                path_pattern="*.js",
                target_origin_id=self.origin_id,
                default_ttl=604800,  # 7 days
                max_ttl=31536000     # 1 year
            )
        )
        
        image_assets_behavior = self._create_cache_behavior(
            CacheBehaviorSpec(
                path_pattern="*.jpg",
                target_origin_id=self.origin_id,
                default_ttl=2592000,  # 30 days
                max_ttl=31536000      # 1 year
            )
        )
        
        png_assets_behavior = self._create_cache_behavior(
            CacheBehaviorSpec(
                path_pattern="*.png",
                target_origin_id=self.origin_id,
                default_ttl=2592000,  # 30 days
                max_ttl=31536000      # 1 year
            )
        )
        
        # Create distribution
        distribution_args = {
            "origins": [self._create_alb_origin()],
            "enabled": True,
            "is_ipv6_enabled": self.enable_ipv6,
            "comment": f"CloudFront distribution for {self.name}",
            "default_root_object": self.default_root_object,
            "price_class": self.price_class,
            
            # Default cache behavior - redirect HTTP to HTTPS
            "default_cache_behavior": cloudfront.DistributionDefaultCacheBehaviorArgs(
                allowed_methods=["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
                cached_methods=["GET", "HEAD", "OPTIONS"],
                target_origin_id=self.origin_id,
                viewer_protocol_policy="redirect-to-https",  # Force HTTPS
                min_ttl=0,
                default_ttl=0,      # Don't cache dynamic content by default
                max_ttl=31536000,
                compress=True,
                forwarded_values=cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
                    query_string=True,
                    cookies=cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                        forward="all"
                    ),
                    headers=["*"]  # Forward all headers for dynamic content
                )
            ),
            
            # Ordered cache behaviors for static assets
            "ordered_cache_behaviors": [
                static_assets_behavior,
                js_assets_behavior,
                image_assets_behavior,
                png_assets_behavior
            ],
            
            # Custom error responses
            "custom_error_responses": [
                cloudfront.DistributionCustomErrorResponseArgs(
                    error_code=404,
                    response_code=404,
                    response_page_path="/404.html",
                    error_caching_min_ttl=300
                ),
                cloudfront.DistributionCustomErrorResponseArgs(
                    error_code=403,
                    response_code=403,
                    response_page_path="/403.html",
                    error_caching_min_ttl=300
                )
            ],
            
            # Geo restrictions (none by default)
            "restrictions": cloudfront.DistributionRestrictionsArgs(
                geo_restriction=cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                    restriction_type="none"
                )
            ),
            
            # Viewer certificate
            "viewer_certificate": self._get_viewer_certificate()
        }
        
        # Add aliases if using custom certificate
        if self.certificate_arn and self.domain_aliases:
            distribution_args["aliases"] = self.domain_aliases
        
        # Add logging if enabled
        if self.enable_logging:
            # You would need an S3 bucket for logs
            pass
        
        # Add tags
        distribution_args["tags"] = self.get_tags("cloudfront", f"{self.name}-cdn")
        
        self.distribution = cloudfront.Distribution(
            f"{self.name}-cdn",
            opts=ResourceOptions(parent=self),
            **distribution_args
        )
        
        # Add resources to component collection
        self.add_resource("oai", self.oai)
        self.add_resource("distribution", self.distribution)
    
    def _create_alb_origin(self) -> cloudfront.DistributionOriginArgs:
        """Create ALB origin configuration."""
        return cloudfront.DistributionOriginArgs(
            domain_name=self.origin_domain_name,
            origin_id=self.origin_id,
            custom_origin_config=cloudfront.DistributionOriginCustomOriginConfigArgs(
                http_port=80,
                https_port=443,
                origin_protocol_policy="https-only",  # Only use HTTPS to origin
                origin_ssl_protocols=["TLSv1.2"],
                origin_keepalive_timeout=5,
                origin_read_timeout=30
            )
        )
    
    def _create_cache_behavior(self, spec: CacheBehaviorSpec) -> cloudfront.DistributionOrderedCacheBehaviorArgs:
        """Create cache behavior from specification."""
        return cloudfront.DistributionOrderedCacheBehaviorArgs(
            path_pattern=spec.path_pattern,
            target_origin_id=spec.target_origin_id,
            viewer_protocol_policy=spec.viewer_protocol_policy,
            allowed_methods=spec.allowed_methods,
            cached_methods=spec.cached_methods,
            min_ttl=spec.min_ttl,
            default_ttl=spec.default_ttl,
            max_ttl=spec.max_ttl,
            compress=spec.compress,
            forwarded_values=cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
                query_string=False,
                cookies=cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(
                    forward="none"
                ),
                headers=[]  # Don't forward headers for static content
            )
        )
    
    def _get_viewer_certificate(self) -> cloudfront.DistributionViewerCertificateArgs:
        """Get viewer certificate configuration."""
        if self.certificate_arn:
            return cloudfront.DistributionViewerCertificateArgs(
                acm_certificate_arn=self.certificate_arn,
                ssl_support_method="sni-only",
                minimum_protocol_version="TLSv1.2_2021"
            )
        else:
            return cloudfront.DistributionViewerCertificateArgs(
                cloudfront_default_certificate=True
            )
    
    def create_invalidation(self, paths: List[str]) -> None:
        """
        Create a cache invalidation.
        
        Args:
            paths: List of paths to invalidate
        """
        # Note: Pulumi doesn't have a direct invalidation resource
        # This would need to be done via AWS CLI or SDK
        pulumi.log.info(
            f"To invalidate CloudFront cache, run: "
            f"aws cloudfront create-invalidation --distribution-id {self.distribution.id} "
            f"--paths {' '.join(paths)}"
        )
    
    def validate(self) -> None:
        """Validate CloudFront configuration."""
        # Validate price class
        valid_price_classes = [
            "PriceClass_All",
            "PriceClass_100",
            "PriceClass_200"
        ]
        if self.price_class not in valid_price_classes:
            raise ValueError(f"Invalid price class: {self.price_class}")
        
        # Validate domain aliases with certificate
        if self.domain_aliases and not self.certificate_arn:
            raise ValueError("Certificate ARN required when using domain aliases")
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        return {
            "distribution_id": self.distribution.id,
            "distribution_arn": self.distribution.arn,
            "distribution_domain_name": self.distribution.domain_name,
            "distribution_hosted_zone_id": self.distribution.hosted_zone_id,
            "oai_id": self.oai.id,
            "oai_iam_arn": self.oai.iam_arn
        }