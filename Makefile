.PHONY: help crawl cluster topics index validate build clean fresh test \
        cc-install cc-uninstall chat-bundle

SKILL_NAME := qlik-talend
SKILL_SRC := $(CURDIR)/skill-output/$(SKILL_NAME)
SKILL_DST := $(HOME)/.claude/skills/$(SKILL_NAME)
CHAT_BUNDLE_DIR := $(CURDIR)/dist/qlik-talend-chat
CHAT_BUNDLE_ZIP := $(CURDIR)/dist/qlik-talend-chat.zip

help:
	@echo "Build pipeline (run in order, or use 'make fresh'):"
	@echo "  make crawl         — full crawl from help.qlik.com (~30 min)"
	@echo "  make cluster       — cluster raw pages into topics"
	@echo "  make topics        — build distilled topic.md files"
	@echo "  make index         — build skill index + per-group sub-indexes"
	@echo "  make validate      — validate citations + crawl manifest"
	@echo "  make build         — cluster + topics + index + validate"
	@echo
	@echo "Distribution targets — pick the surface you need:"
	@echo "  make cc-install    — Claude Code: symlink skill into ~/.claude/skills/$(SKILL_NAME)"
	@echo "  make cc-uninstall  — Claude Code: remove symlink"
	@echo "  make chat-bundle   — Claude Chat (claude.ai): build dist/qlik-talend-chat.zip"
	@echo
	@echo "Convenience:"
	@echo "  make fresh         — wipe outputs, recrawl, rebuild, cc-install"
	@echo "  make clean         — wipe build artefacts (keeps raw mirror)"
	@echo "  make test          — run unit tests (no network, ~1s)"

crawl:
	uv run python -m crawler.run --delay 0.5

cluster:
	uv run python -m distill.cluster

topics:
	uv run python -m distill.build_topics

index:
	uv run python -m package.build_index

validate:
	uv run python -m crawler.validate
	uv run python -m distill.validate_citations

build: cluster topics index validate

test:
	uv run pytest -v

cc-install:
	@mkdir -p $(HOME)/.claude/skills
	@if [ -L "$(SKILL_DST)" ] || [ -e "$(SKILL_DST)" ]; then \
		echo "removing existing $(SKILL_DST)"; rm -f "$(SKILL_DST)"; \
	fi
	@ln -s "$(SKILL_SRC)" "$(SKILL_DST)"
	@echo "linked $(SKILL_DST) -> $(SKILL_SRC)"
	@ls -la "$(SKILL_DST)"

cc-uninstall:
	@if [ -L "$(SKILL_DST)" ]; then rm "$(SKILL_DST)"; echo "removed symlink $(SKILL_DST)"; \
	else echo "no symlink at $(SKILL_DST)"; fi

chat-bundle:
	uv run python -m package.build_chat_bundle
	@echo
	@echo "Upload to claude.ai:"
	@echo "  - As a Skill (Settings -> Skills): upload $(CHAT_BUNDLE_ZIP)"
	@echo "  - As Project Knowledge: drop the contents of $(CHAT_BUNDLE_DIR) into a Project"

clean:
	rm -rf $(SKILL_SRC)/topics $(SKILL_SRC)/index $(SKILL_SRC)/index.md
	rm -rf $(CHAT_BUNDLE_DIR) $(CHAT_BUNDLE_ZIP)
	rm -f topic_map.yaml

fresh:
	rm -rf $(SKILL_SRC)
	rm -f topic_map.yaml
	$(MAKE) crawl
	$(MAKE) build
	$(MAKE) cc-install
