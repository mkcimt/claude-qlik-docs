# claude-qlik-docs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Crawler + Claude-skill builder for the [Qlik Talend documentation](https://help.qlik.com/talend/).
Produces a local, versioned knowledge skill `qlik-talend` that Claude Code and
Claude Chat can use as token-efficient answer context — without dragging the
full documentation into every prompt.

## What it does

- **Crawls** all relevant Talend sub-sitemaps (Studio 8.x, TMC, Remote Engine
  Linux/Windows, Dynamic Engine, installation, SDLC/CI-CD, Cloud platform)
  using `httpx + BeautifulSoup + markdownify`. Honours `robots.txt`, throttles,
  retries, hash-caches.
- **Clusters and distils**: groups ~3,000 raw pages into ~440 topics; produces
  one distilled markdown file per topic with TL;DR, procedure outline, notes
  and restrictions, plus a citations table that maps each anchor exactly to
  the source raw file and canonical URL (no hallucinations — generated
  mechanically).
- **Packages** as a Claude skill — `SKILL.md` triggers on Talend questions and
  navigates progressively from index → sub-index → topic → raw page.

Token cost per question: typically 25–40 KB of context instead of the 14 MB
full mirror.

## License / redistribution

The crawled Qlik content is **not** included in this repo and is intentionally
in `.gitignore`. The repo only ships **code and skill scaffolding** (e.g.
`SKILL.md`). Each user crawls locally — comparable to `pip install`-style
installation, not a content mirror.

## Setup

```bash
# Prerequisites: macOS, Python 3.9+, uv (https://docs.astral.sh/uv/), make
brew install uv
git clone https://github.com/ElRakiti/claude-qlik-docs.git
cd claude-qlik-docs
uv sync                    # creates .venv, installs deps
make fresh                 # crawls (~30 min) + builds topics + cc-install
```

`make fresh` runs:
1. `make crawl`       — crawl help.qlik.com (~30 min, ~3,000 pages)
2. `make build`       — cluster + topic-build + index + validate
3. `make cc-install`  — symlink to `~/.claude/skills/qlik-talend`

After that, in a **new** Claude Code session, just ask Talend questions. The
skill triggers automatically via the description in `SKILL.md`.

## Distribution targets

Two surfaces, two targets — explicitly named so it is obvious which one is
for what:

### Claude Code (CLI, on your local machine)

```bash
make cc-install      # symlinks skill-output/qlik-talend → ~/.claude/skills/qlik-talend
make cc-uninstall    # removes the symlink
```

The skill uses the local `raw/` files as the source of truth for detailed
look-ups — maximum fidelity, no network needed.

### Claude Chat (claude.ai, in the browser)

```bash
make chat-bundle     # produces dist/qlik-talend-chat.zip (~600 KB)
```

The bundle contains **no** raw files (Chat has no filesystem access).
Instead, every citations table points directly at the canonical URLs on
`help.qlik.com/talend`. When Claude needs the exact wording it can fetch the
URL via WebFetch.

Upload to claude.ai:
- **Settings → Skills**: upload the ZIP (Pro/Team/Enterprise with the Skills
  feature).
- **Project Knowledge**: drop the contents of `dist/qlik-talend-chat/` into a
  Project.

## Re-crawl

```bash
make crawl           # idempotent, ETag/hash cache saves bandwidth
make build           # rebuild topics + index
make chat-bundle     # optional: rebuild the chat ZIP
```

## Scope (MS1)

- Talend Studio 8.0 (User Guide + companion docs)
- Talend Management Console (Cloud)
- Remote Engine Linux + Windows (Cloud) + Gen2 + Dynamic Engine
- Installation Guide Linux/Windows (Cloud + 8.0), Hybrid, migration / upgrade
- SDLC / CI-CD best practices (8.0 + Cloud)
- Talend Cloud getting started + glossary

**Not included** (planned for later milestones): components reference, Data
Quality, Data Catalog, Data Stewardship, ESB, API Designer, MDM, 7.x.

## Architecture

```
crawler/       # discovery / fetch / extract / run / validate
distill/       # cluster (heuristic) / build_topics (mechanical) / validate_citations
package/       # build_index, build_chat_bundle
spike/         # MS0 discovery findings + extract spike
skill-output/  # build artefact → linked into ~/.claude/skills/ via cc-install
dist/          # chat distribution → ZIP for claude.ai upload
```

## Extending

To cover additional Talend products or other Qlik docs (Sense, QlikView):

1. Look up sub-sitemap names in `https://help.qlik.com/talend/sitemap.xml`
   (or `https://help.qlik.com/sitemap.xml`).
2. Add them to `PRODUCT_SITEMAPS` in `crawler/config.py`.
3. `make fresh`.

## Roadmap (post-MS1)

- LLM-based distillation as an additional topic layer (current build is
  purely mechanical — no hallucination risk, but lower token reduction)
- Re-crawl diff report (what changed between snapshots)
- Components reference as a separate sub-skill
- 7.x support in parallel (second version slot)
- Generalisation to Qlik Sense / QlikView / Replicate / Compose

## License

Code in this repository is licensed under [MIT](LICENSE).

### Note on crawled content

The MIT license covers **the source code only**. The crawler downloads
documentation from `help.qlik.com/talend`, which is owned by Qlik and
governed by Qlik's own terms of use. The crawled and distilled content is
**not** part of this repo and must be regenerated locally by each user via
`make fresh`. Users are responsible for complying with Qlik's terms of use
when running the crawler.

This project is **not** affiliated with or endorsed by Qlik.
