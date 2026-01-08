# Mobile Loading Issue - Fix Instructions

## Problem
The PWA service worker was caching the homepage as a static file, causing mobile devices to fail loading with ERR_FAILED.

## Solution Applied
Updated the service worker to:
1. ✅ Removed homepage (`/`) from static cache list
2. ✅ Only cache truly static files (images, icons, manifest)
3. ✅ Cache CDN resources on-demand (not during installation)
4. ✅ Use network-first for all dynamic pages
5. ✅ Updated cache version to v2 (forces refresh)

## Deploy Steps

### 1. Upload Updated Files to PythonAnywhere
Upload these modified files:
- `static/service-worker.js` (main fix)
- `templates/index.html` (improved SW registration)

### 2. Clear Old Service Worker Cache

**Option A: Force refresh on PythonAnywhere**
```bash
# In PythonAnywhere console, touch the WSGI file to reload:
touch /var/www/<username>_pythonanywhere_com_wsgi.py
```

**Option B: Manual cache clear (recommended for users)**
Ask affected users to:
1. Go to browser settings
2. Clear browsing data → Cached images and files
3. Refresh the page

**Option C: Programmatic unregister (add to index.html temporarily)**
```javascript
// Add this temporarily to force unregister old SW
navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
        registration.unregister();
    }
});
```

### 3. Test on Mobile

1. **Clear app data on mobile:**
   - Android Chrome: Settings → Site settings → Storage → Clear
   - iOS Safari: Settings → Safari → Clear History and Website Data

2. **Test the homepage:**
   - Visit `https://filesharepro.pythonanywhere.com/`
   - Should load without errors
   - Check browser console (no SW errors)

3. **Verify static caching:**
   - Open DevTools → Application → Cache Storage
   - Should only see icons and manifest cached
   - Should NOT see homepage cached

## What Changed in Service Worker

### Before (Problematic):
```javascript
const STATIC_CACHE_URLS = [
  '/',  // ❌ Homepage - dynamic, shouldn't be cached
  '/static/manifest.json',
  // ... CDN URLs cached during install
];
```

### After (Fixed):
```javascript
const STATIC_CACHE_URLS = [
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon.svg'
  // CDN resources cached on-demand
];
```

### Cache Strategy Change:
- **Static files** (only .png, .jpg, .svg, .json, .css, .js in /static/): Cache-first
- **Everything else** (including homepage): Network-only
- **CDN resources**: Cache on-demand (first fetch)

## Verification

After deployment, verify:
- [ ] Homepage loads on mobile without errors
- [ ] PWA still installable
- [ ] Icons display correctly
- [ ] No console errors related to service worker
- [ ] Static resources load quickly (cached)
- [ ] Dynamic content always fresh (not cached)

## Rollback (if needed)

If issues persist, temporarily disable PWA:
1. Remove service worker registration from templates
2. Or serve empty service-worker.js:
```javascript
// Empty service worker to unregister
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => {
  self.clients.claim();
  caches.keys().then(keys => Promise.all(keys.map(key => caches.delete(key))));
});
```

## Notes
- The `?show_all=0` parameter works because it makes the page lighter
- The real issue was caching dynamic content as static
- New cache version (v2) automatically clears old caches
