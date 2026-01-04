---
name: OnTime ERP MVP Implementation
overview: A production-grade implementation plan for the OnTime ERP Attendance + Payroll Management system, following the phased approach from the cursor rules with comprehensive test coverage for all components.
todos:
  - id: phase0-docker
    content: Create docker-compose.yml with postgres, backend, frontend services and data/ volumes
    status: pending
  - id: phase0-config
    content: Update face_recognition.py to use config.py values (model name, embedding size, threshold)
    status: pending
  - id: phase0-tests
    content: Setup pytest infrastructure with conftest.py, fixtures, and test database
    status: pending
  - id: phase1-models
    content: Implement all SQLModel models (Person, Role, Location, Shift, Skill, Attendance, Payroll tables)
    status: pending
  - id: phase1-migrations
    content: Create database migration setup and initial migration
    status: pending
  - id: phase2-api-structure
    content: Create server/app/ structure with main.py, database.py, dependencies.py
    status: pending
  - id: phase2-person-api
    content: Implement Person CRUD API with 6-char ID generation
    status: pending
  - id: phase2-master-data-api
    content: Implement Location, Shift, Skill, Assignment CRUD APIs
    status: pending
  - id: phase2-attendance-api
    content: Implement Attendance check-in/out and verification APIs
    status: pending
  - id: phase2-rbac
    content: Implement RBAC middleware with role and field-level guards
    status: pending
  - id: phase3-automation
    content: Implement attendance reconciliation service (overtime_pending/absent rules)
    status: pending
  - id: phase4-payroll-api
    content: Implement Payroll period, run, calculation, and approval APIs
    status: pending
  - id: phase5-admin-ui
    content: Create Admin UI pages (locations, shifts, skills, persons, salary components, payroll dashboard)
    status: pending
  - id: phase5-supervisor-ui
    content: Create Supervisor UI pages (workers, take attendance, overtime management)
    status: pending
  - id: phase5-worker-ui
    content: Create Worker UI pages (my attendance, my payslip)
    status: pending
  - id: phase6-unit-tests
    content: Write unit tests for all services (ID generator, face recognition, automation, payroll calc)
    status: pending
  - id: phase6-integration-tests
    content: Write integration tests for all API endpoints
    status: pending
  - id: phase7-migration-script
    content: Create migration script from old schema to new schema
    status: pending
  - id: phase7-seed-data
    content: Create seed script with admin, supervisor, workers, locations, shifts, skills, components
    status: pending
---

# OnTime ERP - Production-Grade Implementation Plan

## Repository Discovery Summary

**Current Stack:**

- Backend: FastAPI + SQLModel (SQLAlchemy-based ORM) + uvicorn
- Database: PostgreSQL with pgvector (via Docker)
- Frontend: React 18 + Vite + react-router-dom + MediaPipe
- Face Recognition: DeepFace with Facenet (128-dim embeddings)
- Package Manager: `uv` (Python), npm (JavaScript)

**Current State:**

- `server/app/` directory does not exist (referenced in scripts but not implemented)
- [`server/db/models.py`](server/db/models.py) has only an empty `Person` stub
- [`docker-compose.yml`](docker-compose.yml) is empty
- No test infrastructure exists

---

## Phase 0: Infrastructure Setup and Config Fixes

### 0.1 Fix Face Recognition Service to Use Config

Update [`server/services/face_recognition.py`](server/services/face_recognition.py) to use values from [`server/config.py`](server/config.py):

- Inject `config.RECOGNITION_MODEL_NAME` (default: `Facenet`)
- Inject `config.EMBEDDING_SIZE` (default: `128`)
- Inject `config.SIMILARITY_THRESHOLD` (default: `0.60`)

### 0.2 Setup Docker Compose with Volumes in `data/`

Create complete [`docker-compose.yml`](docker-compose.yml) with:

- **postgres** service: pgvector-enabled PostgreSQL with volume at `./data/postgres`
- **backend** service: FastAPI app with volume at `./data/uploads` for images/documents
- **frontend** service: Vite React app (nginx for production)

### 0.3 Test Infrastructure Setup

Add `pytest` + `pytest-asyncio` + `httpx` + `faker` to dev dependencies in [`pyproject.toml`](pyproject.toml). Create:

- `tests/conftest.py` - fixtures for test DB, async client, seed factories
- `tests/unit/` - unit tests
- `tests/integration/` - API integration tests
- `client/src/__tests__/` - React component tests (vitest)

---

## Phase 1: Database Schema Design

