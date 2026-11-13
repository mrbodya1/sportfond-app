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
