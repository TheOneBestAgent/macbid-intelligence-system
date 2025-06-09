# 🔐 API Token Capture Guide for Mac.bid

## What You Just Captured

The cURL command you provided is an **OPTIONS request** (preflight request). This is good news because it shows:

✅ **Authorization header is required** (`access-control-request-headers: authorization,content-type`)  
✅ **Your browser has access** to make authenticated requests  
✅ **The endpoint exists** and is accessible  

## Next Steps: Capture the Actual GET Request

### 1. 🌐 Open Mac.bid in Browser
- Go to https://www.mac.bid
- Log in with your account (darvonmedia@gmail.com)

### 2. 🛠️ Open Developer Tools
- Press **F12** (or **Cmd+Option+I** on Mac)
- Click on **"Network"** tab
- ✅ **Check "Preserve log"** (important!)
- 🗑️ **Clear the network log** (click the clear button)

### 3. 🎯 Navigate to Personal Data Pages
Navigate to pages that load your personal auction data:
- **Account/Profile page**
- **Bid History page**
- **Purchase History/Invoices page**
- **Watch List page**
- **Any page showing your personal auction data**

### 4. 📡 Find the Authenticated API Call
Look for network requests to:
- `api.macdiscount.com`
- Specifically: `/user/2710619/invoices` or `/user/2710619/invoices-items`
- **Method: GET** (not OPTIONS)
- **Status: 200** (successful)

### 5. 🔍 Identify the Right Request
The correct request will:
- ✅ Be a **GET request** (not OPTIONS)
- ✅ Have **Status 200**
- ✅ Return actual data (not empty)
- ✅ Have an **Authorization header**

### 6. 📋 Copy the Authenticated Request
Right-click on the **GET request** → **Copy** → **Copy as cURL**

### 7. 🔐 What to Look For
The authenticated cURL should include headers like:
```bash
-H 'authorization: Bearer [long-token-string]'
# OR
-H 'authorization: [token-string]'
# OR
-H 'cookie: auth_token=[token]; session_id=[session]'
```

## 🎯 Target Endpoints to Find

Look for these specific API calls in the Network tab:

1. **Invoices**: `/user/2710619/invoices?pg=1`
2. **Invoice Items**: `/user/2710619/invoices-items?pg=1&ppg=30`
3. **Bid History**: `/user/2710619/getBidHistory?pg=1&ppg=25`
4. **Watch List**: `/user/2710619/getWatchList`
5. **My Bids**: `/auction/getMyBids?pg=1&ppg=25`

## 🚨 Common Issues & Solutions

### Issue: Only seeing OPTIONS requests
**Solution**: Navigate to more pages, refresh the page, or click on different sections

### Issue: No Authorization header visible
**Solution**: 
- Make sure you're logged in
- Try different pages (Profile, Bid History, etc.)
- Look for cookies with token-like names

### Issue: 401/403 errors in Network tab
**Solution**: 
- Log out and log back in
- Clear browser cache
- Try incognito/private browsing mode

## 💡 Pro Tips

1. **Filter by domain**: In Network tab, filter by "macdiscount.com"
2. **Look for XHR/Fetch requests**: These are usually the API calls
3. **Check Response tab**: Successful requests will show your actual data
4. **Multiple attempts**: Try navigating to different personal pages

## 🎯 Once You Have the Authenticated cURL

Run this command with your captured cURL:
```bash
python3 capture_browser_tokens.py
```

Then paste the **authenticated GET request** (not the OPTIONS request).

## 📞 Need Help?

If you're having trouble finding the authenticated request:
1. Try visiting your "Account" or "Profile" page
2. Look for any page that shows your purchase history
3. Check the "My Bids" or "Bid History" sections
4. The authenticated request should appear when these pages load your personal data

---

**Remember**: We need the **GET request with Authorization header**, not the OPTIONS preflight request! 