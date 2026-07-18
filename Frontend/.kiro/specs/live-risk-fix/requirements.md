# Requirements: Live Risk Page Fix

## Problem Statement
The `/live-risk` page displays no data because of two bugs:
1. `api.js` has `baseURL: ''`, ignoring `VITE_API_BASE_URL` from `.env`, so every API call goes to the Vite dev server (`localhost:5173`) instead of the backend (`localhost:8080`).
2. `LiveRisk.jsx` expects a per-supplier array of rows, but the backend's `GET /api/v1/risk/run` returns a single aggregated object: `{ risk_class, risk_score, reasons[] }`.

## Goals
Fix both bugs so the page correctly calls the backend and renders the data it actually returns.

## Requirements

### REQ-1: Fix API Base URL
- `api.js` must read `import.meta.env.VITE_API_BASE_URL` and use it as the Axios `baseURL`.
- When the env variable is absent the default must fall back to `'http://127.0.0.1:8080'`.
- No other files that import `api.js` need changes (the fix is contained in `api.js`).

### REQ-2: Redesign LiveRisk Page to Match Backend Response
The page must display the actual backend response shape:
```
{ risk_class: "HIGH" | "MEDIUM" | "LOW", risk_score: 0–100, reasons: string[] }
```

#### REQ-2a: Risk Score Card
- Display the numeric `risk_score` prominently (large number).
- Show a circular or bar progress indicator that fills proportionally to `risk_score`.
- Colour the indicator: red for HIGH (score > 70), amber for MEDIUM (score 40–70), green for LOW (score < 40).

#### REQ-2b: Risk Class Badge
- Display `risk_class` as a styled badge matching the colour coding above.

#### REQ-2c: Risk Reasons List
- Display each string in `reasons` as a clearly readable bullet item.
- Show an icon or indicator per item (e.g. a warning icon).
- If `reasons` is empty, show a placeholder message: "No specific risk factors identified."

#### REQ-2d: Page Header & Actions
- Keep the existing "Live Risk Intelligence" heading and subtitle.
- Keep the Refresh button (re-calls the API).
- Remove the Export CSV button and supplier-table UI that no longer apply.

#### REQ-2e: Loading & Error States
- Show the existing `<Loader>` component while the request is in-flight.
- Show the existing `<ErrorCard>` component on failure, with a retry callback.

### REQ-3: No Backend Changes
- The backend (`unified_server.py`, adapters, models) must not be modified.
- The fix is entirely in the frontend (`api.js` and `LiveRisk.jsx`).

### REQ-4: Consistent Styling
- Use the existing CSS variables (`--danger`, `--warning`, `--success`, `--text-primary`, `--border-color`, `--bg-secondary`, `glass-card`, `page-container`, etc.) already present in the project.
- Do not introduce new CSS files or external style libraries.
