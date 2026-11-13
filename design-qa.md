# Design QA

Source visual truth: ../design/app-v1/home.png, registration.png, account.png.
Implementation evidence: qa/home-mobile.png, qa/registration-mobile.png, qa/account-mobile.png, qa/registration-tablet.png, qa/account-desktop.png.

Viewports: 390x844 CSS px for source comparisons; additional checks at 320x740, 768x1024 and 1440x1000. Screenshots use browser output density. Reference images are 977px wide; compare scaled to the available mobile content width. Full-page evidence includes fixed navigation at the captured viewport position; this is not an extra content row.

## Findings and iteration history

- P2: Header links crossed the bright sky and lost contrast. Fixed with a dark translucent backing; checked in the tablet and mobile captures.
- P2: Latin digits used fallback fonts. Added local Latin font subsets alongside Cyrillic. Stats now use Montserrat consistently.
- P2: Initial registration full-page capture was incomplete during rendering. Recaptured after inspecting the settled page; fields span the content width and the hero renders correctly.
- P2: Long names could overflow the greeting. Added heading wrapping and fluid sizing.

## Required fidelity surfaces

Typography: Montserrat 400/600/700/800 and Open Sans 400/600, local Latin and Cyrillic. Main hierarchy, bold navy headings and uppercase labels preserved. Form text is at least 16px in inputs to avoid mobile autozoom.
Spacing: same order and anatomy as selected mocks. Desktop expands to columns; mobile keeps one content column. Readable touch sizes and extra vertical space are intentional responsive adaptations, not raster copies of the mocks.
Colors: navy #1E3A8A, blue #3B82F6, cyan #22D3EE, pale #F8FAFC. Green confirmation remains semantic.
Imagery: generated Yugra river/forest background with cyan contours; generated white brand lockup. No rasterized UI. Real Phosphor library icons. P3: replace raster logo with the official vector original when available.
Copy: core headings and example stats preserved. Demo notices explicitly distinguish illustrative data, local file selection and inactive email/AI integration. No fake server success.

## Comparison evidence

Opened source and mobile implementation images in the same comparison input for registration and account; home reference and implementation inspected, then compared together in final review. Focused readable regions: form inputs/consent, statistics, upload controls, recent activity. Template status bars and device frames are absent because the user explicitly requested a responsive website across all screen sizes.

## Functional checks

Browser: registration name/email/consent -> demo code; wrong code error; correct code -> personalized account. History dialog opens and closes. Manual review explains that no request was sent. File chooser selects PNG, preview appears, check action states that API/AI are not connected. Reload clears participant/file state. Browser error log: empty. No horizontal overflow observed at checked widths. Production build and four Sites worker tests pass.

## Follow-up polish

P3: replace the generated raster brand lockup with an official vector asset. Test on physical iOS/Android before production. Backend, real email and AI are future work and outside this visual prototype.

final result: passed

## Iteration: administration and documents, 13 November 2026

User-requested extension of the approved existing brand. Added /#admin, /#rules, /#privacy and /#consent; kept the original three-page visual direction. Evidence: qa/admin-desktop.png (1440x1000), qa/admin-mobile.png (390x844), qa/privacy-mobile.png (390x844). Readable mobile document content checked also at 320x740; no horizontal overflow observed. At 1440px the admin uses sidebar/queue/review columns; at 390px the layout stacks. Selecting a queue row on mobile now scrolls to the review, resolving an offscreen-feedback usability issue.

Fonts, spacing, navy/cyan palette and header assets follow the approved main/app design. Documents use calm body typography, numbered headings and a persistent desktop document index. Legal content is explicitly a draft and contains no invented operator details, launch dates or prizes. Admin records use example.com addresses and fictional participant labels. The empty screenshot area describes absent demo files and does not masquerade as a real training screenshot.

Browser checks: rejecting without a reason displays an error; approving 6.30 km updates confirmed total to 11.40 km; journal records action/distance/comment. Search empty state and reset work. Two registration checkboxes are initially false; submitting with only rules checked stays on the form, then checking consent proceeds to the demo code screen. Browser error logs empty. Four Sites runtime tests and three isolated SMTP diagnostic unit tests pass. Real TLS SMTP connectivity separately checked from the home server; credentials and delivery remain unverified.

