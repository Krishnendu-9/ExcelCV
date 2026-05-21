It's the most-asked question in resume formatting: PDF or Word? The answer in 2026 is more nuanced than the internet wants you to believe — both work in most modern ATS, but each fails in specific edge cases. Here's the data, not the opinion.

## The Short Answer

In 2026, **both PDF and DOCX work in nearly every modern ATS**. If the job posting specifies a format, follow it. If it doesn't:

- **Use DOCX** when applying through legacy or unknown ATS, or when in doubt.
- **Use PDF** when the company explicitly accepts it and you want layout fidelity guaranteed for the human reviewer.

The fights you'll see online about one being universally better are five or more years out of date.

## How ATS Software Reads Each Format

### DOCX

DOCX is XML under the hood. ATS parsers can extract text, headings, lists, and table structure cleanly. The downside: any unusual formatting — custom XML elements, embedded objects, autoshapes — can confuse parsers in surprising ways.

### PDF

Modern text-based PDFs (the kind exported by Word, Google Docs, or Pages) embed text in a structured stream that good parsers can read. The catch: PDF doesn't enforce a consistent reading order. Multi-column or floating-element PDFs can produce parsed text where the columns are interleaved or randomly ordered. Older or scanned PDFs — image-based PDFs — are unreadable to most ATS without OCR. Many systems don't OCR. Those resumes get rejected silently.

## When DOCX Wins

- **Legacy ATS:** Older Taleo, BrassRing, and some on-prem enterprise systems still parse DOCX more reliably than PDF.
- **Unknown ATS:** If the company doesn't say what they use, DOCX is the safer default.
- **Government jobs:** Many federal and state hiring systems explicitly prefer Word documents.
- **You used a complex layout:** Multi-column or table-heavy resumes parse more predictably as DOCX than PDF.

## When PDF Wins

- **You want layout fidelity for the human reviewer.** Word documents render differently across versions and fonts. PDF locks the visual.
- **Modern ATS like Greenhouse, Lever, Workable, Ashby.** These were built post-2015 with strong PDF parsing.
- **Workday.** Workday handles PDF fine and even pre-fills application fields from a parsed PDF.
- **The posting explicitly accepts PDF.** Take the company at its word.

## How Major ATS Platforms Handle Each Format

| ATS | DOCX | PDF | Recommendation |
|---|---|---|---|
| Workday | Excellent | Excellent | Either |
| Greenhouse | Excellent | Excellent | Either |
| Lever | Excellent | Excellent | Either |
| iCIMS | Good | Good | Either, DOCX safer |
| SmartRecruiters | Good | Good | Either |
| Taleo (legacy) | Good | Sometimes poor | DOCX |
| BrassRing | Good | Variable | DOCX |
| BambooHR | Good | Good | Either |
| Workable | Excellent | Excellent | Either |
| Ashby | Excellent | Excellent | Either |

## Common Parsing Failures by Format

### DOCX failure modes

- Text in headers and footers is dropped by most ATS.
- Text inside text boxes is often ignored.
- Tables with merged cells confuse field detection.
- Embedded SmartArt and charts are skipped.
- Tracked changes and comments occasionally bleed into the parse.

### PDF failure modes

- Multi-column layouts parse with the wrong reading order.
- Scanned or image-based PDFs are unreadable.
- Custom or embedded fonts can produce garbled text in some parsers.
- PDFs exported from design tools (Canva, InDesign) often lose text-layer structure.

## The Single Layout Rule That Beats the Format Debate

Whichever format you choose, the single biggest predictor of clean parsing is the same: **one column, top-to-bottom layout, standard fonts, no tables for structure**. A well-formatted single-column resume parses cleanly in both DOCX and PDF. A two-column resume with sidebars fails in both — just in different ways.

## How to Export Each Format the Right Way

### DOCX

- Save as `.docx`, not `.doc` (the `.doc` format is pre-2007 and many ATS no longer support it).
- Use built-in heading styles (H1, H2) — they help parsing.
- Don't use Word headers/footers for content.
- Skip text boxes, SmartArt, and embedded charts.

### PDF

- Export from Word or Google Docs (text-based PDF) — never scan.
- Stick to standard fonts: Arial, Calibri, Helvetica, Times New Roman, Georgia.
- Avoid Canva or InDesign exports unless you've verified text-layer integrity.
- Keep file size under 2 MB.
- Test by opening the PDF and copy-pasting your full resume into a plain text document. If the order comes out wrong, the ATS will see the same wrong order.

## Test Before You Submit

The only way to actually know if your specific resume parses cleanly in either format is to run it through an ATS checker. ExcelCV accepts both PDF and DOCX, runs the same parsing pipeline real ATS platforms use, and shows you exactly which fields were extracted correctly — and which weren't.

## Frequently Asked Questions

**Will my resume be rejected if I use the "wrong" format?**

Rarely outright rejected, but it may be misparsed — which lowers your match score and can effectively reject you. The real risk isn't format choice; it's layout complexity.

**What about plain text (.txt)?**

Some applications still accept `.txt` as a fallback. It's the most ATS-friendly format possible — zero parsing complexity — but offers no visual hierarchy for the human reviewer. Use it only when explicitly required.

**Should I email the same format I uploaded?**

Yes — keep the file consistent across every touchpoint of the same application.

**Does Google Docs export the same as Microsoft Word?**

For DOCX export: very close, with occasional minor formatting differences. For PDF export: nearly identical. Both produce ATS-readable files.

**What if a job asks for both?**

Some applications require DOCX for parsing and PDF for the human reviewer. Upload both if asked, with identical content.

## The Bottom Line

The format war is over and both sides won. Use DOCX as your default unless the company explicitly accepts or requests PDF. Either way, lay your resume out in a single column with standard fonts and run it through ExcelCV before submitting to catch any parsing issues that slipped in.
