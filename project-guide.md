# BrandWise overview
BrandWise reviews marketing and brand content against a company's approved claims, terminology, guidelines, and required disclaimers. It produces an explainable audit with findings, evidence references, suggested wording, a score, and a review workflow. Rule checks are deterministic. Optional AI review adds suggestions that still require a human decision. Scores are policy-risk indicators, not a legal-compliance guarantee or AI accuracy score.

## Navigating BrandWise
The left navigation opens Audit Workspace, Official Guidelines, Audit History, Brand Assets, Calendar, Team Overview, Settings, and Profile. Team Overview is for company administrators. BrandWise Guide is the robot button at the bottom right. It can answer general product questions at any time and use an open saved audit for detailed follow-up questions.

## Appearance and dark mode
Open Settings, then Appearance to choose the workspace color theme. The sign-in page also has a Theme selector near the top right. The theme preference is saved in the browser.

## Calendar and reminders
Open Calendar in the left navigation. Select a date or use + Add reminder. Enter a title, type, date, time, and optional notes, then save. Turn on Notify me at this time for an in-app or browser notification. The calendar also shows upcoming items and has search and month navigation. Browser notifications depend on browser permission and an open app session.

## Audit Workspace and running an audit
Open Audit Workspace. Enter an optional audit name and paste or import draft content. Choose whether to include optional AI review, then use AUDIT CONTENT to save and check it. The audit report shows the score, configured passing threshold, confidence estimate, findings, evidence, suggested wording, and activity. A finding can be reviewed, edited, dismissed, or reported as incorrect through its controls. Start new audit clears the current report and draft editor.

## Audit findings, scores, and detailed questions
Each finding can include its category, title, severity, why it was flagged, matched wording, source ID, evidence reference, location, suggested fix, action status, and uncertainty or human-review flags. Ask BrandWise Guide which issues to fix first, why a specific phrase was flagged, how a suggestion relates to a source, how to rewrite a sentence, or what remains before approval. The saved report's findings and draft are the authority for audit-specific answers. A score is calculated from configured rule checks and unresolved findings. A high or critical pending finding can block approval. Meeting the score threshold alone does not automatically approve a draft.

## Review, revisions, and approval
Saved audits appear in Audit History and can be reopened with View Report. The workspace has a version comparison and reviewer discussion. Authorized Reviewer, Brand Manager, or Admin roles can request changes or approve eligible drafts. The Approve control is in the audit report's stage bar. Approval requires the configured threshold and no pending high or critical finding. Publication requires approval and disposition of pending findings. A new draft revision requires another review. BrandWise Guide explains the steps but cannot approve, publish, or change an audit itself.

## Official Guidelines and claims
Official Guidelines contains the company's guidance for tone, terminology, required disclaimers, and accessibility. The claims ledger holds statements and supporting details such as source, status, owner, and expiry. Active, relevant claims support audit checks. Expired or unsupported claims need human verification. Brand Manager and Admin roles manage shared claims and guidelines. BrandWise Guide can explain the current workspace guidance to signed-in users while respecting their workspace access.

## Brand Assets
Open Brand Assets in the left navigation to find and manage workspace brand files. Availability and sharing depend on the active company workspace. The audit engine checks text and metadata. It does not inspect logo pixels or artwork automatically.

## Settings, accounts, and workspaces
Settings contains audit preferences, appearance, notifications, workspace profile, brand configuration, and service key controls for administrators. Audit preferences include strictness and a passing threshold. Profile contains personal account details. A company administrator manages the team and invitations in Team Overview. Users sign in to access private workspace data. Public visitors can ask BrandWise Guide general product questions, but saved audits and company guidance require account access.

## Accessibility and supported content
The app estimates reading grade and checks Markdown or HTML heading order. The WCAG and Contrast Studio provides a manual color contrast calculator. These checks do not analyze images or logo pixels. Supported draft imports include TXT, Markdown, CSV, PDF, and DOCX. The product does not provide OCR, image review, Hindi or regional-language validation, or direct Google Docs, Canva, or Figma connectors in the running demo.

## AI review and chat privacy
Audit checks can run without AI. Optional browser AI review runs a downloaded local model in the browser. Optional Gemini review sends the selected draft and relevant guidance to Google when configured. BrandWise Guide first uses the integrated in-browser model for questions. On first use the browser downloads and caches model files. If the browser model cannot run, the app can use a configured Gemini or OpenAI server key as a fallback, sending the question, recent chat, relevant product guidance, and any open audit context to that provider. Answers can be mistaken and do not replace reviewer decisions.