Comparison: original approved home/registration visual direction and rendered extensions inspected for coherent typography, white surface, navy headings, spacing and image treatment. New admin/document anatomy is requested functionality, not an exact clone of an absent screen. No remaining actionable P0/P1/P2 findings in the demonstrated frontend scope. Actual server authentication, role enforcement and mail delivery remain intentionally unimplemented and are not represented as working.

final result: passed

## Supplied legal documents update

Replaced draft policy and consent with owner-provided Markdown, preserving wording. Policy source byte-for-byte matches the supplied attachment. Rendering only translates headings, lists, bold text and links into React elements; no raw HTML execution. Operator details are owner-supplied, not independently verified. Existing styling reused. Evidence: qa/policy-supplied.png and qa/consent-supplied-mobile.png, direct /policy/ and /consent/ visits. Mobile viewport 390x844, no horizontal overflow; browser error log empty. Implementation notice about inactive server consent capture is visually separate from the document text. Static route copies generated by build. No new actionable visual issues.

final result: passed

## Complete frontend iteration — 13 November 2026

Source truth: approved design/app-v1/account.png for brand/layout system; owner-supplied rules message for content. New history and leaderboard are requested functional extensions, not screenshot clones. Same-input comparison reviewed the approved account reference alongside qa/history-320.png and qa/leaderboard-final.png. Focused regions: stat hierarchy, filters, rows, status chips and bottom navigation. Source image 977px wide is scaled for comparison to browser CSS widths; no device chrome duplicated.

Evidence: qa/history-320.png (320x740), qa/leaderboard-320-list.png (320x740), qa/leaderboard-final.png (390x844), qa/history-desktop.png (1440x1000), qa/admin-tablet-final.png (768x1024). New screens inspected in development and production preview. CSS viewport sizes verified in the browser; initial resize affected the production tab rather than dev tab, so the actual 320/1440 captures were repeated on the production tab. No horizontal overflow found.

Typography: local Montserrat/Open Sans retained, fluid headings wrap at 320px, inputs are 16px on mobile. Spacing: one-column mobile and two-column desktop history, responsive admin review; navigation stays reachable and content has bottom clearance. Color: established navy, cyan and pale surfaces, semantic status colors. Imagery: original generated river hero retained; a generated community-symbol icon provides PNG launcher sizes. No artificial training image presented as real. Copy: rewritten owner rules preserve running/GPS/indoor HR and prize conditions, and explicitly leave dates/ages/numerical limits unspecified. Recognition outputs remain labelled examples, not extracted values.

P2 fixes: made avatar background dark enough over sky; increased icon touch targets; changed member rules navigation to an SPA hash to preserve demo state; protected selected images from leaking after non-submitted upload component unmount. Existing header and form visual hierarchy preserved. P3: replace generated raster logo with official vector when available; verify physical iOS/Android installation before launch.

Browser interactions passed: history filters; rejected reason and retry link; deletion of 13.22 confirmed km changed personal 71.68 -> 58.46 and common 508.20 -> 494.98; undo restored both. Leaderboard empty search/reset. Local image selection -> waiting -> labelled example -> shared moderation queue -> zoom to 125% -> approve -> personal 84.90. Network-error/retry and unclear-result/manual-review branches passed. Expired demo session and expired code UI observed; repeat request, 60-second countdown, incorrect-code error and correct-code entry passed. Install instructions rendered in production preview. Browser error logs empty.

Seven build/runtime/PWA tests pass: static route output, icon dimensions, offline shell fallback, API/uploads/POST/cross-origin cache bypass, existing Worker routing. Service worker is production-only; real browser installation, physical-device offline behavior and a full update lifecycle remain prelaunch checks. No real authentication, email sending, persistence or AI was enabled by this frontend iteration. SMTP delivery is separately confirmed by the owner.

final result: passed
