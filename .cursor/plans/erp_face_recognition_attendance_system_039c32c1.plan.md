---
name: ERP Face Recognition Attendance System
overview: Build a production-ready attendance management system with face recognition featuring employee registration (face enrollment) and daily attendance tracking (face verification). Uses FastAPI backend with PostgreSQL+pgvector, MediaPipe for client-side face detection, and SFace (OpenCV) for server-side face recognition.
todos:
  - id: phase1-foundation
    content: Set up FastAPI project structure, PostgreSQL with pgvector, database models, and configuration management
    status: pending
  - id: phase2-face-recognition
    content: Integrate SFace model (OpenCV), create embedding generation service, and image preprocessing utilities
    status: pending
    dependencies:
      - phase1-foundation
  - id: phase3-vector-search
    content: Implement vector similarity search using pgvector with cosine similarity and proper indexing
    status: pending
    dependencies:
      - phase1-foundation
      - phase2-face-recognition
  - id: phase4-api-endpoints
    content: Create all REST API endpoints for employee registration, face enrollment, and attendance tracking
    status: pending
    dependencies:
      - phase1-foundation
      - phase2-face-recognition
      - phase3-vector-search
  - id: phase5-client-ui
    content: Set up React app with Vite, create Face ID-style interface components with CSS modules
    status: pending
  - id: phase6-mediapipe
    content: Integrate MediaPipe Face Detection with React hooks (useFaceDetection, useCamera) for real-time face detection overlay
    status: pending
    dependencies:
      - phase5-client-ui
  - id: phase7-quality-checks
    content: Implement client-side quality checks as React hook (useQualityChecks) with visual feedback components
    status: pending
    dependencies:
      - phase6-mediapipe
  - id: phase8-liveness
    content: Implement liveness detection as React hook (useLivenessDetection) with user instructions component
    status: pending
    dependencies:
      - phase6-mediapipe
  - id: phase9-auto-capture
    content: Build auto-capture logic as React hook (useAutoCapture) that triggers when all quality checks pass and liveness is complete
    status: pending
    dependencies:
      - phase7-quality-checks
      - phase8-liveness
  - id: phase10-integration
    content: Create React components for registration and attendance workflows, connect to API endpoints using service layer
    status: pending
    dependencies:
      - phase4-api-endpoints
      - phase9-auto-capture
  - id: phase11-testing
    content: End-to-end testing, edge case handling, performance validation, and mobile device testing
    status: pending
    dependencies:
      - phase10-integration
  - id: phase12-documentation
    content: Create comprehensive README, API documentation, and code comments
    status: pending
    dependencies:
      - phase11-testing
---

# ERP Attendance System with Face Recognition - Implementation Plan

## Architecture Overview

The system consists of:

- **Client**: React web app with MediaPipe Face Detection for real-time face capture and quality validation
- **Backend**: FastAPI server with SFace (OpenCV) for face recognition and PostgreSQL with pgvector for vector similarity search
- **Database**: PostgreSQL with pgvector extension for storing 128-dimensional face embeddings

### Data Flow

```mermaid
flowchart TD
    Registration[Employee Registration] --> Capture[Face Capture UI]
    Capture --> Quality[Quality Checks]
    Quality --> Liveness[Liveness Detection]
    Liveness --> Upload[Upload to Server]
    Upload --> Embed[Generate Embedding]
    Embed --> Store[Store in pgvector]
    
    Attendance[Attendance Check] --> Verify[Face Verification UI]
    Verify --> Quality2[Quality Checks]
    Quality2 --> Upload2[Upload to Server]
    Upload2 --> Search[Vector Similarity Search]
    Search --> Match{Match Found?}
    Match -->|Yes| Record[Record Attendance]
    Match -->|No| Reject[Reject]
```



## File Structure

