# Face Detector Feature - Technical Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Session ID: ________    Student ID: ________                   │
│  [ Check Enrollment ]                                           │
│                                                                   │
│  ┌─ Camera Feed ──────────────────────────────────┐             │
│  │                                                │             │
│  │    Live Video (320x240)                        │             │
│  │    ┌──────────────────────────────────┐        │             │
│  │    │                                  │        │             │
│  │    │        📹 Live Stream            │        │             │
│  │    │                                  │        │             │
│  │    └──────────────────────────────────┘        │             │
│  │          Canvas Overlay (Hidden)               │             │
│  │                                                │             │
│  │  Status: [ Face confidence: -- ]              │             │
│  │                                                │             │
│  └────────────────────────────────────────────────┘             │
│                                                                   │
│  [ 🔒 Start Attendance Check ]  [ 📷 Capture Now ]             │
│                                                                   │
│  Result: _________________________________                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Capture Process Flow

```
User Clicks
"Capture Now"
      ↓
┌─────────────────────────────────┐
│ JavaScript captures frame from  │
│ video element                   │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│ Converts to Blob (JPEG)         │
│ Adds session_id & student_id    │
└─────────────────────────────────┘
      ↓
    POST /attendance
      ↓
┌─────────────────────────────────────────────────────┐
│        FLASK BACKEND (app.py)                       │
├─────────────────────────────────────────────────────┤
│ 1. Load image                                       │
│ 2. Detect face locations using face_recognition    │
│ 3. Validate single face (security check)          │
│ 4. Get face encodings                              │
│ 5. Compare with student embeddings                 │
│ 6. Calculate confidence score                      │
│ 7. Return response with face_location & match flag │
└─────────────────────────────────────────────────────┘
      ↓
    Response:
    {
      "status": "logged",
      "match": true,
      "confidence": 0.89,
      "face_location": [50, 200, 150, 100]
    }
      ↓
┌─────────────────────────────────────────────────────┐
│        JAVASCRIPT RENDERING                        │
├─────────────────────────────────────────────────────┤
│ 1. Check if face_location exists                    │
│ 2. Call drawFaceBox(location, match, confidence)   │
│ 3. Clear canvas                                     │
│ 4. Draw bounding box (Green or Red)                │
│ 5. Draw corner markers                              │
│ 6. Update status indicator                          │
│ 7. Display result message                           │
└─────────────────────────────────────────────────────┘
      ↓
┌────────────────────────────────────────────────────┐
│  ✅ GREEN BOX      OR      ❌ RED BOX             │
│  ✅ MATCH (89.5%)   OR     ❌ NO MATCH            │
│  ✅ Success msg     OR     ❌ Error msg           │
└────────────────────────────────────────────────────┘
```

## Data Structure

### Request
```javascript
FormData {
  "session_id": "SESSION123",
  "student_id": "12345",
  "image": Blob (JPEG)
}
```

### Response
```json
{
  "status": "logged|not_recognized|low_confidence|not_enrolled|security_failed",
  "message": "...",
  "confidence": 0.89,
  "student_id": "12345",
  "face_location": [50, 200, 150, 100],
  "match": true|false
}
```

## Face Location Coordinates

```
face_location = [top, right, bottom, left]

    0        x        right
    ┌─────────────────────┐ 0
    │                     │
    │   top               │
    │   ┌─────────────┐   │
    │   │             │   │
  y │   │  FACE       │   │ height
    │   │             │   │
    │   │  bottom     │   │
    │   └─────────────┘   │
    │                     │
    └─────────────────────┘

Bounding Box Calculation:
  width = right - left
  height = bottom - top

Canvas Drawing:
  ctx.strokeRect(left, top, width, height)
```

## Green Box (Match)

