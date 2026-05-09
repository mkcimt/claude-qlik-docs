.PHONY: help install uninstall crawl cluster topics index validate build all clean fresh

SKILL_NAME := qlik-talend
SKILL_SRC := $(CURDIR)/skill-output/$(SKILL_NAME)
SKILL_DST := $(HOME)/.claude/skills/$(SKILL_NAME)

help:
	@echo "Targets:"
	@echo "  make crawl     — full crawl from help.qlik.com (~30 min)"
	@echo "  make cluster   — cluster raw pages into topics"
	@echo "  make topics    — build distilled topic.md files"
	@echo "  make index     — build skill index + per-group sub-indexes"
	@echo "  make validate  — validate citations"
	@echo "  make build     — cluster + topics + index + validate"
	@echo "  make install   — symlink skill into ~/.claude/skills/$(SKILL_NAME)"
	@echo "  make uninstall — remove symlink"
	@echo "  make fresh     — wipe outputs, recrawl, rebuild, install"
	@echo "  make clean     — wipe build outputs (keeps raw mirror)"

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

install:
	@mkdir -p $(HOME)/.claude/skills
	@if [ -L "$(SKILL_DST)" ] || [ -e "$(SKILL_DST)" ]; then \
		echo "removing existing $(SKILL_DST)"; rm -f "$(SKILL_DST)"; \
	fi
	@ln -s "$(SKILL_SRC)" "$(SKILL_DST)"
	@echo "linked $(SKILL_DST) -> $(SKILL_SRC)"
	@ls -la "$(SKILL_DST)"

uninstall:
	@if [ -L "$(SKILL_DST)" ]; then rm "$(SKILL_DST)"; echo "removed symlink $(SKILL_DST)"; \
	else echo "no symlink at $(SKILL_DST)"; fi

clean:
	rm -rf $(SKILL_SRC)/topics $(SKILL_SRC)/index $(SKILL_SRC)/index.md
	rm -f topic_map.yaml

fresh:
	rm -rf $(SKILL_SRC)
	rm -f topic_map.yaml
	$(MAKE) crawl
	$(MAKE) build
	$(MAKE) install