```javascript
ERP/
├── client/
│   ├── package.json               # React dependencies and scripts
│   ├── vite.config.js             # Vite build configuration
│   ├── index.html                 # HTML entry point
│   ├── src/
│   │   ├── main.jsx               # React app entry point
│   │   ├── App.jsx                # Main app component with routing
│   │   ├── config/
│   │   │   └── api.js             # API endpoints, thresholds
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Layout.jsx     # Main layout wrapper
│   │   │   │   └── Navigation.jsx # Navigation component
│   │   │   ├── FaceCapture/
│   │   │   │   ├── FaceCapture.jsx        # Main face capture component
│   │   │   │   ├── FaceDetectionOverlay.jsx # Face detection visualization
│   │   │   │   ├── QualityIndicators.jsx   # Quality check UI
│   │   │   │   ├── LivenessIndicator.jsx   # Liveness detection UI
│   │   │   │   └── ScanningRing.jsx        # Animated scanning indicator
│   │   │   ├── Registration/
│   │   │   │   ├── RegistrationForm.jsx    # Employee details form with validation
│   │   │   │   ├── EmployeeIdDisplay.jsx   # Display generated 5-character ID
│   │   │   │   └── RegistrationFlow.jsx    # Registration workflow
│   │   │   ├── Attendance/
│   │   │   │   ├── AttendanceCheck.jsx     # Attendance verification
│   │   │   │   └── AttendanceHistory.jsx   # Attendance history view
│   │   │   └── Common/
│   │   │       ├── Button.jsx              # Reusable button
│   │   │       ├── LoadingSpinner.jsx      # Loading indicator
│   │   │       └── ErrorMessage.jsx        # Error display
│   │   ├── hooks/
│   │   │   ├── useFaceDetection.js         # MediaPipe face detection hook
│   │   │   ├── useQualityChecks.js         # Quality validation hook
│   │   │   ├── useLivenessDetection.js     # Liveness detection hook
│   │   │   ├── useAutoCapture.js           # Auto-capture logic hook
│   │   │   └── useCamera.js                # Camera access hook
│   │   ├── services/
│   │   │   ├── api.js                      # API client utilities
│   │   │   ├── faceDetection.js            # MediaPipe integration
│   │   │   ├── qualityChecks.js            # Quality check algorithms
│   │   │   └── livenessDetection.js        # Liveness detection logic
│   │   ├── styles/
│   │   │   ├── index.css                   # Global styles
│   │   │   ├── FaceCapture.module.css      # Face ID-style interface
│   │   │   └── QualityIndicators.module.css # Quality check UI
│   │   └── utils/
│   │       ├── imageProcessing.js           # Image processing utilities
│   │       └── constants.js                # Constants and thresholds
│   └── public/
│       └── models/                         # MediaPipe models (if needed locally)
│
├── server/
│   ├── app/
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # Database connection & session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── employee.py        # Employee SQLAlchemy model
│   │   │   ├── face_embedding.py  # Face embedding model
│   │   │   └── attendance.py      # Attendance model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── employee.py        # Pydantic schemas for employees
│   │   │   ├── attendance.py      # Pydantic schemas for attendance
│   │   │   └── face.py            # Face-related schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── face_recognition.py # SFace embedding generation
│   │   │   ├── vector_search.py   # pgvector similarity search
│   │   │   └── image_processing.py # Image preprocessing utilities
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── employees.py   # Employee registration endpoints
│   │   │   │   ├── attendance.py   # Attendance endpoints
│   │   │   │   └── health.py      # Health check endpoint
│   │   │   └── dependencies.py    # Shared dependencies (DB session, etc.)
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logging.py          # Logging configuration
│   │       ├── validators.py       # Input validation utilities
│   │       └── employee_id_generator.py  # Generate unique 5-character employee IDs
│   ├── migrations/                # Alembic migrations
│   │   └── versions/
│   ├── storage/                   # Local image storage
│   │   ├── registrations/         # Registration images
│   │   └── attendance/            # Attendance verification images (optional)
│   └── tests/
│       ├── test_face_recognition.py
│       ├── test_api.py
│       └── test_vector_search.py
│
├── .env                          # Environment variables
├── .env.example                  # Example env file
├── .gitignore                    # Git ignore rules
├── pyproject.toml                # Python dependencies
├── README.md                     # Setup and usage instructions
└── docker-compose.yml            # PostgreSQL + pgvector setup (optional)
```



## Implementation Phases

### Phase 1: Foundation & Database Setup

**Files to create:**

- `server/app/config.py` - Environment variable management
- `server/app/database.py` - PostgreSQL connection with pgvector support
- `server/app/models/employee.py` - Employee model
- `server/app/models/face_embedding.py` - Face embedding model with vector type
- `server/app/models/attendance.py` - Attendance model
- `server/app/main.py` - FastAPI app initialization
- `.env` and `.env.example` - Configuration files
- `docker-compose.yml` - PostgreSQL with pgvector (optional but recommended)

**Key implementation details:**

- Use SQLAlchemy with async support
- Configure pgvector extension in database initialization
- Set up Alembic for migrations
- Create database session dependency for FastAPI routes

### Phase 2: Server-Side Face Recognition

**Files to create:**

