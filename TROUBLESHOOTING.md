# Face Detector - Troubleshooting Guide

## Common Issues and Solutions

### 1. No Box Appears After Capture

**Problem:** After clicking "Capture Now", no colored box appears

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Camera not accessible | Check browser permissions (Allow camera) |
| JavaScript error | Open browser console (F12) and check for errors |
| Face not detected | Ensure face is clearly visible and centered |
| Response missing data | Verify Flask app is running the updated code |
| Canvas not rendering | Try different browser or hard refresh (Ctrl+Shift+R) |

**Debug Steps:**
1. Open Browser Console: Press `F12`
2. Check for errors (red text)
3. Try the capture again and watch console
4. Look for specific error messages

**Console Check Example:**
```javascript
// Check if response has required fields
console.log(data);
// Should show: { status: "logged", face_location: [...], match: true, ... }
```

---

### 2. Always Shows Red Box

**Problem:** Face is recognized but always shows red box

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Student not enrolled | Verify student is enrolled in system |
| Poor lighting | Ensure well-lit environment |
| Face angle wrong | Position face directly at camera |
| Recognition threshold too strict | Backend tolerance might be too high |

**Verification Steps:**
1. Check student is in enrollment list
2. Verify enrollment used same camera/lighting
3. Try enrollment again with better conditions
4. Check confidence scores (may be < 0.6)

**If confidence always low:**
- Check backend threshold: `if best_confidence >= 0.6:` in app.py
- Adjust if needed (be careful with security)

---

### 3. Always Shows Green Box (False Positives)

**Problem:** Different person's face shows green box

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| Recognition tolerance too loose | Backend threshold might be too low |
| Similar face features | Re-enroll with clearer, varied angles |
| Poor enrollment images | Use better quality enrollment photos |

**Security Verification:**
1. Verify match confidence is > 0.6
2. Check enrollment images are diverse
3. Test with different people
4. Monitor confidence scores

**Backend Check:**
```python
# In app.py line 615:
if best_confidence >= 0.6:  # Adjust if needed
```

---

### 4. Camera Permission Denied

**Problem:** Error message: "❌ Error accessing webcam"

**Solution by Browser:**

**Chrome/Edge:**
1. Look for camera icon in URL bar
2. Click "Reset permissions"
3. Reload page
4. Click "Allow" when prompted

**Firefox:**
1. Settings → Privacy → Permissions
2. Find "Camera" section
3. Remove site from blocked list
4. Reload page

**Safari:**
1. Safari → Settings → Privacy
2. Check "Camera" is allowed
3. Reload page

**Mobile Browsers:**
1. Check Settings → Privacy → Camera
2. Allow camera access for website
3. Reload page

---

### 5. "Multiple Faces Detected" Error

**Problem:** Error message when only one person visible

**Solution:**
- Remove other objects/reflections
- Clear background
- Ensure good lighting distinguishes face from background
- Move away from mirrors/windows
- Retry capture

**Detection Debug:**
If persistent, faces might be detected in background. Try:
1. Different room with plain background
2. Remove reflective surfaces
3. Better lighting to reduce shadows

---

### 6. No Face Detected

**Problem:** Camera works but "No face detected" error

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Face too small | Move closer to camera |
| Face partially out of frame | Position face in center |
| Poor lighting | Increase light, avoid harsh shadows |
| Sunglasses/hat | Remove to expose full face |
| Face at angle | Look directly at camera |

**Optimal Positioning:**
```
GOOD POSITION:           POOR POSITION:
┌──────────────┐         ┌──────────────┐
│              │         │   /          │
│   ● Face     │         │  ∟ Camera   │
│              │         │  (at angle) │
└──────────────┘         └──────────────┘

Good Lighting:           Poor Lighting:
┌──────────────┐         ┌──────────────┐
│ Light ◉      │         │   ☁ Dark    │
│      ● Face  │         │   ● Face    │
│              │         │   (shadows) │
└──────────────┘         └──────────────┘
```

---

### 7. Box Appears but Wrong Color

**Problem:** Box color doesn't match expected result

**Verification Steps:**
1. Check confidence displayed (should match result)
2. Verify student enrollment status
3. Check error message for reason
4. Compare with expected behavior