```mermaid
erDiagram
    Person ||--o{ Document : has
    Person ||--o{ PersonSkill : has
    Person ||--o{ Assignment : has
    Person ||--o{ Attendance : records
    Person ||--o{ OvertimeRequest : creates
    Person ||--o{ EmployeeComponent : has
    Person ||--o{ PayrollRunEmployee : receives
    
    Skill ||--o{ PersonSkill : linked
    Skill ||--o{ SkillLocationPrice : priced_at
    
    Location ||--o{ Assignment : hosts
    Location ||--o{ SkillLocationPrice : prices
    Location ||--o{ Attendance : occurs_at
    Location ||--o{ PayrollRun : scoped_to
    
    Shift ||--o{ Assignment : scheduled
    Shift ||--o{ Attendance : for_shift
    
    PayrollPeriod ||--o{ PayrollRun : contains
    PayrollRun ||--o{ PayrollRunEmployee : has
    PayrollRunEmployee ||--o{ PayrollRunLine : lines
    
    SalaryComponent ||--o{ EmployeeComponent : applied
    SalaryComponent ||--o{ PayrollRunLine : used_in
```



### Core Tables (with indexes):

| Table | Primary Key | Key Fields ||-------|-------------|------------|| `role` | UUID | `name` (admin/employee/worker) || `person` | CHAR(6) | `full_name`, `identity_number`, `dob`, `sex`, `phone`, `status`, `face_embedding` (vector), `supervisor_id` FK, `role_id` FK || `document` | UUID | `person_id` FK, `type`, `storage_url`, `uploaded_by_person_id` FK || `location` | UUID | `name`, `city` || `shift` | UUID | `starts_at` (TIME), `ends_at` (TIME) || `skill` | UUID | `name` || `person_skill` | Composite | `person_id` FK, `skill_id` FK || `skill_location_price` | Composite | `skill_id` FK, `location_id` FK, `price` || `assignment` | UUID | `person_id` FK, `location_id` FK, `shift_id` FK, `title`, `rate`, `effective_from`, `effective_to` || `attendance` | UUID | `person_id` FK, `taken_by_person_id` FK, `location_id` FK, `shift_id` FK, `attendance_date`, `check_in`, `check_out`, `image_url`, `status` enum || `overtime_request` | UUID | `person_id` FK, `attendance_id` FK, `date`, `hours`, `status` enum, `created_by_person_id` FK || `salary_component` | UUID | `name`, `kind`, `type`, `amount_type`, `amount`, `active` || `employee_component` | UUID | `person_id` FK, `component_id` FK, `value_override` || `payroll_period` | UUID | `start_date`, `end_date`, `status` enum || `payroll_run` | UUID | `payroll_period_id` FK, `location_id` FK, `status` enum, `created_by_person_id` FK || `payroll_run_employee` | UUID | `payroll_run_id` FK, `person_id` FK, `gross`, `deductions`, `net`, `total_hours` || `payroll_run_line` | UUID | `payroll_run_employee_id` FK, `component_id` FK, `kind`, `amount` |---

## Phase 2: Backend Implementation

### 2.1 Project Structure

```javascript
server/
  app/
    __init__.py
    main.py              # FastAPI app entry
    database.py          # Engine, session management
    dependencies.py      # Dependency injection (get_db, get_current_user)
    models/
      __init__.py
      person.py          # Person, Role models
      location.py        # Location, Shift, Assignment
      skill.py           # Skill, PersonSkill, SkillLocationPrice
      attendance.py      # Attendance, OvertimeRequest
      payroll.py         # PayrollPeriod, PayrollRun, etc.
      document.py
      salary_component.py
    schemas/
      __init__.py
      person.py          # Pydantic schemas for validation
      location.py
      attendance.py
      payroll.py
    api/
      __init__.py
      v1/
        __init__.py
        router.py        # Main router aggregating all routers
        auth.py          # Login, token endpoints
        persons.py       # Person CRUD
        locations.py     # Location CRUD
        shifts.py        # Shift CRUD
        skills.py        # Skills CRUD
        assignments.py   # Assignment CRUD
        attendance.py    # Attendance endpoints
        overtime.py      # Overtime request endpoints
        payroll.py       # Payroll endpoints
        reports.py       # Export/report endpoints
    services/
      __init__.py
      face_recognition.py
      attendance_automation.py
      payroll_calculation.py
      person_id_generator.py
    middleware/
      __init__.py
      rbac.py            # Role-based access control
```



### 2.2 RBAC Implementation

Implement middleware in `server/app/middleware/rbac.py`:

- `require_role(roles: List[str])` - decorator for endpoint access
- `field_level_guard(admin_only_fields: List[str])` - for PUT/PATCH requests blocking monetary fields for non-admins

### 2.3 API Endpoints Summary

