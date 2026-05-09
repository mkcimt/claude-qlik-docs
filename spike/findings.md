# MS0 Discovery-Spike — Findings

**Datum:** 2026-05-09
**Ziel:** Technische Unbekannte vor MS1 ausräumen (SSR vs. JS-Rendering, TOC-Discovery, robots.txt, Einstiegs-URLs).

## Zusammenfassung

Alle MS0-Risiken sind grün. **MS1 kann ohne Stack-Änderung starten:** `httpx + BeautifulSoup + markdownify` reicht, kein Playwright nötig.

## 1. Robots.txt

- `https://help.qlik.com/robots.txt` ist `User-agent: *` mit langer Disallow-Liste.
- Disallowed: viele 7.x-Pfade, MDM-Bereich (8.0), Data-Catalog (8.0), `archive-release-notes/8.0`, `features-per-license-and-application/8.0`, `upgrading-java-from-8-to-11-for-remote-engine/8.0`.
- **MS1-relevante Produkte sind NICHT disallowed**: Studio User Guide 8.0, Management Console (Cloud), Remote Engine (Linux/Windows, Cloud), SDLC-Best-Practices 8.0, Installation/Upgrade.
- Kuriosität: alle Disallow-Pfade haben Prefix `/talend/talend/...` (doppelt), echte URLs nutzen `/talend/...` (einfach). Wir respektieren die Disallows defensiv als „gemeint" und halten uns an Major 8.x bzw. Cloud (Out-of-Scope sowieso).
- **Rate-Limit-Plan:** 1 req/s, exponentiales Backoff bei 429/5xx, max 5 Retries (`tenacity`).

## 2. Sitemap-Discovery

- Hauptsitemap `https://help.qlik.com/sitemap.xml` enthält **kein** Talend.
- **Talend-eigener Sitemap-Index** existiert: `https://help.qlik.com/talend/sitemap.xml` (sitemap-index, 712 Sub-Sitemaps).
- Schema der Sub-Sitemaps: `sitemap_<product-slug>_<version>_<locale>.xml` mit Versionen `Cloud / 8.0 / 8.1 / 7.3 / 7.2` und Locales `en-US / fr-FR / ja-JP / ...`.
- Studio User Guide existiert **pro R-Code als eigene Sitemap**, neueste = `8.0-R2026-04`. Wir nehmen jeweils die neueste R-Variante.
- TOC selbst (linke Navigation auf Seiten) ist **nicht** discovery-relevant — Sitemap deckt alles ab. Wir verwenden Sitemap als Single Source of Truth, TOC nur optional für Hierarchie-Anreicherung in MS2.

## 3. SSR vs. JS-Rendering

- Test: `curl ... studio-user-guide/8.0-R2026-04/welcome-to-talend-studio` → 50 KB HTML.
- Initial-HTML enthält Body-Text vollständig (22 Treffer auf Schlüssel-Strings, alle `<h1>`/`<h2>` direkt im Markup).
- Keine Marker für React/Next/Angular: kein `__NEXT_DATA__`, kein `window.__INITIAL_STATE__`, kein `data-reactroot`, kein `<app-root>`.
- **Verdikt: SSR.** `httpx + BeautifulSoup` ausreichend, Playwright nicht erforderlich.

## 4. Content-Selektor

- Main-Container: **`div#topicContent`** (innerhalb von `<main id="main">`).
- Validiert auf 4 Produkten (Studio, TMC, Remote Engine Linux, SDLC) — identische Struktur.
- Junk zum Strippen: `script, style, noscript, iframe, svg, nav, footer, header, .feedback, .rating, [class*=version-selector], [class*=breadcrumb], button, .doc-feedback, [id*=feedback]`.
- Compression-Ratio (Markdown / HTML): **0.6 % – 8 %**, je nach Content-Dichte. Gesund.

## 5. URL-Pattern + Versions-Parsing

```
/talend/<locale>/<product-slug>/<version>/<page-slug>
```

- `version` ist entweder `Cloud` oder `<major>.<minor>[-R<YYYY>-<MM>[-and-earlier]]`.
- Parser extrahiert `major_version` (`Cloud` oder `8.0`) und `r_code` (`R2026-04`, sonst leer).

## 6. MS1-Sitemap-Selektion (verbindlich)

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
| `installation-guide-linux_8.0_en-US` | (zu zählen) |
| `installation-guide-windows_8.0_en-US` | (zu zählen) |
| `migration-upgrade-guide_8.0_en-US` | 53 |
| `dynamic-engine-configuration-guide_Cloud_en-US` | 87 |
| `talend-cloud-getting-started_Cloud_en-US` | 16 |
| `development-operational-management_Cloud_en-US` | 5 |

**Geschätzt ≈ 1.876 Seiten** für MS1. Bei 1 req/s ≈ 30 min Crawl pro Vollversion. Sub-Sekunden-ETag/Hash-Caching macht Re-Runs billig.

Die für MS1 relevanten Studio-„Begleitdokus" (`discovering-talend-studio_8.0`, `creating-using-metadata-talend-studio_8.0`, `using-context-variables-talend-studio_8.0`, `studio-getting-started-guide-data-integration_8.0`, `joining-two-data-sources-tmap-talend-studio_8.0`, `reading-a-file-talend-studio_8.0`, `sorting-a-file-talend-studio_8.0`) werden in MS1 mitaufgenommen.

## 7. Bekannte Polishing-Items für MS1

- **Title-Joining-Bug:** `get_text(strip=True)` erzeugt `"What isTalend Studio?"` statt `"What is Talend Studio?"` — Fix: `get_text(separator=" ", strip=True)` und Whitespace-Collapse.
- **Info-Icon-Artefakte:** "Information noteNote:" / "Information noteRestriction:" — Icon-Span ohne Text-Trenner. Fix: `<span class="info-icon">` o.ä. komplett strippen, bevor markdownify läuft.
- **`version_constraints`-Heuristik zu eager:** sammelt Sätze wie „available in the following regions". Fix: Regex auf konkrete Versionsnummern (`\d+\.\d+(?:\.\d+)?(?:-R\d{4}-\d{2})?`) verengen.

## 8. Spike-Deliverable

- `spike/extract_one_page.py` — End-to-End-Pfad (URL → fetch → extract → markdown + frontmatter). Funktioniert auf 4 Produkten.
- `spike/out/*.md` — Beispiel-Outputs.
- Aufruf: `uv run python spike/extract_one_page.py [<url>]` (ohne Argument: Studio-Beispielseite).

## Entscheidung

**Greenlight für MS1** mit dem geplanten Stack. Anpassungen am MS1-Plan: keine. Polishing-Items aus §7 in MS1-Implementation einfließen lassen.
