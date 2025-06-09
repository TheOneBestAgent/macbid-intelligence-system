#!/usr/bin/env python3
"""
Example script demonstrating authentication usage with the API Endpoint Scraper.

This script shows how to use the scraper with login credentials to access
protected areas of websites and discover authenticated API endpoints.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.scraper import WebScraper, EndpointExtractor, ReportGenerator, create_auth_credentials


async def demo_authentication():
    """Demonstrate authentication capabilities."""
    print("🔐 API Endpoint Scraper - Authentication Demo")
    print("=" * 60)
    
    # Example 1: Form-based authentication
    print("\n📝 Example 1: Form-based Authentication")
    print("-" * 40)
    
    # Create authentication credentials
    auth_creds = create_auth_credentials(
        username="your_username",
        password="your_password",
        auth_type="form",
        login_url="https://example.com/login",  # Optional - will auto-detect if not provided
        username_field="email",  # Default is "username"
        password_field="password",  # Default is "password"
        success_indicators=["dashboard", "profile", "welcome", "logout"]  # What to look for after login
    )
    
    print(f"✅ Created credentials for: {auth_creds.username}")
    print(f"   Auth type: {auth_creds.auth_type}")
    print(f"   Login URL: {auth_creds.login_url}")
    print(f"   Success indicators: {auth_creds.success_indicators}")
    
    # Example 2: How to use with the scraper
    print("\n🔍 Example 2: Using Authentication with Scraper")
    print("-" * 50)
    
    scraper = WebScraper()
    extractor = EndpointExtractor()
    
    target_url = "https://httpbin.org/"  # Safe test site
    
    try:
        print(f"📡 Scanning: {target_url}")
        print("   (Note: httpbin.org doesn't require auth, this is just a demo)")
        
        # Scrape with authentication (will skip auth for httpbin.org)
        content = await scraper.scrape_url(
            url=target_url,
            use_dynamic=True,  # Required for authentication
            auth_credentials=auth_creds
        )
        
        if content.error:
            print(f"❌ Error: {content.error}")
        else:
            print(f"✅ Scraping successful!")
            print(f"   - Status: {content.status_code}")
            print(f"   - Response time: {content.response_time:.2f}s")
            print(f"   - Network requests captured: {len(content.network_requests)}")
            
            # Extract endpoints
            endpoints = extractor.extract_endpoints(content)
            print(f"   - Endpoints found: {len(endpoints)}")
            
            if endpoints:
                print("\n📋 Discovered Endpoints:")
                for i, endpoint in enumerate(endpoints[:5], 1):  # Show first 5
                    confidence_pct = int(endpoint.confidence * 100)
                    print(f"   {i}. {endpoint.method} {endpoint.url}")
                    print(f"      Confidence: {confidence_pct}% | Source: {endpoint.source}")
    
    except Exception as e:
        print(f"❌ Error during demo: {e}")
    finally:
        await scraper.cleanup()


async def demo_cli_usage():
    """Show CLI usage examples for authentication."""
    print("\n💻 CLI Usage Examples")
    print("=" * 30)
    
    examples = [
        {
            "title": "Basic form authentication",
            "command": "python3 cli.py scan https://example.com --dynamic --username 'user@example.com' --password 'mypassword'"
        },
        {
            "title": "With custom login URL",
            "command": "python3 cli.py scan https://example.com --dynamic --username 'user' --password 'pass' --login-url 'https://example.com/signin'"
        },
        {
            "title": "Authenticated scan with all formats",
            "command": "python3 cli.py scan https://app.example.com --dynamic --username 'user' --password 'pass' --all-formats"
        },
        {
            "title": "Scan with authentication and custom output",
            "command": "python3 cli.py scan https://api.example.com --dynamic -U 'user' -P 'pass' -o 'authenticated_endpoints.json'"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(f"   {example['command']}")


def demo_auth_types():
    """Show different authentication types supported."""
    print("\n🔑 Supported Authentication Types")
    print("=" * 40)
    
    auth_examples = [
        {
            "type": "Form Authentication",
            "description": "Standard HTML form login (most common)",
            "code": """
auth_creds = create_auth_credentials(
    username="user@example.com",
    password="mypassword",
    auth_type="form",
    login_url="https://example.com/login"
)"""
        },
        {
            "type": "Custom Field Names",
            "description": "For forms with non-standard field names",
            "code": """
auth_creds = create_auth_credentials(
    username="user@example.com",
    password="mypassword",
    auth_type="form",
    username_field="email",
    password_field="passwd",
    login_url="https://example.com/signin"
)"""
        },
        {
            "type": "Auto-Detection",
            "description": "Let the scraper find the login page automatically",
            "code": """
auth_creds = create_auth_credentials(
    username="user@example.com",
    password="mypassword",
    auth_type="form"
    # login_url will be auto-detected
)"""
        }
    ]
    
    for example in auth_examples:
        print(f"\n📌 {example['type']}")
        print(f"   {example['description']}")
        print(f"   Code example:{example['code']}")


async def main():
    """Run all authentication demos."""
    await demo_authentication()
    await demo_cli_usage()
    demo_auth_types()
    
    print("\n" + "=" * 60)
    print("🎯 Key Benefits of Authentication:")
    print("   • Access protected API endpoints")
    print("   • Discover user-specific endpoints")
    print("   • Find admin/dashboard APIs")
    print("   • Capture authenticated network requests")
    print("   • More comprehensive endpoint discovery")
    
    print("\n⚠️  Important Notes:")
    print("   • Always use --dynamic flag for authentication")
    print("   • Only use on sites you have permission to test")
    print("   • Authentication requires valid credentials")
    print("   • Some sites may have anti-automation measures")
    
    print("\n✨ Ready to discover authenticated endpoints!")


if __name__ == "__main__":
    asyncio.run(main()) 