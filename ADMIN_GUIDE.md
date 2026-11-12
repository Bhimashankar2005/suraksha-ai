# SURAKSHA AI – SOC Administrator & Security Operations Manual

This manual provides operational instructions for Security Operations Center (SOC) administrators, threat intelligence analysts, and community moderators managing the **SURAKSHA AI** platform.

---

## Table of Contents
1. [SOC Architecture & Access Control](#1-soc-architecture--access-control)
2. [Administrator Account Provisioning](#2-administrator-account-provisioning)
3. [SOC Dashboard & System Telemetry](#3-soc-dashboard--system-telemetry)
4. [Community Threat Moderation Queue](#4-community-threat-moderation-queue)
5. [Threat Intelligence & Citizen Broadcasts](#5-threat-intelligence--citizen-broadcasts)
6. [User Directory & RBAC Management](#6-user-directory--rbac-management)
7. [Append-Only Security Audit Trail Explorer](#7-append-only-security-audit-trail-explorer)
8. [Defensive Security Hardening & Rate Limiting](#8-defensive-security-hardening--rate-limiting)
9. [Database Maintenance & Backup Procedures](#9-database-maintenance--backup-procedures)

---

## 1. SOC Architecture & Access Control

SURAKSHA AI implements strict server-side Role-Based Access Control (RBAC):
- **Roles**:
  - `ADMIN`: Full administrative control, user role management, system telemetry, audit trail inspection, threat broadcasting.
  - `COMMUNITY_MODERATOR`: Threat report review and queue moderation.
  - `USER`: Platform citizen access (scanners, assistant, vault, academy).
- **Protection**: All `/admin/*` API endpoints require valid signed JWT bearer tokens carrying the `ADMIN` role. Attempts to access admin routes with `USER` tokens are intercepted by `require_admin` dependency and rejected with HTTP `403 Forbidden`.

---

## 2. Administrator Account Provisioning

To prevent accidental hardcoding of admin credentials in source repositories, administrators must be provisioned via the secure CLI provisioning tool:

```bash
# Provision a new SOC Administrator
python backend/app/scripts/create_admin.py --email admin@suraksha.gov.in --password "SuperAdminSecure2026!" --name "Chief SOC Officer"
```

### Script Security Features:
- Assigns the immutable `ADMIN` role from the database `roles` table.
- Hashes passwords using **Argon2id** (`argon2-cffi`) with memory-hard parameters.
- Rejects weak passwords failing standard complexity checks (minimum 8 characters).
- Records an `ADMIN_PROVISIONED` event in the append-only `audit_logs` table.

### Accessing the SOC Command Center
Once provisioned:
1. Navigate to `http://localhost:3000/admin/login`.
2. Enter your administrator email and Argon2id-secured password.
3. Upon authentication, you will be redirected to the SOC Command Center at `/admin/dashboard`.

---

## 3. SOC Dashboard & System Telemetry (`/admin/dashboard`, `/admin/security`)

The SOC Dashboard aggregates real-time platform metrics directly from the relational database without requiring third-party monitoring agents:

- **System Uptime & Health**: Reports `HEALTHY_ONLINE` when database connection pools, storage vaults, and rate limiters are nominal.
- **Platform Usage Telemetry**:
  - Total registered citizens.
  - Total scans performed across all detection engines (Message, URL, Screenshot, Deepfake, Privacy).
  - Total community threat reports and moderation queue backlog.
- **Evidence Vault Storage Metrics**:
  - Total physical files secured in `storage/evidence/`.
  - Total disk storage consumed (bytes/MB).
  - Total financial loss documented across compiled citizen FIR dossiers (in INR).
- **Active Threat Indicators**: Number of verified indicators currently active in the public threat feed.

---

## 4. Community Threat Moderation Queue (`/admin/reports`)

Crowdsourced reports submitted by citizens enter the queue in `PENDING` status with unique tracking references (`SUR-REP-XXXXXX`).

### Moderation Workflow
1. Open `/admin/reports`.
2. Filter the queue by status: `PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, or `DUPLICATE`.
3. Click **Inspect** on any report to review:
   - Threat type (`PHONE`, `URL`, `MESSAGE`, `SCREENSHOT`, `HARASSMENT`).
   - Offending value (e.g., suspicious phone number, phishing link).
   - Citizen narrative and region.
   - Associated evidence attachments and SHA-256 hashes.
   - System duplicate detection indicators (flags recurring patterns).

### Review Actions & Publishing
When reviewing a report, choose an action:
- **`APPROVE_VERIFY`**: Verifies the threat. If **Publish as Public Threat Alert** is checked, the indicator is published to the `threats` table and appears in the public citizen warning feed.
- **`REJECT`**: Declines unverified or false-positive reports.
- **`MARK_DUPLICATE`**: Links the report to an existing parent incident code.
- **`RESOLVE`**: Marks historical threats as neutralized or taken down.

### Automated Citizen Notification Hook
Whenever a report review is submitted:
- The system automatically compiles and dispatches an in-app notification to the citizen who submitted the report.
- The citizen receives immediate feedback informing them that report `SUR-REP-XXXXXX` has been reviewed and verified, reinforcing community trust.

---

## 5. Threat Intelligence & Citizen Broadcasts (`/admin/intelligence`)

The Threat Intelligence manager allows SOC analysts to curate the public indicator feed and broadcast emergency alerts to all citizens:

### Managing Indicators
- View active indicators by type: `PHONE`, `URL`, `UPI_ID`, `SMS_SENDER`.
- Adjust threat severity: `MEDIUM`, `HIGH`, or `CRITICAL`.
- Deactivate obsolete indicators or update incident frequency counters.

### High-Priority Citizen Broadcasts
In the event of an active, widespread campaign (e.g., mass electricity bill disconnection SMS targeting a specific state):
1. In `/admin/intelligence`, click **Broadcast Security Alert**.
2. Enter an Alert Title (e.g., *CRITICAL ADVISORY: Fake Electricity Bill SMS Active in Karnataka*).
3. Enter actionable mitigation directives (e.g., *Do not call numbers ending in 9822; electricity boards never threaten power cutoff via SMS*).
4. Select severity (`CRITICAL_ALERT`).
5. Click **Broadcast to Citizens**.
6. The alert is instantly delivered to every active citizen's in-app Notification Center and displayed prominently in their portal header.

---

## 6. User Directory & RBAC Management (`/admin/users`)

Manage platform accounts, monitor user activity, and administer roles:

- **Search & Filter**: Search citizens by email, full name, or role (`USER`, `ADMIN`, `COMMUNITY_MODERATOR`).
- **Role Assignment**: Elevate trusted analysts to `COMMUNITY_MODERATOR` or `ADMIN`.
- **Account Suspension**: Toggle `is_active` to suspend compromised or abusive accounts.

### Last-Admin Security Safeguard
To prevent accidental administrative lockout:
- The backend enforces a strict server-side validation check in `backend/app/api/endpoints/admin_management.py`.
- If an administrator attempts to demote their own account, or deactivates the last remaining active administrator on the platform, the server rejects the request with HTTP `400 Bad Request` and error detail:
  `"Cannot demote or deactivate the last active administrator. Create or assign another administrator first."`

---

## 7. Append-Only Security Audit Trail Explorer (`/admin/audit-logs`)

For forensic transparency and compliance, every administrative and security-critical action is logged in an append-only audit trail (`audit_logs` table):

### Logged Security Events
- `ADMIN_LOGIN`: Successful administrator authentication with IP and user agent.
- `REPORT_REVIEW`: Threat report approval, rejection, or status modification.
- `USER_ROLE_UPDATED`: Changes to user roles and privileges.
- `USER_STATUS_TOGGLED`: Account activations and suspensions.
- `EVIDENCE_DOWNLOAD`: Evidence file retrieval (tracks file code, requester, timestamp).
- `BROADCAST_SENT`: High-priority community alerts dispatched.

### Audit Inspection Interface
In `/admin/audit-logs`:
- Filter logs by Action, Resource Type, or User ID.
- Inspect detailed structured JSON payloads recording the exact state change.
- Audit logs cannot be modified or deleted through the API.

---

## 8. Defensive Security Hardening & Rate Limiting

### In-Memory Sliding-Window Rate Limiter
Located in `backend/app/core/rate_limiter.py`:
- **Auth Routes** (`/api/v1/auth/login`, `/api/v1/auth/register`):
  - Limit: **10 requests per 60 seconds** per client IP.
  - Prevents credential stuffing and dictionary brute-force attacks.
- **Scan Routes** (`/api/v1/scam/scan`, `/api/v1/url/scan`, `/api/v1/image/scan`, etc.):
  - Limit: **60 requests per 60 seconds** per client IP.
  - Prevents automated abuse and denial-of-service on local compute.
- **General APIs**: Limit: **120 requests per 60 seconds**.
- **Excluded Routes**: `/api/v1/health`, `/api/v1/docs`, `/api/v1/openapi.json`.
- **429 Response**: Returns standard HTTP 429 status, `Retry-After` header, and statutory **1930 Helpline** guidance.

### OWASP Defensive Security Headers
Configured in `backend/app/core/security_headers.py`:
- `X-Content-Type-Options: nosniff` (MIME sniffing defense)
- `X-Frame-Options: DENY` (Clickjacking defense)
- `X-XSS-Protection: 1; mode=block` (Cross-site scripting defense)
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HSTS)
- `Referrer-Policy: strict-origin-when-cross-origin` (Privacy protection)
- `Permissions-Policy: geolocation=(), camera=(), microphone=(self)` (Device sensor restriction)
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none';` (Content injection prevention)

### Path Traversal Defense
In `backend/app/core/sanitizer.py`:
- `validate_safe_path(base_dir, target_path)` verifies using canonicalized paths (`os.path.realpath`) that all file download and delete requests strictly resolve within the designated storage root (`storage/evidence/`). Any attempt to traverse using `../` or absolute system paths is rejected with HTTP `400 Bad Request`.

---

## 9. Database Maintenance & Backup Procedures

### Local SQLite Database (`suraksha.db`)
For single-server or local edge deployments:
1. **Periodic Snapshot Backup**:
   ```bash
   # Create a timestamped backup copy
   copy suraksha.db "storage\backups\suraksha_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
   ```
2. **Vacuuming & Optimization**:
   SQLite is configured with `PRAGMA foreign_keys=ON;` and a 30-second busy timeout for concurrent transactions. Run periodic maintenance in SQLite:
   ```sql
   VACUUM;
   ANALYZE;
   ```

### Storage Vault Backup (`storage/evidence/`)
The Evidence Vault stores encrypted/isolated binary artifacts named by UUID (`.dat`).
- Regularly back up the `storage/` directory to an encrypted offline volume.
- File integrity can be audited against the `sha256_hash` field recorded in the `evidence_files` database table.

### Migrating to Production PostgreSQL
When scaling to a distributed multi-node infrastructure:
1. Provision a local or self-hosted PostgreSQL 15+ database.
2. Update `.env`:
   ```ini
   DATABASE_URL=postgresql://suraksha_user:StrongPassword@localhost:5432/suraksha_db
   ```
3. Restart the backend service. SQLAlchemy automatically detects PostgreSQL dialect and connects via connection pooling.

