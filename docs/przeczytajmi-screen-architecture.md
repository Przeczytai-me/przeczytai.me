# PrzeczytAI.me screen architecture

This document defines the front-end screens needed for PrzeczytAI.me: a Polish document cleanup and text-to-speech application. It focuses on user-facing routes, navigation paths, screen responsibilities, states, and the main interaction model.

## Product assumptions

- Users upload Polish `.txt` or `.md` files in v1. Other formats may be considered later.
- After the user starts processing, the system prepares Speech Synthesis Markup Language (SSML) optimized for AI reading, creates an MP3 narration, and lets the user review the original text, generated SSML, and audio output.
- Users need a private workspace with their uploaded files and generated results.
- Authentication is handled by Clerk, with sign-in and sign-up routes already expected by the project.
- MP3 generation starts after the user uploads a supported file and clicks the `czytAI` start button. There is no manual review or edit step in v1.
- Users can retry generation for a document. A retry creates a new processing job linked to the same document and replaces generated text/audio when it succeeds.
- Original files, generated SSML, and MP3 outputs are deleted when they have not been touched for 365 days.
- Billing is expected to be subscription-based, but plan details are not defined for v1.
- Mobile layouts are out of scope for v1; desktop experience is the design target.

## Recommended route map

| Route | Screen | Access | Primary purpose |
|---|---|---:|---|
| `/` | Landing page | Public | Explain value, show example, and route users toward the protected workspace. |
| `/sign-in` | Sign in | Public | Authenticate existing users. |
| `/sign-up` | Sign up | Public | Create account. |
| `/app` | User workspace | Private | Show a table of uploaded files, statuses, and generated narrations. |
| `/app/new` | New document | Private | Upload a `.txt` or `.md` file, optionally define abbreviation readings, and start processing. |
| `/app/jobs` | Processing overview | Private | Show all active and recent processing jobs with compact progress indicators. |
| `/app/documents/:documentId` | Document reader | Private | Review the original text with playback highlighting, retry generation, and download outputs. |
| `/app/settings` | Settings | Private | Set default model, voice, playback behavior, exports, and custom abbreviation readings for future documents. |
| `/app/account` | Account | Private | Manage profile, sign out, connected auth, and data deletion. |
| `/docs` | Documentation | Public or private | Technical-style product documentation, examples, supported files, and common errors. |
| `/privacy` | Privacy policy | Public | Explain document storage, retention, and AI processing. |
| `/terms` | Terms | Public | Legal terms. |

## User flow

```mermaid
flowchart TD
    Landing["/ Landing page"] --> SignIn["/sign-in"]
    Landing --> SignUp["/sign-up"]
    Landing --> Demo["Public example preview"]

    SignIn --> AuthSuccess["Successful authentication"]
    SignUp --> AuthSuccess
    AuthSuccess --> Workspace["/app Workspace"]

    Workspace --> NewDoc["/app/new New document"]
    Workspace --> Reader["/app/documents/:documentId Reader"]
    Workspace --> Jobs["/app/jobs Processing overview"]
    Workspace --> Settings["/app/settings Settings"]
    Workspace --> Account["/app/account Account"]
    Workspace --> Docs["/docs Documentation"]

    NewDoc --> UploadValidate["Validate .txt or .md file"]
    UploadValidate --> Abbreviations["Optional abbreviation readings"]
    Abbreviations --> Start["User clicks czytAI"]
    Start --> AutoProcess["Cleanup + SSML + MP3"]
    AutoProcess --> Jobs
    Jobs --> Reader

    Reader --> DownloadMP3["Download MP3"]
    Reader --> DownloadSSML["Download generated SSML"]
    Reader --> DownloadOriginal["Download original file"]
    Reader --> Retry["Retry generation"]
    Retry --> AutoProcess
    Reader --> Workspace

    Settings --> Workspace
    Account --> Landing
```

## Information architecture

```mermaid
flowchart LR
    Public["Public area"] --> Landing["Landing"]
    Public --> Auth["Sign in / Sign up"]
    Public --> Legal["Privacy / Terms"]

    Private["Authenticated app shell"] --> Library["Document table"]
    Private --> Create["Upload file"]
    Private --> Jobs["Processing overview"]
    Private --> Reader["Reader and audio player"]
    Private --> Settings["Reading defaults"]
    Private --> Account["Account"]
    Private --> Docs["Documentation"]

    Library --> DocumentRow["Document table row"]
    DocumentRow --> Status["Processing / Ready / Failed"]
    DocumentRow --> Actions["Open / Retry / Download / Delete"]

    Reader --> TextPanel["Original text with playback highlighting"]
    Reader --> Player["Bottom audio player"]
    Reader --> SidePanel["Downloads / metadata / retry"]
```

## Global app shell

Private pages should share one quiet, work-focused shell:

- Left sidebar on desktop with navigation: Documents, New document, Jobs, Settings, Documentation.
- Top bar with product name, current document title when applicable, processing status, account menu, and sign out.
- Mobile navigation is not specified for v1.
- Persistent toast region for upload, processing, download, and save events.
- Breadcrumbs on document detail pages: `Documents / Document title`.
- Main content width should be constrained for reading views, while the workspace table and processing overview may use the full available desktop width.