- `server/app/services/face_recognition.py` - SFace model loading and embedding generation
- `server/app/services/image_processing.py` - Image preprocessing (resize, normalize, alignment)
- `server/app/utils/validators.py` - Image validation (size, format, dimensions)

**Key implementation details:**

- Load SFace model using OpenCV DNN module
- Preprocess images: resize to 112x112, normalize to [0,1], BGR to RGB conversion
- Generate 128-dimensional embeddings
- Handle model loading and caching
- Error handling for invalid images

### Phase 3: Vector Search & Storage

**Files to create:**

- `server/app/services/vector_search.py` - Cosine similarity search using pgvector
- Update `server/app/models/face_embedding.py` - Add vector index configuration

**Key implementation details:**

- Use pgvector's cosine similarity operator (`<=>`)
- Create IVFFlat index for efficient similarity search
- Set similarity threshold (0.6-0.7) for face matching
- Return top match with confidence score
- Handle "no match found" scenarios

### Phase 4: API Endpoints

**Files to create:**

- `server/app/schemas/employee.py` - Pydantic models for employee data (registration request/response)
- `server/app/schemas/attendance.py` - Pydantic models for attendance
- `server/app/schemas/face.py` - Face verification request/response schemas
- `server/app/api/v1/employees.py` - Employee registration endpoints
- `server/app/api/v1/attendance.py` - Attendance endpoints
- `server/app/api/v1/health.py` - Health check
- `server/app/api/dependencies.py` - Shared dependencies
- `server/app/utils/employee_id_generator.py` - Generate unique 5-character employee IDs

**Endpoints to implement:**

- `POST /api/v1/employees/register` - Create employee with auto-generated 5-character ID
- Request body: full_name, email, department, phone (optional), position (optional)
- Response: employee_id (5-character code), full_name, email, department, created_at
- `POST /api/v1/employees/{employee_id}/enroll-face` - Upload face, generate embedding
- `GET /api/v1/employees/{employee_id}` - Get employee details
- `POST /api/v1/attendance/verify` - Face verification with vector search
- `POST /api/v1/attendance/check-in` - Record check-in
- `POST /api/v1/attendance/check-out` - Record check-out
- `GET /api/v1/attendance/history` - Get attendance history
- `GET /api/v1/health` - Health check

**Key implementation details for employee ID generation:**

- Generate unique 5-character alphanumeric code (uppercase letters and numbers)
- Format: e.g., "A1B2C", "X9Y3Z", "M4N8P"
- Check database for uniqueness before assigning
- Retry generation if collision occurs (max 10 attempts)
- Store in `employee_id` field (VARCHAR(5) - exactly 5 characters)

**Key implementation details:**

- Use FastAPI's File upload for images
- Validate image size (max 5MB), format (JPEG/PNG)
- Store images in `server/storage/` directory
- Implement rate limiting on attendance endpoints
- CORS configuration for client access
- Comprehensive error handling
- **Employee Registration**: Generate unique 5-character ID using `employee_id_generator.py`
- Use uppercase letters (A-Z) and numbers (0-9) = 36 characters
- Total combinations: 36^5 = 60,466,176 possible IDs
- Check database for uniqueness before returning
- Return generated ID in response for display to user

### Phase 5: React App Setup & Client-Side Face Detection UI

**Files to create:**

- `client/package.json` - React dependencies (React, React Router, Vite)
- `client/vite.config.js` - Vite configuration
- `client/index.html` - HTML entry point
- `client/src/main.jsx` - React app entry point
- `client/src/App.jsx` - Main app with React Router
- `client/src/components/Layout/Layout.jsx` - Layout wrapper
- `client/src/components/Layout/Navigation.jsx` - Navigation component
- `client/src/components/FaceCapture/FaceCapture.jsx` - Main face capture component
- `client/src/components/FaceCapture/FaceDetectionOverlay.jsx` - Face detection visualization
- `client/src/components/FaceCapture/ScanningRing.jsx` - Animated scanning indicator
- `client/src/components/FaceCapture/QualityIndicators.jsx` - Quality check UI
- `client/src/components/FaceCapture/LivenessIndicator.jsx` - Liveness detection UI
- `client/src/styles/index.css` - Global styles
- `client/src/styles/FaceCapture.module.css` - Face ID-style interface styling
- `client/src/styles/QualityIndicators.module.css` - Quality check UI

**Key implementation details:**

- Set up React with Vite for fast development
- Use React Router for navigation (registration, attendance routes)
- Full-screen black background
- Large circular white frame (similar to Face ID)
- Animated scanning indicator (green ring with tick marks)
- Real-time face detection overlay with crosshair
- Centered face positioning feedback
- Back navigation button (top-left)
- Mobile-responsive design using CSS modules