| Endpoint Group | Admin | Employee/Supervisor | Worker ||---------------|-------|---------------------|--------|| `POST /persons` | Create any | Create workers only | - || `PUT /persons/{id}` | All fields | Non-monetary fields only | - || `CRUD /locations, /shifts, /skills` | Full | Read-only | - || `CRUD /salary-components` | Full | - | - || `POST /attendance/check-in` | - | Self + workers | - || `GET /attendance` | All | Own + workers | Own only || `POST /overtime-requests` | Create/approve | Submit for workers | - || `POST /payroll/run` | Full | - | - || `GET /payroll/{person_id}` | All | Own + workers | Own only |---

## Phase 3: Attendance Automation Service

Create `server/app/services/attendance_automation.py`:

```python
async def reconcile_attendance(date: date, session: AsyncSession):
    """
    Rules:
    1. check_in exists, check_out missing, shift ended -> status=overtime_pending, create OvertimeRequest
    2. No check_in by shift end -> status=absent
    """
```

Trigger via:

- Scheduled job (APScheduler or Celery beat)
- Admin endpoint: `POST /api/v1/attendance/reconcile`
- Before payroll run

---

## Phase 4: Payroll Calculation Service

Create `server/app/services/payroll_calculation.py`:

```python
async def calculate_payroll(period_id: UUID, location_id: UUID | None, session: AsyncSession):
    """
    For each person:
    1. Sum attendance hours (present + approved overtime)
    2. Apply base salary component
    3. Apply allowances, incentives
    4. Apply deductions
    5. Calculate overtime pay
    6. Store in payroll_run_employee + payroll_run_line
    """
```

---

## Phase 5: Frontend UI Updates

### 5.1 New Routes in [`client/src/App.jsx`](client/src/App.jsx)

```jsx
<Route path="/login" element={<LoginPage />} />
<Route path="/admin/*" element={<AdminLayout />}>
  <Route path="locations" element={<LocationsPage />} />
  <Route path="shifts" element={<ShiftsPage />} />
  <Route path="skills" element={<SkillsPage />} />
  <Route path="persons" element={<PersonsPage />} />
  <Route path="salary-components" element={<SalaryComponentsPage />} />
  <Route path="payroll" element={<PayrollDashboard />} />
  <Route path="reports" element={<ReportsPage />} />
</Route>
<Route path="/supervisor/*" element={<SupervisorLayout />}>
  <Route path="workers" element={<WorkersPage />} />
  <Route path="attendance" element={<TakeAttendancePage />} />
  <Route path="overtime" element={<OvertimeManagementPage />} />
</Route>
<Route path="/worker/*" element={<WorkerLayout />}>
  <Route path="my-attendance" element={<MyAttendancePage />} />
  <Route path="my-payslip" element={<MyPayslipPage />} />
</Route>
```



### 5.2 Key UI Components

- `PayrollDashboard` - Monthly summary table with filters, drill-down
- `TakeAttendancePage` - Face capture with location/shift selector
- `PersonForm` - CRUD form with field-level disabled states per role

---

## Phase 6: Testing Strategy

### Unit Tests (`tests/unit/`)

| Test File | Coverage ||-----------|----------|| `test_person_id_generator.py` | 6-char alphanumeric uniqueness || `test_face_recognition_service.py` | Embedding generation, similarity || `test_attendance_automation.py` | Reconciliation rules || `test_payroll_calculation.py` | Calculation logic || `test_rbac.py` | Role checks, field guards |

### Integration Tests (`tests/integration/`)

| Test File | Coverage ||-----------|----------|| `test_person_api.py` | CRUD, role restrictions || `test_attendance_api.py` | Check-in/out, verification || `test_payroll_api.py` | Run creation, approval, locking || `test_overtime_api.py` | Request/approve flows |

### Frontend Tests (`client/src/__tests__/`)

| Test File | Coverage ||-----------|----------|| `PayrollDashboard.test.jsx` | Renders data, filters work || `AttendanceCheck.test.jsx` | Capture flow, API calls |---

## Phase 7: Migration and Deployment

### 7.1 Database Migration Strategy

1. Create new tables alongside old (no drop)
2. Migrate data with script: `scripts/migrate_to_new_schema.py`
3. Update code paths to new tables
4. Archive old tables (prefix with `_old_`)

### 7.2 Environment Files

Create `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://erp_user:erp_password@localhost:5432/erp_db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
RECOGNITION_MODEL_NAME=Facenet
EMBEDDING_SIZE=128
SIMILARITY_THRESHOLD=0.60
SECRET_KEY=your-secret-key-here
```

---

## Execution Order

1. **Phase 0**: Docker + Config fixes + Test infrastructure
2. **Phase 1**: Schema design + Models
3. **Phase 2**: API implementation with RBAC
4. **Phase 3**: Attendance automation
5. **Phase 4**: Payroll calculation