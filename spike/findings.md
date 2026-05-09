# MS0 Discovery Spike — Findings

**Date:** 2026-05-09
**Goal:** Eliminate the technical unknowns before MS1 (SSR vs. JS rendering, TOC discovery, robots.txt, entry URLs).

## Summary

All MS0 risks are green. **MS1 can start without changing the stack:** `httpx + BeautifulSoup + markdownify` is sufficient — no Playwright needed.

## 1. robots.txt

- `https://help.qlik.com/robots.txt` is `User-agent: *` with a long Disallow list.
- Disallowed: many 7.x paths, the MDM area (8.0), Data Catalog (8.0), `archive-release-notes/8.0`, `features-per-license-and-application/8.0`, `upgrading-java-from-8-to-11-for-remote-engine/8.0`.
- **MS1-relevant products are NOT disallowed**: Studio User Guide 8.0, Management Console (Cloud), Remote Engine (Linux/Windows, Cloud), SDLC best practices 8.0, installation/upgrade.
- Quirk: every Disallow path uses the prefix `/talend/talend/...` (doubled), while real URLs use `/talend/...` (single). We respect the Disallows defensively as "intended" and stay within Major 8.x or Cloud (out of scope anyway).
- **Rate-limit plan:** 1 req/s, exponential back-off on 429/5xx, max 5 retries (`tenacity`).

## 2. Sitemap discovery

- The main sitemap `https://help.qlik.com/sitemap.xml` does **not** include Talend.
- A **Talend-specific sitemap index** exists: `https://help.qlik.com/talend/sitemap.xml` (sitemap-index, 712 sub-sitemaps).
- Sub-sitemap naming scheme: `sitemap_<product-slug>_<version>_<locale>.xml` with versions `Cloud / 8.0 / 8.1 / 7.3 / 7.2` and locales `en-US / fr-FR / ja-JP / ...`.
- The Studio User Guide has **one sitemap per R-code**; latest = `8.0-R2026-04`. We always pick the latest R-variant.
- The on-page TOC (left navigation) is **not** discovery-relevant — the sitemap covers everything. We use the sitemap as the single source of truth; the TOC is only used optionally to enrich hierarchy in MS2.

## 3. SSR vs. JS rendering

- Test: `curl ... studio-user-guide/8.0-R2026-04/welcome-to-talend-studio` → 50 KB HTML.
- The initial HTML contains the body text in full (22 hits on key strings, all `<h1>`/`<h2>` directly in the markup).
- No React/Next/Angular markers: no `__NEXT_DATA__`, no `window.__INITIAL_STATE__`, no `data-reactroot`, no `<app-root>`.
- **Verdict: SSR.** `httpx + BeautifulSoup` is sufficient; Playwright is not required.

## 4. Content selector

- Main container: **`div#topicContent`** (inside `<main id="main">`).
- Validated on 4 products (Studio, TMC, Remote Engine Linux, SDLC) — identical structure.
- Junk to strip: `script, style, noscript, iframe, svg, nav, footer, header, .feedback, .rating, [class*=version-selector], [class*=breadcrumb], button, .doc-feedback, [id*=feedback]`.
- Compression ratio (markdown / HTML): **0.6 % – 8 %**, depending on content density. Healthy.

## 5. URL pattern + version parsing

```
/talend/<locale>/<product-slug>/<version>/<page-slug>
```

- `version` is either `Cloud` or `<major>.<minor>[-R<YYYY>-<MM>[-and-earlier]]`.
- Parser extracts `major_version` (`Cloud` or `8.0`) and `r_code` (`R2026-04`, otherwise empty).

## 6. MS1 sitemap selection (committed)

| Sitemap | URLs |
|---------|-----:|
| `studio-user-guide_8.0-R2026-04_en-US` | 991 |
| `management-console-user-guide_Cloud_en-US` | 223 |
| `remote-engine-user-guide-linux_Cloud_en-US` | 110 |
| `remote-engine-user-guide-windows_Cloud_en-US` | 87 |
| `remote-engine-gen2-quick-start-guide_Cloud_en-US` | 47 |
| `software-dev-lifecycle-best-practices-guide_8.0_en-US` | 65 |
| `installation-guide-linux_Cloud_en-US` | 98 |
| `installation-guide-windows_Cloud_en-US` | 94 |
| `installation-guide-linux_8.0_en-US` | (to count) |
| `installation-guide-windows_8.0_en-US` | (to count) |
| `migration-upgrade-guide_8.0_en-US` | 53 |
| `dynamic-engine-configuration-guide_Cloud_en-US` | 87 |
| `talend-cloud-getting-started_Cloud_en-US` | 16 |
| `development-operational-management_Cloud_en-US` | 5 |

**Estimated ~1,876 pages** for MS1. At 1 req/s that's roughly 30 min for a full crawl. Sub-second ETag/hash caching makes re-runs cheap.

The Studio "companion docs" relevant to MS1 (`discovering-talend-studio_8.0`, `creating-using-metadata-talend-studio_8.0`, `using-context-variables-talend-studio_8.0`, `studio-getting-started-guide-data-integration_8.0`, `joining-two-data-sources-tmap-talend-studio_8.0`, `reading-a-file-talend-studio_8.0`, `sorting-a-file-talend-studio_8.0`) are included in MS1 too.

## 7. Known polishing items for MS1

- **Title-joining bug:** `get_text(strip=True)` produces `"What isTalend Studio?"` instead of `"What is Talend Studio?"`. Fix: `get_text(separator=" ", strip=True)` plus whitespace collapse.
- **Info-icon artefacts:** "Information noteNote:" / "Information noteRestriction:" — the icon span has no text separator. Fix: drop `<span class="info-icon">`-style elements before running markdownify.
- **`version_constraints` heuristic too eager:** picks up sentences like "available in the following regions". Fix: tighten the regex to require concrete version numbers (`\d+\.\d+(?:\.\d+)?(?:-R\d{4}-\d{2})?`).

## 8. Spike deliverable

- `spike/extract_one_page.py` — end-to-end path (URL → fetch → extract → markdown + frontmatter). Works on all 4 products.
- `spike/out/*.md` — sample outputs.
- Invocation: `uv run python spike/extract_one_page.py [<url>]` (without an argument: Studio sample page).

## Decision

**Greenlight for MS1** with the planned stack. No changes to the MS1 plan — fold the polishing items from §7 into MS1 implementation.
