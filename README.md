# claude-qlik-docs

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A pipeline that turns the public [Qlik Talend documentation](https://help.qlik.com/talend/)
into a token-efficient knowledge base for Claude. One source crawl, three
distribution targets — local Claude Code, claude.ai Skill, claude.ai Project
Knowledge — sharing the same distilled content but packaged for the
mechanics of each surface.

Why this exists: out-of-the-box, Claude either answers Talend questions from
stale model knowledge or requires you to attach the entire Qlik docs to
every prompt. This project produces a structured, versioned reference that
Claude pulls in progressively — typical Talend question costs **25–40 KB of
context**, not 14 MB.

## What it does, end to end

1. **Crawls** all relevant Talend sub-sitemaps (Studio 8.x, TMC, Remote Engine
   Linux/Windows, Dynamic Engine, installation, SDLC/CI-CD, Cloud platform)
   with `httpx + BeautifulSoup + markdownify`. Honours `robots.txt`,
   throttles, retries, hash-caches.
2. **Clusters and distils**: ~3,000 raw pages → ~440 topic clusters. Each
   topic gets a markdown file with TL;DR, procedure outline, notes /
   restrictions, and a citations table that maps every anchor exactly to
   its raw file and canonical URL. Distillation is **mechanical** — no LLM
   in the loop, so no hallucination risk.
3. **Builds three distribution artefacts** from the same distilled content:
   one for the Claude Code CLI, one for claude.ai as a Skill, one for
   claude.ai as Project Knowledge.

## The three distribution modes

All three are produced from the same source. Pick whichever fits your
workflow — you can also use several in parallel.

| Mode | Surface | Activation | Build target | Output |
|------|---------|------------|--------------|--------|
| **Claude Code skill** | Claude Code CLI | **Auto-triggered** by SKILL description | `make cc-install` | symlink `~/.claude/skills/qlik-talend` |
| **Chat Skill** | claude.ai (Settings → Skills) | **Slash command + auto-trigger** | `make chat-bundle` | `dist/qlik-talend-chat.zip` (~300 KB, 37 files) |
| **Project Knowledge** | claude.ai Projects | **Implicit** via Custom Instructions | `make project-bundle` | `dist/qlik-talend-project/` (~1.8 MB folder) |

### How each mode actually works

**Claude Code skill.** At session start the Claude Code harness scans
`~/.claude/skills/*/SKILL.md` and loads only name + description (~80 tokens
each) into the system prompt. The model decides per-turn whether the skill
is relevant; if it is, it reads the full SKILL.md and follows its routing
instructions. Detail look-ups go straight to the local raw markdown files.

**Chat Skill (claude.ai).** You upload the ZIP under Settings → Skills.
The skill then appears in the `/`-picker (mode label: *"Slash command +
auto"*), so it can be invoked **two ways**: explicitly via
`/qlik-talend`, or **auto-triggered** by Claude when the user's question
matches the SKILL description. The description in `SKILL.md` therefore
serves both as the slash-picker label and as the auto-trigger signal —
which is why it lists Talend keywords explicitly. There are no raw files
in the bundle; citations point at canonical URLs on `help.qlik.com/talend`,
and Claude `WebFetch`es them when verbatim text is needed.

**Project Knowledge.** You create a Project in claude.ai, paste the
generated `PROJECT-INSTRUCTIONS.md` into the Project's Custom Instructions
field, and upload the rest of the folder as Project Knowledge. From then
on, every chat in that Project has the Talend reference available
implicitly — no slash command. Like the Chat Skill, citations point at
URLs, and `WebFetch` is the path to verbatim text.

### Trade-offs side by side

| | Claude Code | Chat Skill | Project Knowledge |
|---|---|---|---|
| **Activation** | Implicit (description match) | `/qlik-talend` **or** auto-trigger via description | Implicit (Project Instructions) |
| **Onboarding cost** | One-time `make cc-install` | Upload ZIP per machine | Project setup per Project |
| **Verbatim-text fidelity** | Highest — local raw markdown always available | Good — `WebFetch` of canonical URL | Good — `WebFetch` of canonical URL |
| **Offline use** | Yes | No (URL fetches need network) | No |
| **Typical context per question** | ~25–40 KB | ~25–40 KB + occasional `WebFetch` | ~25–40 KB + Custom Instructions baseline (~3 KB) |
| **Persistent baseline cost** | ~80 tokens per session (description) | ~80 tokens in slash picker (only if Skills feature loaded) | Custom Instructions reload every chat in Project |
| **Cross-project / cross-team reuse** | Per-developer install | Once per workspace | Once per Project |
| **Update flow** | `make fresh && make cc-install` | `make chat-bundle` + re-upload | `make project-bundle` + re-upload |
| **Best for** | Daily local development | Ad-hoc Talend questions in Chat | Long-running Project where Talend is a recurring topic |

### Quality differences

The **distilled topic content is identical** across all three modes — same
TL;DRs, same procedure outlines, same notes, same citation anchors. The
only quality differential comes from the **detail look-up path**:

- **Claude Code** can open the raw `.md` file directly. Zero latency, no
  network, exact wording always available.
- **Chat Skill / Project Knowledge** must `WebFetch` the canonical URL when
  verbatim text is needed. This is correct as long as the Qlik page hasn't
  changed since the crawl — which is almost always true within a major
  version, but can drift between R-codes for Studio.

For all three modes, claims that the topic file already states
authoritatively (TL;DR, procedure outline, notes, version constraints) are
identical. The trade-off only shows up when you ask "give me the exact
parameter list for this component" — that's when local raw files vs.
WebFetch matters.

## Setup

```bash
# Prerequisites: macOS, Python 3.9+, uv (https://docs.astral.sh/uv/), make
brew install uv
git clone https://github.com/ElRakiti/claude-qlik-docs.git
cd claude-qlik-docs
uv sync                    # creates .venv, installs deps
make fresh                 # crawl (~30 min) + build + cc-install
```

`make fresh` runs the crawl, builds the distilled artefacts, and installs
the Claude Code skill in one go. If you only want one of the other modes,
build it separately:

```bash
make build           # crawl already done — just rebuild distilled artefacts
make chat-bundle     # → dist/qlik-talend-chat.zip
make project-bundle  # → dist/qlik-talend-project/
```

## Mode-specific instructions

### Claude Code

```bash
make cc-install      # symlink skill-output/qlik-talend → ~/.claude/skills/qlik-talend
make cc-uninstall    # remove the symlink
```

After install, open a **new** Claude Code session and just ask a Talend
question. The skill triggers automatically.

### Chat Skill (claude.ai)

```bash
make chat-bundle     # → dist/qlik-talend-chat.zip
```

In claude.ai: **Settings → Skills → Upload** and pick the ZIP. In any chat,
either type `/qlik-talend` to invoke it explicitly, or just ask a Talend
question — the skill description lets Claude auto-trigger it (mode label
in the Skills UI: *"Slash command + auto"*).

The bundle has no raw files (Chat has no filesystem) and consolidates
topics per guide+version into single files with anchored sections, to fit
under claude.ai's 200-file Skill-upload limit.

### Project Knowledge (claude.ai)

```bash
make project-bundle  # → dist/qlik-talend-project/  (folder, no ZIP)
```

1. Create a new Project in claude.ai.
2. Open `dist/qlik-talend-project/PROJECT-INSTRUCTIONS.md`, copy its
   contents, paste into the Project's **Custom Instructions** field.
3. Upload the rest of the folder (`index.md`, `index/`, `topics/`,
   `BUNDLE-INFO.txt`, `README-FOR-USER.md`) as Project Knowledge.

Every chat in that Project then has the Talend reference available without
any slash command.

## Tests

```bash
make test            # 44 unit tests, no network, ~1 s
```

Tests cover the pure transforms: URL parsing, HTML extraction (with a
title-bug regression test), topic clustering heuristics, citation
validation, chat-bundle topic transformer. Heuristic boundaries (regex
patterns, prefix lists, title cleanup) have regression tests so tuning
them later doesn't silently break existing behaviour.

## Re-crawl

```bash
make crawl           # idempotent; ETag/hash cache saves bandwidth
make build           # rebuild topics + index
make chat-bundle     # rebuild Chat ZIP if needed
make project-bundle  # rebuild Project folder if needed
```

## License / redistribution

The crawled Qlik content is **not** in this repo — it's `.gitignore`d. The
repo ships only **code and skill scaffolding** (e.g. `SKILL.md`,
`PROJECT-INSTRUCTIONS.md`). Each user crawls locally — comparable to a
`pip install`, not a content mirror.

## Scope (MS1, current)

In scope:

- Talend Studio 8.0 (User Guide + companion docs: getting started, metadata,
  context variables, secure services, components availability)
- Talend Management Console (Cloud) + companion docs
- Remote Engine Linux + Windows (Cloud) + Gen2 + Dynamic Engine
- Installation Guide Linux/Windows (Cloud + 8.0), Hybrid, migration / upgrade
- SDLC / CI-CD best practices (8.0 + Cloud)
- Talend Cloud getting started + glossary

Out of scope (MS1):

- Components reference, Data Quality, Data Catalog, Data Stewardship
- ESB, API Designer, MDM, Data Inventory, Data Preparation
- Talend 7.x

## Architecture

```
crawler/       # discovery / fetch / extract / run / validate
distill/       # cluster / build_topics / validate_citations
package/       # build_index, build_chat_bundle, build_project_bundle, _consolidate
spike/         # MS0 discovery findings + extract spike
tests/         # 44 unit tests on pure transforms
skill-output/  # build artefact → linked into ~/.claude/skills/ via cc-install
dist/          # claude.ai distribution → ZIP for Skill, folder for Project
```

## Extending

To cover additional Talend products or other Qlik docs (Sense, QlikView):

1. Look up sub-sitemap names in `https://help.qlik.com/talend/sitemap.xml`
   (or `https://help.qlik.com/sitemap.xml`).
2. Add them to `PRODUCT_SITEMAPS` in `crawler/config.py`.
3. `make fresh`.

## Roadmap / next milestones

Tracked here at a high level — concrete plans live in
`~/.claude/plans/ich-will-ein-tool-linear-sundae.md` (local, not in the
repo).

### MS2 — quality polish

- LLM-based distillation as an additional topic layer for sharper TL;DRs
  and better-structured procedure summaries (current build is purely
  mechanical — zero hallucination risk, but lower compression).
- Sharper procedure-outline extractor: skip the standard Qlik scaffolding
  headings (`Procedure`, `In this section`) and surface H4 / strong-text
  inside the body.
- Multi-line Note / Restriction extractor: current regex stops at the first
  newline, missing the second clause of two-sentence notes.

### MS3 — operations

- Re-crawl diff report: surface added / removed / changed pages between
  snapshots, with a per-topic delta digest.
- Optional CI workflow that crawls monthly and publishes a versioned
  bundle (Chat ZIP + Project folder) as a GitHub Release artefact, so
  team-mates can download a fresh build without running the crawler
  themselves.

### MS4 — coverage expansion

- Components reference (Studio components / connectors). Out of MS1 because
  it would multiply the page count by ~5×; deserves its own sub-skill.
- Talend 7.x as a parallel version slot in the same skill (frontmatter
  already supports it; just needs sitemap config + index split).
- Generalise the crawler to non-Talend Qlik docs (Qlik Sense, QlikView,
  Replicate, Compose). The pipeline is product-agnostic; only sitemap
  config and a few selectors would need to be revisited.

### MS5 — distribution

- Internal cimt distribution: monthly CI build pushed to a private artefact
  registry; team-mates `curl | tar xz` instead of running the crawler.
- Public Plugin Marketplace entry for the Claude Code skill (crawler-only,
  Qlik content regenerated locally per install).

## License

The code in this repository is licensed under [MIT](LICENSE).

### Note on crawled content

The MIT license covers **the source code only**. The crawler downloads
documentation from `help.qlik.com/talend`, which is owned by Qlik and
governed by Qlik's own terms of use. The crawled and distilled content is
**not** part of this repo and must be regenerated locally by each user via
`make fresh`. Users are responsible for complying with Qlik's terms of use
when running the crawler.

This project is **not** affiliated with or endorsed by Qlik.
