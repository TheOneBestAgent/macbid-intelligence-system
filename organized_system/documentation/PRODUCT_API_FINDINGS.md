# MAC.BID Product API Discovery Report

## 🎯 **Key Product APIs Discovered**

### **1. Main Product Listing API**
```
GET https://api.macdiscount.com/auctionsummary?pg={page}&ppg={per_page}
```
- **Purpose**: Fetches paginated auction/product listings
- **Parameters**: 
  - `pg` = page number (1, 2, 3, ...)
  - `ppg` = products per page (typically 10)
- **Usage**: This is the primary API for loading product listings on the site
- **Frequency**: Called extensively during browsing (40+ calls observed)

### **2. User-Specific Product APIs**
```
GET https://api.macdiscount.com/auctions/customer/{customer_id}/active-auctions
GET https://api.macdiscount.com/auctions/customer/{customer_id}/auction-alerts
```
- **Purpose**: User-specific auction/product data
- **Customer ID**: `2845068` (your user ID)
- **Endpoints**:
  - `active-auctions`: Your current active auctions
  - `auction-alerts`: Your watchlist/alerts

### **3. Special Auction Types**
```
GET https://api.macdiscount.com/turbo-clock-auctions
```
- **Purpose**: Time-sensitive/special auction products
- **Usage**: Likely for featured or urgent auctions

### **4. Product Search API**
```
POST https://xczkhpt94lod37gqp.a1.typesense.net/multi_search
```
- **Purpose**: Advanced product search using Typesense search engine
- **Fields**: `product_name`, `description`, `keywords`, `upc`, `inventory_id`, `auction_title`
- **Usage**: Powers the search functionality when users search for products
- **Data Structure**: Vector-based search with embeddings

### **5. Real-time Product Updates**
```
POST https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel
```
- **Purpose**: Real-time updates for product/auction data
- **Database**: `projects/recommerce-a0291/databases/(default)`
- **Usage**: Live auction updates, bid changes, product status changes
- **Technology**: Google Firestore for real-time synchronization

## 🔍 **API Patterns & Architecture**

### **Domain Structure**
- **Main API**: `api.macdiscount.com` (primary product operations)
- **Search**: `xczkhpt94lod37gqp.a1.typesense.net` (search functionality)
- **Real-time**: `firestore.googleapis.com` (live updates)
- **Frontend**: `www.mac.bid` (user interface)

### **Authentication**
- Uses session-based authentication after login
- Customer ID (`2845068`) embedded in API calls
- Firebase authentication tokens for real-time features

### **Data Flow**
1. **Product Listings**: `api.macdiscount.com/auctionsummary` → Frontend display
2. **Search**: User query → Typesense → Search results
3. **Real-time**: Firestore → Live updates → Frontend
4. **User Data**: Customer-specific APIs → Personal dashboards

## 🎯 **Likely Product Addition APIs** (Not Yet Observed)

Based on the discovered patterns, the product addition APIs are likely:

### **Predicted Endpoints**
```
POST https://api.macdiscount.com/auctions          # Create new auction
POST https://api.macdiscount.com/products          # Add new product
PUT  https://api.macdiscount.com/auctions/{id}     # Update auction
POST https://api.macdiscount.com/inventory         # Add to inventory
```

### **Firestore Operations**
```
POST https://firestore.googleapis.com/.../documents/auctions
POST https://firestore.googleapis.com/.../documents/products
```

### **Search Index Updates**
```
POST https://xczkhpt94lod37gqp.a1.typesense.net/collections/products/documents
```

## 🔐 **Access Restrictions**

### **Why Product Addition APIs Weren't Found**
1. **Admin-Only Access**: Product addition likely restricted to admin users
2. **Different User Roles**: Your account may not have seller privileges
3. **Separate Admin Interface**: Could be on different subdomain (admin.mac.bid)
4. **API Gateway**: Creation APIs might be behind additional authentication

### **Next Steps to Find Creation APIs**
1. **Monitor Admin Areas**: Check admin/seller dashboards
2. **Network Monitoring**: Watch for POST/PUT requests during product actions
3. **API Documentation**: Look for Swagger/OpenAPI docs
4. **Reverse Engineering**: Analyze JavaScript for API calls

## 📊 **Technical Stack Identified**

### **Backend**
- **API Server**: Custom API at `api.macdiscount.com`
- **Database**: Google Firestore (`recommerce-a0291`)
- **Search**: Typesense (vector search engine)
- **Real-time**: Firebase/Firestore listeners

### **Frontend**
- **Framework**: Next.js (React-based)
- **Domain**: `www.mac.bid`
- **CDN**: `_next/static/` for assets

### **Third-Party Integrations**
- **Analytics**: Google Analytics, Mixpanel, TikTok Pixel
- **Payments**: Stripe
- **Marketing**: Facebook Pixel, Kargo, StackAdapt
- **Monitoring**: Various tracking pixels

## 🎯 **Recommendations for Finding Product Addition APIs**

### **1. Monitor Admin Interface**
```bash
python3 monitor_admin_apis.py
```

### **2. Direct API Testing**
Try common REST endpoints:
```bash
curl -X POST https://api.macdiscount.com/auctions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Product","description":"..."}'
```

### **3. JavaScript Analysis**
Look for API calls in the frontend JavaScript:
```bash
python3 cli.py scan https://mac.bid --dynamic --extract-js
```

### **4. Network Monitoring During Actions**
Monitor network traffic while:
- Browsing seller areas
- Attempting to create listings
- Interacting with product forms

## 📝 **Summary**

**Discovered**: 5 major product-related API endpoints
**Architecture**: Microservices with separate search, real-time, and main APIs
**Missing**: Product creation/addition endpoints (likely admin-restricted)
**Next**: Focus on admin areas and seller interfaces to find creation APIs 