```
┌─────────────────────────┐
│ ■                     ■ │  ← Top corners (filled)
│                         │
│    ╭─────────────╮      │
│    │             │      │  ← Green box (#00CC00)
│    │   Face ✅   │      │  ← Line width: 3px
│    │             │      │
│    ╰─────────────╯      │
│                         │
│ ■                     ■ │  ← Bottom corners (filled)
└─────────────────────────┘

Status Display:
✅ MATCH (89.5%)
Color: #28a745 (Green)
```

## Red Box (No Match)

```
┌─────────────────────────┐
│ ■                     ■ │  ← Top corners (filled)
│                         │
│    ╭─────────────╮      │
│    │             │      │  ← Red box (#FF0000)
│    │   Face ❌   │      │  ← Line width: 3px
│    │             │      │
│    ╰─────────────╯      │
│                         │
│ ■                     ■ │  ← Bottom corners (filled)
└─────────────────────────┘

Status Display:
❌ NO MATCH
Color: #dc3545 (Red)
```

## Component Interaction

```
┌─────────────────────────────────────────────────────┐
│              BROWSER (Frontend)                     │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐       ┌──────────────┐           │
│  │ getUserMedia │───→   │   HTMLVideo  │           │
│  │   (Camera)   │       │   Element    │           │
│  └──────────────┘       └──────────────┘           │
│                              ↓                      │
│  ┌──────────────┐       ┌──────────────┐           │
│  │ HTMLCanvas   │←──────│ drawImage()  │           │
│  │ (Overlay)    │       │              │           │
│  └──────────────┘       └──────────────┘           │
│        ↑                                            │
│        │                                            │
│  ┌──────────────────────────────┐                  │
│  │ drawFaceBox(location, match) │                  │
│  │ - strokeRect() [Green/Red]   │                  │
│  │ - fillRect() [corners]       │                  │
│  │ - Update status text         │                  │
│  └──────────────────────────────┘                  │
└──────────────────┬───────────────────────────────┘
                   │
                   │ FormData
                   ↓
┌─────────────────────────────────────────────────────┐
│           FLASK SERVER (Backend)                    │
├─────────────────────────────────────────────────────┤
│  ┌────────────────────────────────┐                │
│  │ POST /attendance               │                │
│  ├────────────────────────────────┤                │
│  │ 1. face_recognition.load()     │                │
│  │ 2. face_recognition.detect()   │                │
│  │ 3. face_recognition.encode()   │                │
│  │ 4. compare_faces()             │                │
│  │ 5. face_distance()             │                │
│  │ 6. Calculate confidence        │                │
│  └────────────────────────────────┘                │
│                │                                   │
│                ↓                                   │
│  ┌────────────────────────────────┐                │
│  │ JSON Response:                 │                │
│  │ - status                       │                │
│  │ - match: true|false            │                │
│  │ - confidence: 0.0-1.0          │                │
│  │ - face_location: [t,r,b,l]     │                │
│  └────────────────────────────────┘                │
└──────────────────┬───────────────────────────────┘
                   │
                   │ JSON Response
                   ↓
         Browser renders box
              & updates UI
```

## Edge Cases Handled

```
CASE 1: No Face Detected
  └─ Security check fails
  └─ face_location = null
  └─ No box drawn (safety feature)
  └─ Error message shown

CASE 2: Multiple Faces
  └─ Security check fails
  └─ face_location = null
  └─ No box drawn (only 1 person allowed)
  └─ Error message shown

CASE 3: Student Not Enrolled
  └─ face_location returned
  └─ match = false
  └─ Red box drawn
  └─ "Not enrolled" message

CASE 4: Low Confidence Match
  └─ face_location returned
  └─ match = false
  └─ Red box drawn (confidence < 0.6)
  └─ "Try again" message

CASE 5: Successful Match
  └─ face_location returned
  └─ match = true
  └─ Green box drawn
  └─ Attendance marked
  └─ Success message
```

---

**Architecture Design:** ✅ Complete  
**Implementation:** ✅ Ready for Production
