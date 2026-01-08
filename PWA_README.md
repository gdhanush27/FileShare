# PWA (Progressive Web App) Support

FileShare Pro now supports PWA functionality, allowing users to install the app on their devices and use it with offline capabilities for static resources.

## Features

### ✅ Installable
- Users can install the app on their desktop or mobile devices
- App appears in the device's app drawer/home screen
- Standalone window mode (no browser chrome)

### ✅ Offline Support (Static Files Only)
The service worker caches:
- Static assets (CSS, JS, icons)
- CDN resources (Bootstrap, Bootstrap Icons)
- Homepage structure

**Note**: File uploads, downloads, and dynamic content require an active internet connection.

### ✅ Custom App Icon
- Custom file-sharing themed icon in brand colors (#4F46E5)
- Multiple sizes (192x192, 512x512) for various devices
- SVG source file included for modifications

## Installation

### Desktop (Chrome/Edge)
1. Visit the app in Chrome or Edge
2. Look for the install icon (⊕) in the address bar
3. Click "Install" in the prompt
4. App will open in standalone window

### Mobile (Android/iOS)
**Android:**
1. Open the app in Chrome
2. Tap the menu (⋮) → "Add to Home screen"
3. Follow the prompt to install

**iOS (Safari):**
1. Open the app in Safari
2. Tap the Share button
3. Scroll and tap "Add to Home Screen"
4. Name the app and tap "Add"

## Technical Details

### Files Created
- `/static/manifest.json` - PWA manifest with app metadata
- `/static/service-worker.js` - Service worker for caching strategy
- `/static/icons/icon.svg` - Source SVG icon
- `/static/icons/icon-192.png` - 192x192 PNG icon
- `/static/icons/icon-512.png` - 512x512 PNG icon
- `/generate_icons.py` - Script to regenerate icons from SVG

### Caching Strategy
- **Static files**: Cache-first (serves from cache, falls back to network)
- **Dynamic content**: Network-only (always fetches fresh data)
- **Offline fallback**: Basic offline page for document requests

### Service Worker Scope
- Caches: `/static/*`, CDN resources, homepage
- Network-only: Uploads, downloads, API calls, user data

## Customization

### Changing App Icon
1. Edit `/static/icons/icon.svg` with your design
2. Run `python generate_icons.py` to regenerate PNG files
3. Icons will be updated automatically

### Updating Manifest
Edit `/static/manifest.json` to change:
- App name and description
- Theme colors
- Shortcuts
- Display mode

### Modifying Cache Strategy
Edit `/static/service-worker.js`:
- Update `STATIC_CACHE_URLS` to add/remove cached files
- Modify fetch event handler to change caching behavior
- Update cache version (`CACHE_NAME`) when making changes

## Browser Support
- ✅ Chrome/Edge (desktop & mobile)
- ✅ Firefox (desktop & mobile)
- ⚠️ Safari (limited - no install prompt, but works as web app)
- ✅ Opera
- ✅ Samsung Internet

## Testing PWA
1. Open DevTools (F12)
2. Go to "Application" tab
3. Check:
   - Manifest: Should show app details
   - Service Workers: Should show registered worker
   - Cache Storage: Should show cached files

## Troubleshooting

### App not installable?
- Ensure HTTPS is enabled (required for PWA)
- Check browser console for manifest/service worker errors
- Verify all icon files exist

### Service Worker not registering?
- Check browser console for errors
- Verify `/service-worker.js` route is accessible
- Clear browser cache and try again

### Icons not displaying?
- Ensure PNG files were generated (run `generate_icons.py`)
- Check file permissions in `/static/icons/`
- Verify paths in `manifest.json` are correct
