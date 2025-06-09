#!/usr/bin/env python3
"""
Example script demonstrating programmatic usage of the API Endpoint Scraper.

This script shows how to use the scraper components directly in your own code.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.scraper import WebScraper, EndpointExtractor, ReportGenerator
from src.config import config


async def basic_example():
    """Basic example of scanning a single URL."""
    print("🔍 Basic API Endpoint Discovery Example")
    print("=" * 50)
    
    # Target URL to scan
    target_url = "https://httpbin.org/"
    
    # Initialize components
    scraper = WebScraper()
    extractor = EndpointExtractor()
    generator = ReportGenerator()
    
    try:
        print(f"📡 Scraping: {target_url}")
        
        # Scrape the website (static scraping)
        content = await scraper.scrape_url(target_url, use_dynamic=False)
        
        if content.error:
            print(f"❌ Error: {content.error}")
            return
        
        print(f"✅ Scraped successfully!")
        print(f"   - Status: {content.status_code}")
        print(f"   - Response time: {content.response_time:.2f}s")
        print(f"   - HTML size: {len(content.html)} characters")
        print(f"   - JavaScript files: {len(content.javascript_content)}")
        
        # Extract API endpoints
        print(f"\n🎯 Extracting API endpoints...")
        endpoints = extractor.extract_endpoints(content)
        
        print(f"✅ Found {len(endpoints)} potential endpoints!")
        
        # Display discovered endpoints
        if endpoints:
            print(f"\n📋 Discovered Endpoints:")
            for i, endpoint in enumerate(endpoints, 1):
                confidence_pct = int(endpoint.confidence * 100)
                print(f"   {i}. {endpoint.method} {endpoint.url}")
                print(f"      Type: {endpoint.endpoint_type} | Confidence: {confidence_pct}% | Source: {endpoint.source}")
        
        # Generate report
        print(f"\n📄 Generating report...")
        report_file = generator.generate_report(endpoints, target_url, content.response_time)
        print(f"✅ Report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during scan: {e}")
    finally:
        await scraper.cleanup()


async def advanced_example():
    """Advanced example with custom configuration and dynamic scraping."""
    print("\n🚀 Advanced API Endpoint Discovery Example")
    print("=" * 50)
    
    # Customize configuration
    config.set('scraping.rate_limit', 0.5)  # Faster scanning
    config.set('output.format', 'html')     # HTML report
    config.set('output.min_confidence', 0.3)  # Lower confidence threshold
    
    target_url = "https://jsonplaceholder.typicode.com/"
    
    scraper = WebScraper()
    extractor = EndpointExtractor()
    generator = ReportGenerator()
    
    try:
        print(f"📡 Scraping with dynamic analysis: {target_url}")
        
        # Use dynamic scraping (Playwright) for JavaScript-heavy sites
        content = await scraper.scrape_url(target_url, use_dynamic=True)
        
        if content.error:
            print(f"❌ Error: {content.error}")
            return
        
        print(f"✅ Dynamic scraping completed!")
        print(f"   - Status: {content.status_code}")
        print(f"   - Response time: {content.response_time:.2f}s")
        print(f"   - Network requests captured: {len(content.network_requests)}")
        print(f"   - Cookies: {len(content.cookies)}")
        
        # Extract endpoints
        endpoints = extractor.extract_endpoints(content)
        
        print(f"\n🎯 Analysis Results:")
        print(f"   - Total endpoints found: {len(endpoints)}")
        
        # Group by type
        by_type = {}
        by_source = {}
        for ep in endpoints:
            by_type[ep.endpoint_type] = by_type.get(ep.endpoint_type, 0) + 1
            by_source[ep.source] = by_source.get(ep.source, 0) + 1
        
        print(f"   - By type: {dict(by_type)}")
        print(f"   - By source: {dict(by_source)}")
        
        # Generate multiple format reports
        print(f"\n📄 Generating reports in multiple formats...")
        report_files = generator.generate_multiple_formats(endpoints, target_url, content.response_time)
        
        print(f"✅ Reports generated:")
        for file_path in report_files:
            print(f"   📄 {file_path}")
        
    except Exception as e:
        print(f"❌ Error during advanced scan: {e}")
    finally:
        await scraper.cleanup()


async def batch_example():
    """Example of scanning multiple URLs."""
    print("\n📦 Batch Scanning Example")
    print("=" * 50)
    
    # List of URLs to scan
    urls = [
        "https://httpbin.org/",
        "https://jsonplaceholder.typicode.com/",
        "https://reqres.in/"
    ]
    
    scraper = WebScraper()
    extractor = EndpointExtractor()
    
    all_endpoints = []
    
    try:
        print(f"📡 Scanning {len(urls)} URLs...")
        
        # Scan all URLs
        for i, url in enumerate(urls, 1):
            print(f"\n   {i}/{len(urls)} Scanning: {url}")
            
            content = await scraper.scrape_url(url, use_dynamic=False)
            
            if content.error:
                print(f"      ❌ Error: {content.error}")
                continue
            
            endpoints = extractor.extract_endpoints(content)
            all_endpoints.extend(endpoints)
            
            print(f"      ✅ Found {len(endpoints)} endpoints")
        
        print(f"\n🎯 Batch Results:")
        print(f"   - Total URLs scanned: {len(urls)}")
        print(f"   - Total endpoints found: {len(all_endpoints)}")
        
        # Generate combined report
        generator = ReportGenerator()
        generator.output_file = "batch_results.json"
        report_file = generator.generate_report(all_endpoints, f"{len(urls)} URLs", 0)
        
        print(f"   📄 Combined report: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during batch scan: {e}")
    finally:
        await scraper.cleanup()


async def main():
    """Run all examples."""
    print("🔍 API Endpoint Discovery Scraper - Examples")
    print("=" * 60)
    
    # Run examples
    await basic_example()
    await advanced_example()
    await batch_example()
    
    print("\n✨ All examples completed!")
    print("\nNext steps:")
    print("1. Try the CLI: python cli.py scan https://your-target.com")
    print("2. Customize config/default.yaml for your needs")
    print("3. Check the generated reports")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 