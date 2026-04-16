# UI Specification: Analyst-First Execution Surface

## 1) UI Goals
- Enable full workflow operation without CLI or coding.
- Make each stage inspectable, testable, and rerunnable.
- Preserve evidence traceability from visuals to raw sources.

## 2) Primary Screens
## 2.1 Run Builder
Purpose: Create a new analysis run with minimal inputs.

Fields:
- **Topic** (required)
- **Date range length** (required, 1-30 days ending now)
- **Advanced settings** (optional, collapsed)

Actions:
- Validate inputs
- Start run
- Save reusable run profile

## 2.2 Run Monitor
Purpose: Observe stage execution and health in real time.

Elements:
- Global run status and elapsed time
- Stage list with statuses: pending/running/completed/partial/failed
- Source ingestion summary (attempted/succeeded/failed)
- Alert panel for policy or quality warnings

Actions:
- Pause/cancel run (role-permitted)
- Open stage detail
- Rerun failed stage

## 2.3 Stage Detail Panel
Purpose: Inspect artifacts and validations for a single stage.

Must show:
- Inputs consumed
- Outputs generated
- Validation checks and pass/fail results
- Stopping condition results
- Linked artifacts and evidence IDs

Actions:
- Approve and continue (if manual gate enabled)
- Trigger bounded rerun

## 2.4 Analysis Workspace
Purpose: Explore outputs by modality.

Tabs:
1. **Events Table** (clustered groups, counts, confidence)
2. **Timeline** (article counts + detected peaks/spikes/trends)
3. **Map** (geospatial mentions with confidence and density)
4. **Narrative Compare** (source framing, agreements, contradictions)
5. **Citations** (claim-to-evidence mapping)

## 2.5 Report Viewer and Export
Purpose: Review final report and export evidence package.

Must support:
- Section-level expand/collapse
- Inline citations clickable to evidence items
- Export options (PDF/HTML/JSON evidence bundle)

## 2.6 Test Console (UI)
Purpose: Execute step-by-step workflow tests from UI.

Must support:
- Stage test catalog
- Test data profile selection
- Assertions view (expected vs actual)
- Reproducible test run history

## 3) Interaction Model
- Default flow is fully automated after run start.
- Optional manual checkpoints can be enabled by admin for high-risk deployments.
- Every chart/table row must support drill-down to evidence.

## 4) Visualization Requirements
## 4.1 Timeline
- Daily bins minimum, optionally hourly for short windows.
- Overlay markers for peaks/spikes/trends.
- Hover shows underlying article IDs and source mix.

## 4.2 Map (Gradio Integration)
The map is an inspectable output panel backed by geospatial artifacts.

### Map Output Panel Requirements
- Render marker-based visualization from the Geospatial Map Marker Set artifact.
- Marker size encodes unique article count.
- Marker color encodes intensity (low/medium/high).
- Marker tooltip must show: location label, article count, average confidence, ambiguous-location count.
- Map legend must define:
  - size-to-count buckets,
  - color-to-intensity buckets,
  - uncertainty symbol for ambiguous locations.

### Map Controls
- Confidence threshold filter.
- Source filter.
- Date range filter.
- Cluster filter.
- Ambiguity-only toggle.

### Required Click-through Behavior
1. Click **location marker** → open location drawer with location group ID and metrics.
2. Click linked **cluster ID** in drawer → open cluster detail table.
3. Click **article ID** in cluster table → open article evidence/citation panel.

This enforces the drill path: **location → cluster → articles**.

## 4.3 Tables
- Sort/filter/export for events, articles, sources, and contradictions.
- Confidence and source-weight columns mandatory.

## 5) Validation UX
- Each stage includes a validation card with:
  - Rules executed
  - Failures/warnings
  - Suggested remediation options
- Critic loop outcomes are visible with iteration count and deltas.
- Geospatial validation card must include ambiguity and deduplicated count metrics.

## 6) Accessibility and Usability
- Keyboard navigable core actions.
- Color-safe encodings for confidence and status.
- Plain-language labels for non-technical analysts.

## 7) Auditability in UI
- Immutable run timeline panel with timestamped actions.
- “Why this output?” affordance on generated insights.
- Downloadable audit log per run.
- For map markers, “Why this location?” must show evidence text span and extraction method.

## 8) Assumptions
- Interactive charting and mapping components are available in selected UI stack.
- Authentication/authorization layer exists in hosting environment.

## 9) Open Decisions
1. Single-page vs multi-page application layout.
2. Real-time transport model (polling vs push events).
3. Manual-gate default policy for production deployments.
