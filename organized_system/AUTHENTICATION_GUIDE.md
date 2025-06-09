# 🔐 Mac.bid Authentication Guide

## Overview

**ALL SCRIPTS NOW REQUIRE AUTHENTICATION** before performing any Mac.bid operations. This ensures secure access to your account data and prevents unauthorized API usage.

## 🚨 CRITICAL REQUIREMENT

Every Python script that interacts with Mac.bid **MUST** call `require_authentication()` before any other operations. Scripts will fail safely if authentication is missing.

## 📁 Authentication Files

The authentication system uses two files in `~/.macbid_scraper/`:

### 1. `api_tokens.json`
```json
{
  "customer_id": "2710619",
  "tokens": {
    "authorization": "Bearer YOUR_JWT_TOKEN_HERE"
  },
  "timestamp": 1749215352
}
```

### 2. `authenticated_session.json`
Contains session cookies and authentication state from your browser session.

## 🔧 How to Use Authentication

### Basic Pattern (Required for ALL scripts):

```python
#!/usr/bin/env python3
import asyncio
import sys

# Import authentication manager (REQUIRED FIRST)
sys.path.append('.')
from core_systems.authentication_manager import require_authentication, get_authenticated_headers, get_customer_id

async def main():
    # STEP 1: AUTHENTICATE FIRST (MANDATORY)
    try:
        auth_manager = await require_authentication()
        headers = get_authenticated_headers()
        customer_id = get_customer_id()
        print(f"✅ Authenticated as Customer ID: {customer_id}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # STEP 2: Now you can safely use Mac.bid APIs
    # Your script logic here...

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛡️ Security Features

### 1. **Mandatory Authentication**
- Scripts cannot access Mac.bid APIs without authentication
- `get_authenticated_headers()` and `get_customer_id()` will fail if not authenticated
- Prevents accidental unauthorized access

### 2. **Session Verification**
- Authentication is verified against Mac.bid servers
- Invalid tokens are detected and rejected
- Automatic session validation

### 3. **Secure Credential Storage**
- JWT tokens stored in `~/.macbid_scraper/` directory
- Session cookies managed securely
- Customer ID validation

## 📊 Authentication Status

Check authentication status:

```python
auth_manager = await require_authentication()
status = auth_manager.get_auth_status()
print(status)
```

Returns:
```python
{
    'is_authenticated': True,
    'customer_id': '2710619',
    'has_jwt_token': True,
    'has_session_cookies': True,
    'auth_timestamp': 1749335864.678826,
    'is_expired': False,
    'headers_configured': True
}
```

## 🔄 Updated Scripts

The following scripts have been updated to require authentication:

### Core Systems:
- ✅ `parallel_discovery_system.py` - Parallel multi-source discovery
- ✅ `authentication_manager.py` - Authentication management

### Testing & Debugging:
- ✅ `verify_bid_data.py` - Bid data verification
- ✅ `test_authentication_requirement.py` - Authentication testing

### Discovery Systems:
- 🔄 `typesense_all_lots_scanner.py` - Needs update
- 🔄 `comprehensive_warehouse_scanner.py` - Needs update
- 🔄 `nextjs_integration_system.py` - Needs update

### ML & Analytics:
- 🔄 `enhanced_ml_models.py` - Needs update
- 🔄 `portfolio_management_system.py` - Needs update
- 🔄 `integrated_auction_system.py` - Needs update

## 🚀 Quick Start

1. **Ensure credentials are in place:**
   ```bash
   ls ~/.macbid_scraper/
   # Should show: api_tokens.json  authenticated_session.json
   ```

2. **Test authentication:**
   ```bash
   python3 core_systems/authentication_manager.py
   ```

3. **Run any script with authentication:**
   ```bash
   python3 testing_debugging/test_authentication_requirement.py
   ```

## ❌ What Happens Without Authentication

Scripts will fail safely with clear error messages:

```
❌ Not authenticated. Call require_authentication() first.
❌ AUTHENTICATION REQUIRED: Cannot proceed without valid Mac.bid authentication
```

## 🔧 Troubleshooting

### Problem: "No module named 'core_systems'"
**Solution:** Ensure you're running from the correct directory or add proper path:
```python
sys.path.append('.')
sys.path.append('..')
```

### Problem: "Authentication failed"
**Solution:** Check that credential files exist and contain valid data:
```bash
cat ~/.macbid_scraper/api_tokens.json
cat ~/.macbid_scraper/authenticated_session.json
```

### Problem: "JWT token expired"
**Solution:** Re-authenticate by updating the JWT token in `api_tokens.json`

## 🎯 Benefits

1. **Security**: Prevents unauthorized access to your Mac.bid account
2. **Reliability**: Ensures all API calls use valid authentication
3. **Debugging**: Clear error messages when authentication fails
4. **Consistency**: Standardized authentication across all scripts
5. **Safety**: Scripts fail safely rather than proceeding without auth

## 📝 Next Steps

1. Update remaining scripts to use authentication
2. Test all scripts with the new authentication requirement
3. Verify that bid data verification works with authenticated sessions
4. Ensure all discovery systems use authenticated headers

---

**Remember: EVERY script that touches Mac.bid APIs must call `require_authentication()` first!** 🔐 