**Color Reference:**
- 🟩 **Green** = Confidence >= 0.6 AND matches student
- 🟥 **Red** = Any of:
  - Confidence < 0.6 (weak match)
  - Face doesn't match
  - Student not enrolled
  - Encoding failed

---

### 8. Browser Compatibility Issues

**Problem:** Feature doesn't work in certain browser

**Supported Browsers:**
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+
- ❌ Internet Explorer (not supported)

**Solution:**
1. Update browser to latest version
2. Try different browser
3. Clear cache (Ctrl+Shift+Del)
4. Disable extensions (might interfere)

**Browser Console Test:**
```javascript
// Check if APIs are available:
console.log('Canvas:', !!document.createElement('canvas').getContext);
console.log('getUserMedia:', !!navigator.mediaDevices?.getUserMedia);
console.log('Fetch:', !!fetch);
```

---

### 9. Performance Issues

**Problem:** Slow capture or delayed box rendering

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Slow computer | Close other apps |
| Poor network | Check internet connection |
| Large image size | Automatic (320x240 used) |
| Browser cache | Clear cache (Ctrl+Shift+Del) |

**Performance Check:**
1. Open DevTools: F12 → Performance tab
2. Capture and record
3. Check timing of steps
4. Look for slow operations

---

### 10. Data Not Saved to Database

**Problem:** Attendance marked (green box) but not in records

**Verification:**

1. **Check Flask console:**
   - Look for "Attendance logged" message
   - Check for database errors

2. **Verify database exists:**
   ```bash
   # Check if database file exists
   ls -la attendance.db
   ```

3. **Check database content:**
   - Use SQLite browser
   - Verify attendance_* tables exist

4. **Check environment variable:**
   ```bash
   # Verify DATABASE_URL if set
   echo $DATABASE_URL
   ```

**Database Troubleshooting:**
- If using CSV: Check `attendance_*.csv` files in project folder
- If using SQLite: Check `attendance.db` exists
- If using MySQL: Verify connection string in `DATABASE_URL`

---

## Debug Checklist

Use this when troubleshooting:

- [ ] Browser console shows no errors (F12)
- [ ] Camera permissions granted
- [ ] Face is clearly visible and centered
- [ ] Good lighting on face
- [ ] Student is enrolled (check with "Check Enrollment")
- [ ] Flask app is running
- [ ] Network connection is stable
- [ ] Browser is updated
- [ ] Canvas is rendering properly
- [ ] Response data is complete (check Network tab)

---

## Getting Help

**Before reporting issue, check:**

1. **Browser Console (F12):**
   ```
   Look for red error messages
   Note any JavaScript errors
   ```

2. **Flask Console:**
   ```
   Look for Python errors
   Check if face_locations detected
   Verify database operations
   ```

3. **Network Tab (F12):**
   - Check `/attendance` request
   - Verify response has all fields:
     - `face_location`
     - `match`
     - `confidence`

4. **Simple Test:**
   - Enroll known person
   - Capture same person
   - Should show green box
   - Should mark attendance

---

## Performance Optimization Tips

1. **Reduce image processing:**
   - Better lighting = faster detection
   - Clear background = faster processing

2. **Browser optimization:**
   - Close unused tabs
   - Disable extensions
   - Clear browser cache

3. **Network optimization:**
   - Use stable WiFi/Ethernet
   - Check bandwidth availability

4. **Computer optimization:**
   - Close unnecessary applications
   - Ensure adequate RAM (2GB+ recommended)
   - Update graphics drivers

---

## Quick Reset

If something seems broken:

1. **Hard refresh page:** `Ctrl + Shift + R`
2. **Clear browser cache:** `Ctrl + Shift + Del`
3. **Restart Flask app:** Stop and restart `python app.py`
4. **Clear browser data:** Developer Tools → Application → Clear Storage
5. **Try different browser:** Verify issue persists

---

## Emergency Fallback

If face detector doesn't work:

1. **Feature still optional** - old text-based feedback still works
2. **Attendance still records** - face detection is just visualization
3. **Can revert changes** - restore original files if needed
4. **Support remains** - other features unaffected

---

**Last Updated:** 2026-04-17  
**Status:** ✅ Ready to Help