## Screen specifications

### Landing page `/`

Goal: quickly explain that PrzeczytAI.me turns noisy Polish documents into SSML and generated narration.

Required sections:

- First viewport with product name `PrzeczytAI.me`, short value proposition, sign-in button, sign-up button, and a secondary example/demo link.
- Animated or graphic example showing dirty source text transformed into SSML. Do not include audio playback on the landing page.
- Capability section: cleanup, reading markup, Polish voice generation, synchronized highlighting, downloads.
- Trust/privacy section explaining that documents are private to the user.
- Supported inputs section: `.txt` and `.md`.

Primary actions:

- `Zaloguj sie` routes to `/sign-in`.
- `Utworz konto` routes to `/sign-up`.
- `Przejdz do dokumentow` routes authenticated users to `/app`.

States:

- Public anonymous state.
- Loading auth state with disabled actions.

### Sign in `/sign-in` and sign up `/sign-up`

Goal: let users authenticate with minimal friction.

Required elements:

- Clerk auth form.
- Link back to landing page.
- Clear title matching action: `Zaloguj sie` or `Utworz konto`.
- Optional note that documents are stored in the user's private workspace.

Post-auth routing:

- Existing and new users are automatically redirected to `/app` after successful sign-in or sign-up.

### Workspace `/app`

Goal: show the user's document library and transformation results in a dense table.

Required layout:

- Header with `Dokumenty`, search input, status filter, sort menu, and `Nowy dokument` button.
- Summary strip: total documents, currently processing, ready narrations, storage/export count if available.
- Document table as the primary layout.

Document table columns:

- Document title.
- Source type and upload date.
- Status: `Processing`, `Ready`, `Failed`.
- Voice/model used.
- Character count and generated audio length when available.
- Retry/action availability when the latest generation failed or the user wants to regenerate output.
- Quick actions: open, download MP3, download SSML, download original file, retry, delete.

Empty state:

- Title: `Nie masz jeszcze dokumentow`.
- Action: `Dodaj pierwszy dokument`.

Error state:

- If documents fail to load, keep the shell visible and show retry.

### New document `/app/new`

Goal: upload a supported file and start cleanup, SSML generation, and narration.

Required flow:

1. Upload `.txt` or `.md` file.
2. Source preview: show file name, type, size, detected character count, and first lines of extracted text.
3. Optional abbreviation readings: let the user provide abbreviation and full reading text pairs.
4. Start action: `czytAI`.

Abbreviation handling:

- Explain that PrzeczytAI.me tries to read abbreviations correctly by default.
- Allow users to provide exact readings when they want control over a specific abbreviation.
- Each row should include `Abbreviation` and `Read as` fields, plus add/remove row controls.
- These document-level abbreviation readings apply only to the uploaded document unless the user saves them as defaults in settings.
- Do not specify lower-level preprocessing rules here; v1 only needs the UI contract for collecting abbreviation readings.

Validation:

- Reject unsupported file types with a specific explanation; v1 accepts only `.txt` and `.md`.
- Reject extracted text over 10,000 characters for v1.
- Require exactly one uploaded file.
- Validate that abbreviation pairs are complete when provided.

After start:

- Route to `/app/jobs` or back to `/app` with visible processing status.
- Do not show cleanup options in v1; cleanup behavior is internal.

Character limit note:

- A 10,000-character limit is reasonable for v1 if the goal is predictable latency, lower TTS cost, and simpler UI states.
- The UI should explain this as a version-one limit and show the detected character count before submission.

### Processing overview `/app/jobs`

Goal: make asynchronous cleanup and audio generation understandable without creating a per-document job page.

Required elements:

- List of active and recent jobs.
- Per-job status badge: uploaded, extracting text, generating SSML, generating MP3, ready, failed.
- Per-job progress bar when progress is available.
- Optional per-job log/progress detail if the backend exposes it.
- Current step message.
- Link to the document when ready.
- Retry action for failed documents.
- Non-blocking note that users can leave this page and return later.
- Multiple jobs may belong to the same document; for example, the original generation and a later retry.

Failure state:

- Show failed step, readable reason, retry action, and link to documentation.

### Document reader `/app/documents/:documentId`

Goal: combine reading, listening, status, and downloads in one focused screen.

Desktop layout:

- Main reading column with the original text and current-sentence playback highlighting.
- Sticky right side panel with document metadata, download actions, retry action, and processing details.
- Persistent bottom audio player spanning the main content area.
- Sentence-level highlight synced to audio playback.
- If processing is not ready, the route should render a full-screen warning that the user needs to wait and link to `/app/jobs`.

Required controls:

- Bottom player controls: play/pause, seek bar, speed control, previous sentence, next sentence.
- Right side panel actions: download MP3, download generated SSML, download original source file, retry generation.
- Toggle sentence highlights.

Text behavior:

- Current sentence highlight should be visually strong but not obscure text.
- Past sentences may use a subtle completed style.
- Clicking a sentence seeks audio to that sentence when the backend provides a text-to-audio timing map.
- V1 should expect a generated timing map rather than trying to infer timing purely from cleaned text in the browser.
- If timing map data is unavailable, show a no-sync fallback instead of guessing incorrect sentence timing.

States:

- Audio ready.
- Processing not ready: full-screen wait warning with link to `/app/jobs`.
- MP3 generation failed.
- Missing original file but generated SSML available.
- Empty extracted text.
- Retry available.

### Settings `/app/settings`

Goal: control defaults for future documents.

Sections:

- Reading model: default TTS model, fallback model.
- Voice: default Polish voice, voice preview, pronunciation style.
- Playback: default speed, sentence highlight behavior.
- Custom abbreviation readings for future documents.
- Exports: default output file names, MP3 quality, text format.
- Privacy: inactive-for-365-days retention notice, delete all documents if supported.

Required behavior:

- Settings affect future documents only.
- Show unsaved changes bar.
- Provide reset-to-defaults action.

### Account `/app/account`

Goal: profile and session management.

Required elements:

- Clerk profile/account management.
- Sign out.
- Email address.
- Data deletion request or direct delete flow if supported.
- Link to privacy policy.

### Documentation `/docs`

Goal: provide technical-style product documentation similar to common developer/product documentation sites.

Recommended content:

- Supported file formats: `.txt` and `.md`.
- 10,000-character limit and how it is counted.
- What cleanup changes.
- How SSML generation works at a high level.
- How reading pauses and pronunciation handling work.
- How custom abbreviation readings work.
- How to improve pronunciation.
- Common processing errors and fixes.
- Privacy and inactive-for-365-days retention summary.

## Suggested screens not in the original request

- `/app/new`: dedicated upload flow. Without this, the workspace table becomes overloaded.
- `/app/jobs`: aggregate processing overview. Audio generation can take time, but v1 does not need per-job detail routes.
- `/docs`: documentation-style help for file quality, Polish pronunciation, abbreviation handling, and failed jobs.
- `/privacy`: important because users upload private documents for AI processing.
- `/app/account`: account and deletion controls should not be buried inside settings.

## Core navigation rules

- Public users can only reach `/`, `/sign-in`, `/sign-up`, `/docs`, `/privacy`, and `/terms`.
- Private routes redirect anonymous users to `/sign-in`.
- After successful sign-in or sign-up, users are automatically redirected to `/app`.
- Authenticated users visiting `/` should see a direct route to `/app`.
- Processing starts after upload when the user clicks the `czytAI` button.
- Finished processing jobs route to the reader.
- The reader should always provide a route back to the workspace and to `/app/jobs`.
- `/app/documents/:documentId` should not show partially processed documents; use the full-screen wait warning instead.

## Main object lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Uploaded: .txt or .md uploaded
    Uploaded --> ExtractingText: user clicks czytAI
    ExtractingText --> GeneratingSSML
    GeneratingSSML --> GeneratingAudio
    GeneratingAudio --> Ready
    ExtractingText --> Failed
    GeneratingSSML --> Failed
    GeneratingAudio --> Failed
    Failed --> Uploaded: retry generation
    Ready --> Uploaded: retry generation
```

## Design direction

The product should feel like a focused document workspace, not a marketing-heavy AI toy.

- Use restrained, high-contrast typography and generous reading line height.
- Prioritize table scanning, playback controls, and clear processing states.
- Use tables for the workspace. Use cards only for modals or small repeated documentation examples.
- Prefer icons for repeated actions: upload, play, pause, download, settings, delete, retry.
- Use Polish UI copy by default.
- Keep long Polish labels from overflowing by designing flexible buttons and responsive wrapping.
- Treat desktop as the v1 target; responsive/mobile behavior can be specified after the core product is proven.

## Accessibility requirements

- All player controls must be keyboard accessible.
- Current sentence highlight must not rely on color alone.
- Audio player needs visible focus states and screen-reader labels.
- Processing status should announce step changes politely.
- Upload drop zone must also support a standard file input button.
- The generated timing map should be exposed in a way that lets assistive technology understand the currently active sentence.

## Resolved product decisions

- V1 supports `.txt` and `.md` files only.
- Users cannot paste text in v1.
- MP3 generation happens after the user uploads a supported file and clicks `czytAI`.
- Users cannot manually edit generated SSML before audio generation.
- Users can retry generation for a document; retry limits are not fixed in this screen spec.
- `/app/documents/:documentId/edit` is not needed for v1.
- `/app/jobs` is an aggregate processing overview; there is no `/app/jobs/:jobId` route.
- Sentence highlighting should be driven by a backend-generated timing map.
- The product will be subscription-based, with details still undefined.
- Original files, generated SSML, and MP3 outputs are deleted after 365 days without being touched.

## Open product decisions

- What exact subscription limits apply: documents per month, characters per month, storage, or generated audio minutes?
- What exact retry limits apply, if any?
- Should default abbreviation readings be global per user, grouped by document type, or both?
- Should `/docs` be fully public, or should some operational documentation require authentication?
- Should the reader expose an original/generated SSML toggle in v2?