### Phase 6: MediaPipe Integration with React Hooks

**Files to create:**

- `client/src/config/api.js` - API endpoints, quality thresholds
- `client/src/hooks/useCamera.js` - Camera access hook
- `client/src/hooks/useFaceDetection.js` - MediaPipe Face Detection hook
- `client/src/services/faceDetection.js` - MediaPipe integration service
- `client/src/utils/imageProcessing.js` - Image processing utilities

**Key implementation details:**

- Create custom React hooks for camera and face detection
- Load MediaPipe Face Detection model (use useEffect for initialization)
- Real-time face detection at 30fps+ using requestAnimationFrame
- Extract face bounding box and landmarks
- Handle multiple faces (reject if >1 detected)
- Extract face region with padding for recognition
- Canvas-based image processing
- Use React state to manage detection results and camera stream

### Phase 7: Quality Checks with React Hooks

**Files to create:**

- `client/src/hooks/useQualityChecks.js` - Quality validation hook
- `client/src/services/qualityChecks.js` - Quality check algorithms
- `client/src/utils/constants.js` - Quality thresholds and constants

**Key implementation details:**

- Create custom React hook that monitors quality in real-time
- **Brightness Check**: Calculate average luminance, ensure 50-200 range
- **Sharpness Check**: Laplacian variance threshold (e.g., >100)
- **Face Size Check**: Face should occupy 20-40% of image area
- **Frontalness Check**: Use MediaPipe head pose estimation (yaw, pitch, roll within ±15°)
- Use React state to track quality metrics
- Real-time visual feedback indicators for each metric via QualityIndicators component
- Display quality status (pass/fail) for each check

### Phase 8: Liveness Detection with React Hooks

**Files to create:**

- `client/src/hooks/useLivenessDetection.js` - Liveness detection hook
- `client/src/services/livenessDetection.js` - Liveness detection logic

**Key implementation details:**

- Create custom React hook for liveness detection state management
- **Blink Detection**: Track eye landmarks, detect 1-2 blinks
- **Head Movement**: Track subtle left/right head rotation (±10-15°)
- Use React state to track liveness progress and status
- Display instructions during liveness check via LivenessIndicator component
- Timeout handling (max 30 seconds) using useEffect cleanup
- Visual feedback for liveness progress

### Phase 9: Auto-Capture Logic with React Hooks

**Files to create:**

- `client/src/hooks/useAutoCapture.js` - Auto-capture logic hook

**Key implementation details:**

- Create custom React hook that combines quality checks and liveness detection
- Monitor all quality checks in real-time using useEffect
- Wait for liveness check completion
- Verify face is centered and aligned
- Capture multiple frames (3-5) when conditions met
- Select best quality image from captured frames
- Use React state to manage capture status and captured images
- Manual capture fallback button
- Debounce capture to prevent multiple triggers using useRef/useEffect

### Phase 10: Registration & Attendance Flows with React Components

**Files to create:**

- `client/src/services/api.js` - API client utilities (fetch wrapper)
- `client/src/components/Registration/RegistrationForm.jsx` - Employee details form
- `client/src/components/Registration/RegistrationFlow.jsx` - Registration workflow component
- `client/src/components/Attendance/AttendanceCheck.jsx` - Attendance verification component
- `client/src/components/Attendance/AttendanceHistory.jsx` - Attendance history view
- `client/src/components/Common/Button.jsx` - Reusable button component
- `client/src/components/Common/LoadingSpinner.jsx` - Loading indicator
- `client/src/components/Common/ErrorMessage.jsx` - Error display component

**Registration flow:**

1. User fills RegistrationForm component with employee data:

- Full Name (required)
- Email (required, validated)
- Department (required, dropdown or text input)
- Phone (optional)
- Position/Job Title (optional)

2. Submit form to `/api/v1/employees/register`
3. Server generates unique 5-character employee ID (e.g., "A1B2C")
4. Display generated employee ID prominently to user
5. Navigate to face capture interface (FaceCapture component) with employee_id
6. Quality checks + liveness detection (via hooks)
7. Auto-capture when ready (useAutoCapture hook)
8. Upload to `/api/v1/employees/{employee_id}/enroll-face` (api service)
9. Show success/error feedback using ErrorMessage component
10. Use React Router for navigation between steps

**RegistrationForm component details:**

