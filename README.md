# claude-qlik-docs

Crawler + Claude-Skill-Builder für die [Qlik Talend Dokumentation](https://help.qlik.com/talend/).
Erzeugt einen lokalen, versionierten Wissens-Skill `qlik-talend`, den Claude Code
und Claude Chat token-effizient als Antwort-Kontext nutzen können — ohne die
komplette Doku im Prompt mitzuschleppen.

## Was es kann

- **Crawlt** alle relevanten Talend-Sub-Sitemaps (Studio 8.x, TMC, Remote Engine
  Linux/Windows, Dynamic Engine, Installation, SDLC/CI-CD, Cloud Platform) per
  `httpx + BeautifulSoup + markdownify`. Respektiert `robots.txt`, throttled,
  retried, hash-cached.
- **Cluster + Distill**: gruppiert ~3000 Roh-Pages in ~440 Topics, baut pro
  Topic eine destillierte Markdown-Datei mit TL;DR, Procedure-Outline,
  Notes/Restrictions und einer Citations-Tabelle, die jeden Anchor exakt auf
  Roh-Datei + Source-URL abbildet (keine Halluzinationen, mechanisch generiert).
- **Packagiert** als Claude Skill — `SKILL.md` triggert auf Talend-Fragen,
  navigiert progressiv über Index → Sub-Index → Topic → Roh-Page.

Token-Effizienz pro Frage: typischerweise 25–40 KB Kontext statt 14 MB Mirror.

## Lizenz / Redistribution

Der gecrawlte Qlik-Content ist **nicht** in diesem Repo enthalten und bewusst
in `.gitignore`. Dieses Repo enthält nur **Code + Skill-Scaffolding** (z. B.
`SKILL.md`). Jeder Nutzer crawlt selbst lokal — vergleichbar mit
`pip install`-Logik, nicht mit einem Content-Mirror.

## Setup

```bash
# Voraussetzungen: macOS, Python 3.9+, uv (https://docs.astral.sh/uv/), make
brew install uv
git clone https://github.com/<user>/claude-qlik-docs.git
cd claude-qlik-docs
uv sync                    # legt .venv an, installiert deps
make fresh                 # crawlt (~30 min) + baut Topics + installiert Skill
```

`make fresh` führt aus:
1. `make crawl`    — Crawl von help.qlik.com (~30 min, ~3000 Seiten)
2. `make build`    — Cluster + Topic-Build + Index + Validate
3. `make install`  — Symlink nach `~/.claude/skills/qlik-talend`

Danach in einer **neuen** Claude-Code-Session: einfach Talend-Fragen stellen.
Der Skill triggert automatisch über die Description in `SKILL.md`.

## Re-Crawl

```bash
make crawl    # idempotent, ETag/Hash-Cache schont Bandbreite
make build    # Topics + Index neu generieren
```

## Scope (MS1)

- Talend Studio 8.0 (User Guide + Begleitdokus)
- Talend Management Console (Cloud)
- Remote Engine Linux + Windows (Cloud) + Gen2 + Dynamic Engine
- Installation Guide Linux/Windows (Cloud + 8.0), Hybrid, Migration/Upgrade
- SDLC / CI-CD Best Practices (8.0 + Cloud)
- Talend Cloud Getting Started + Glossary

**Nicht enthalten** (Erweiterung in späteren MS): Components-Referenz, Data
Quality, Data Catalog, Data Stewardship, ESB, API Designer, MDM, 7.x.

## Architektur

```
crawler/      # discovery / fetch / extract / run / validate
distill/      # cluster (heuristisch) / build_topics (mechanisch) / validate_citations
package/      # build_index (top-level + per-group)
spike/        # MS0 discovery findings + extract spike
skill-output/ # Build-Artefakt → wird per Symlink unter ~/.claude/skills/ gelinkt
```

Detail-Plan unter `~/.claude/plans/ich-will-ein-tool-linear-sundae.md` (lokal,
nicht im Repo).

## Erweitern

Neue Talend-Produkte oder andere Qlik-Doku (Sense, QlikView):

1. Sub-Sitemap-Namen aus `https://help.qlik.com/talend/sitemap.xml` (oder
   `https://help.qlik.com/sitemap.xml`) raussuchen.
2. In `crawler/config.py` unter `PRODUCT_SITEMAPS` ergänzen.
3. `make fresh`.

## Roadmap (post-MS1)

- LLM-basierte Distillation als Topic-Layer (aktuell: rein mechanisch, ohne
  Halluzinationsrisiko, dafür weniger Token-Reduktion)
- Re-Crawl-Diff-Report (was hat sich geändert)
- Components-Referenz als separater Sub-Skill
- 7.x-Support parallel (zweiter Versions-Slot)
- Generalisierung auf Qlik Sense / QlikView / Replicate / Compose
