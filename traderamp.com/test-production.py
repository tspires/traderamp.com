#!/usr/bin/env python3
"""
Production Test Suite for TradeRamp
Tests the deployed AWS infrastructure
"""

import requests
import time
from typing import Dict, List

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def test_endpoint(name: str, url: str, expected_status: int = 200, 
                 check_content: str = None) -> Dict:
    """Test a single endpoint"""
    print(f"\n{Colors.BLUE}Testing {name}...{Colors.END}")
    
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start
        
        result = {
            'url': url,
            'status': response.status_code,
            'time': elapsed,
            'success': response.status_code == expected_status
        }
        
        if check_content and result['success']:
            result['content_found'] = check_content in response.text
        else:
            result['content_found'] = None
            
        # Print results
        status_color = Colors.GREEN if result['success'] else Colors.RED
        print(f"  Status: {status_color}{response.status_code}{Colors.END} (expected {expected_status})")
        print(f"  Response Time: {elapsed:.3f}s")
        
        if check_content:
            content_color = Colors.GREEN if result.get('content_found') else Colors.RED
            content_status = "✓ Found" if result.get('content_found') else "✗ Not Found"
            print(f"  Content Check: {content_color}{content_status}{Colors.END}")
            
        return result
        
    except Exception as e:
        print(f"  {Colors.RED}Error: {e}{Colors.END}")
        return {
            'url': url,
            'status': 0,
            'time': 0,
            'success': False,
            'error': str(e)
        }

def test_seo_elements(url: str) -> Dict:
    """Test SEO elements on a page"""
    print(f"\n{Colors.BLUE}Testing SEO elements...{Colors.END}")
    
    try:
        response = requests.get(url, timeout=10)
        content = response.text
        
        checks = {
            'title': '<title>' in content and '</title>' in content,
            'meta_description': 'name="description"' in content,
            'h1_tag': '<h1' in content,
            'canonical': 'rel="canonical"' in content,
            'og_tags': 'property="og:' in content,
            'schema': 'application/ld+json' in content,
            'sitemap_ref': 'sitemap.xml' in content
        }
        
        for element, found in checks.items():
            color = Colors.GREEN if found else Colors.YELLOW
            status = "✓" if found else "⚠"
            print(f"  {color}{status} {element.replace('_', ' ').title()}{Colors.END}")
            
        return checks
        
    except Exception as e:
        print(f"  {Colors.RED}Error: {e}{Colors.END}")
        return {}

def run_production_tests():
    """Run all production tests"""
    print(f"\n{Colors.BOLD}=== TradeRamp Production Tests ==={Colors.END}")
    
    # Define endpoints
    base_alb = "http://traderamp-dev-alb-95b0200-1783108054.us-east-1.elb.amazonaws.com"
    base_cf = "https://d16blg9x9q03wx.cloudfront.net"
    
    # Test ALB endpoints
    print(f"\n{Colors.BOLD}1. Application Load Balancer Tests{Colors.END}")
    alb_tests = [
        ("ALB Homepage", f"{base_alb}/", 200, "Fill Your Calendar with High-Paying Jobs"),
        ("ALB Privacy Policy", f"{base_alb}/privacy-policy.html", 200, "Privacy Policy"),
        ("ALB Sitemap", f"{base_alb}/sitemap.xml", 200, "urlset"),
        ("ALB Robots.txt", f"{base_alb}/robots.txt", 200, "User-agent"),
        ("ALB Health Check", f"{base_alb}/health", 200, "OK"),
    ]
    
    alb_results = []
    for test in alb_tests:
        result = test_endpoint(*test)
        alb_results.append(result)
    
    # Test CloudFront
    print(f"\n{Colors.BOLD}2. CloudFront CDN Tests{Colors.END}")
    cf_tests = [
        ("CloudFront Homepage", f"{base_cf}/", 200, "TradeRamp"),
        ("CloudFront HTTPS Redirect", f"{base_cf}/", 200),
        ("CloudFront Caching", f"{base_cf}/assets/css/main.css", 200),
    ]
    
    cf_results = []
    for test in cf_tests:
        result = test_endpoint(*test)
        cf_results.append(result)
    
    # Test SEO
    print(f"\n{Colors.BOLD}3. SEO Implementation Tests{Colors.END}")
    seo_results = test_seo_elements(f"{base_alb}/")
    
    # Summary
    print(f"\n{Colors.BOLD}=== Test Summary ==={Colors.END}")
    
    total_tests = len(alb_results) + len(cf_results)
    passed_tests = sum(1 for r in alb_results + cf_results if r['success'])
    
    print(f"\nEndpoint Tests: {Colors.GREEN if passed_tests == total_tests else Colors.YELLOW}"
          f"{passed_tests}/{total_tests} passed{Colors.END}")
    
    seo_passed = sum(1 for v in seo_results.values() if v)
    seo_total = len(seo_results)
    print(f"SEO Elements: {Colors.GREEN if seo_passed == seo_total else Colors.YELLOW}"
          f"{seo_passed}/{seo_total} implemented{Colors.END}")
    
    # Performance
    avg_alb_time = sum(r['time'] for r in alb_results) / len(alb_results)
    avg_cf_time = sum(r['time'] for r in cf_results if r['time'] > 0) / len([r for r in cf_results if r['time'] > 0])
    
    print(f"\nPerformance:")
    print(f"  ALB Average Response: {avg_alb_time:.3f}s")
    print(f"  CloudFront Average Response: {avg_cf_time:.3f}s")
    
    # Overall status
    if passed_tests == total_tests and seo_passed == seo_total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All production tests passed!{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Some tests need attention{Colors.END}")

if __name__ == "__main__":
    run_production_tests()