- Form validation (required fields, email format)
- Loading state during API call
- Display generated 5-character ID in a highlighted box after successful registration
- "Continue to Face Enrollment" button (disabled until registration succeeds)
- Error handling for duplicate email or registration failures

**Attendance flow:**

1. Navigate to attendance interface (AttendanceCheck component)
2. Quality checks (no liveness needed for attendance)
3. Auto-capture when ready
4. Upload to `/api/v1/attendance/verify`
5. If match found, show employee details and record attendance
6. If no match, show error message
7. Use React state to manage attendance status and history

### Phase 11: Integration & Testing

**Tasks:**

- Connect all client components
- End-to-end testing of registration flow
- End-to-end testing of attendance flow
- Test edge cases (poor lighting, multiple faces, no face)
- Performance testing (embedding generation <500ms, detection 30fps+)
- Error handling validation
- Mobile device testing

### Phase 12: Documentation & Polish

**Files to update:**

- `README.md` - Comprehensive setup instructions
- Add API documentation (FastAPI auto-generates Swagger UI)
- Add inline code comments
- Create `.env.example` with all required variables

## Dependencies

### Server (pyproject.toml)

```toml
dependencies = [
    "fastapi[standard]>=0.124.4",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.29.0",  # PostgreSQL async driver
    "psycopg2-binary>=2.9.9",  # For pgvector support
    "pgvector>=0.3.0",  # pgvector Python client
    "alembic>=1.13.0",  # Database migrations
    "opencv-python>=4.9.0",
    "opencv-contrib-python>=4.9.0",  # For SFace model
    "numpy>=1.26.0",
    "python-multipart>=0.0.9",  # File uploads
    "python-dotenv>=1.0.0",  # Environment variables
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]
```



### Client (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@mediapipe/face_detection": "^0.4.0",
    "@mediapipe/camera_utils": "^0.3.0",
    "@mediapipe/drawing_utils": "^0.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

**Build setup:**

- Use Vite for fast development and production builds
- React Router for client-side routing
- MediaPipe via npm packages

## Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/erp_db
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/erp_db  # For migrations

# Server
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000  # Vite default port is 5173

# Face Recognition
FACE_SIMILARITY_THRESHOLD=0.65
SFACE_MODEL_PATH=models/sface.onnx  # Or download path

# Storage
STORAGE_PATH=./server/storage
MAX_IMAGE_SIZE_MB=5

# Security
RATE_LIMIT_PER_MINUTE=60
```



## Database Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Employees table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(5) UNIQUE NOT NULL,  -- 5-character alphanumeric code (e.g., "A1B2C")
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,  -- Email should be unique
    department VARCHAR(100),
    phone VARCHAR(20),  -- Optional phone number
    position VARCHAR(100),  -- Optional job title/position
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster employee_id lookups
CREATE INDEX idx_employee_id ON employees(employee_id);

-- Face embeddings table
CREATE TABLE face_embeddings (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    embedding vector(128) NOT NULL,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create vector index for similarity search
CREATE INDEX ON face_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Attendance records
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    check_in_time TIMESTAMP NOT NULL,
    check_out_time TIMESTAMP,
    location VARCHAR(255),
    device_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_attendance_employee ON attendance(employee_id);
CREATE INDEX idx_attendance_date ON attendance(check_in_time);
```



## Technical Considerations

1. **Face Detection Performance**: MediaPipe should achieve 30fps+ on modern devices. Use `requestAnimationFrame` for smooth rendering.
2. **Embedding Generation**: SFace model typically generates embeddings in <500ms. Cache model loading to avoid reload on each request.
3. **Vector Search**: IVFFlat index with 100 lists provides good balance between speed and accuracy for <10K employees. Adjust lists parameter as data grows.
4. **Image Storage**: Store images with employee_id and timestamp in filename. Implement cleanup policy for old attendance images.
5. **Error Handling**: Comprehensive error messages for:

- No face detected
- Multiple faces detected
- Poor image quality
- No match found (attendance)
- Database errors
- Model loading errors

6. **Security**: 

- Validate all inputs
- Rate limiting on sensitive endpoints
- CORS configuration
- Image size/format validation
- SQL injection prevention (SQLAlchemy ORM)

## Development Order

1. **Phase 1-3**: Backend foundation (database, face recognition, vector search)
2. **Phase 4**: API endpoints (test with Postman/curl)
3. **Phase 5**: React app setup and basic UI structure
4. **Phase 6**: MediaPipe integration with React hooks
5. **Phase 7-9**: Quality checks, liveness, auto-capture (as React hooks)