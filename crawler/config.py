"""Crawler configuration: which Talend sitemaps to crawl.

Each entry maps a logical product group → list of sub-sitemap names (without
.xml suffix). The crawler resolves these against
`https://help.qlik.com/talend/sitemap_<name>_en-US.xml`.

Studio User Guide is special: its sitemap name embeds the R-code. We resolve
the latest R-code at runtime by inspecting the Talend sitemap-index.

Integrated documentation entry pages (one per sitemap below):

studio:
- https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R<latest>/
- https://help.qlik.com/talend/en-US/discovering-talend-studio/8.0/
- https://help.qlik.com/talend/en-US/creating-using-metadata-talend-studio/8.0/
- https://help.qlik.com/talend/en-US/using-context-variables-talend-studio/8.0/
- https://help.qlik.com/talend/en-US/studio-getting-started-guide-data-integration/8.0/
- https://help.qlik.com/talend/en-US/joining-two-data-sources-tmap-talend-studio/8.0/
- https://help.qlik.com/talend/en-US/reading-a-file-talend-studio/8.0/
- https://help.qlik.com/talend/en-US/sorting-a-file-talend-studio/8.0/
- https://help.qlik.com/talend/en-US/access-secure-services-with-studio-and-runtime/8.0/
- https://help.qlik.com/talend/en-US/studio-components-availability/8.0/

tmc:
- https://help.qlik.com/talend/en-US/management-console-user-guide/Cloud/
- https://help.qlik.com/talend/en-US/management-console-with-pipeline-designer/Cloud/
- https://help.qlik.com/talend/en-US/tmc-account-limits/Cloud/

remote-engine:
- https://help.qlik.com/talend/en-US/remote-engine-user-guide-linux/Cloud/
- https://help.qlik.com/talend/en-US/remote-engine-user-guide-windows/Cloud/
- https://help.qlik.com/talend/en-US/remote-engine-gen2-quick-start-guide/Cloud/
- https://help.qlik.com/talend/en-US/dynamic-engine-configuration-guide/Cloud/

installation:
- https://help.qlik.com/talend/en-US/installation-guide-linux/Cloud/
- https://help.qlik.com/talend/en-US/installation-guide-windows/Cloud/
- https://help.qlik.com/talend/en-US/installation-guide-linux/8.0/
- https://help.qlik.com/talend/en-US/installation-guide-windows/8.0/
- https://help.qlik.com/talend/en-US/hybrid-installation-guide-linux/Cloud/
- https://help.qlik.com/talend/en-US/hybrid-installation-guide-windows/Cloud/
- https://help.qlik.com/talend/en-US/migration-upgrade-guide/8.0/

sdlc-cicd:
- https://help.qlik.com/talend/en-US/software-dev-lifecycle-best-practices-guide/8.0/
- https://help.qlik.com/talend/en-US/development-operational-management/Cloud/

cloud-platform:
- https://help.qlik.com/talend/en-US/talend-cloud-getting-started/Cloud/
- https://help.qlik.com/talend/en-US/talend-glossary/Cloud/

api:
- https://help.qlik.com/talend/en-US/api-user-guide/Cloud/
- https://help.qlik.com/talend/en-US/api-designer-getting-started-guide/Cloud/
- https://help.qlik.com/talend/en-US/api-designer-user-guide/Cloud/
- https://help.qlik.com/talend/en-US/api-portal-deployment-guide/Cloud/
- https://help.qlik.com/talend/en-US/api-services-getting-started-guide-api-services-platform/Cloud/
- https://help.qlik.com/talend/en-US/api-tester-user-guide/Cloud/

esb:
- https://help.qlik.com/talend/en-US/esb-developer-guide/8.0/
- https://help.qlik.com/talend/en-US/esb-service-developer-guide/8.0/
- https://help.qlik.com/talend/en-US/esb-container-administration-guide/8.0/
- https://help.qlik.com/talend/en-US/esb-sts-user-guide/8.0/
- https://help.qlik.com/talend/en-US/esb-infra-services-configuration-guide/8.0/
- https://help.qlik.com/talend/en-US/esb-system-management/8.0/
- https://help.qlik.com/talend/en-US/esb-best-practices/8.0/
- https://help.qlik.com/talend/en-US/studio-getting-started-guide-esb/8.0/
- https://help.qlik.com/talend/en-US/esb-glossary/8.0/

To extend coverage with another guide:
1. Look up the sub-sitemap name in https://help.qlik.com/talend/sitemap.xml
   (filter for `_<latest-version>_en-US.xml`).
2. Add `<sitemap-name>_<version>` to the appropriate group below (or create
   a new group key).
3. Add a display label to GROUP_LABELS and a version string to GROUP_VERSIONS
   below (used by `package/update_meta.py` to regenerate README + SKILL.md).
4. Update the SKILL.md `description` frontmatter (the auto-trigger keywords
   for claude.ai) — this is the only thing NOT auto-generated.
5. Run `make fresh` (or just `make crawl && make build`).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Group metadata — used by package/update_meta.py to auto-regenerate
# README.md and SKILL.md after each build.
# Add an entry here whenever you add a new product group to PRODUCT_SITEMAPS.
# ---------------------------------------------------------------------------

# Short parenthetical label shown in README "Integrated documentation guides".
GROUP_LABELS: dict[str, str] = {
    "studio": "Talend Studio 8.0 — latest R-code at crawl",
    "tmc": "Talend Management Console, Cloud",
    "remote-engine": "Remote Engine + Dynamic Engine, Cloud",
    "installation": "Cloud + 8.0",
    "sdlc-cicd": "SDLC / CI-CD",
    "cloud-platform": "Talend Cloud platform basics",
    "api": "Talend Cloud APIs + API Designer / Portal / Services / Tester",
    "esb": "Talend ESB 8.0 — Camel routes, CXF services, Karaf container",
}

# Version string shown in the SKILL.md coverage table.
GROUP_VERSIONS: dict[str, str] = {
    "studio": "8.0 (latest R-code at crawl)",
    "tmc": "Cloud",
    "remote-engine": "Cloud",
    "installation": "Cloud + 8.0",
    "sdlc-cicd": "Cloud + 8.0",
    "cloud-platform": "Cloud",
    "api": "Cloud",
    "esb": "8.0",
}

USER_AGENT = "qlik-docs-skill-builder/0.1 (+https://github.com/mkcimt/claude-qlik-docs)"
LOCALE = "en-US"
TALEND_SITEMAP_INDEX = "https://help.qlik.com/talend/sitemap.xml"
SITEMAP_URL_TEMPLATE = "https://help.qlik.com/talend/sitemap_{name}_{locale}.xml"

# Conservative throttle (sequential, 1 req/s)
REQUEST_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 5

# Logical groups → static sitemap names (no R-codes here; Studio is dynamic).
# Any name containing the placeholder "<latest-r>" gets resolved against the
# sitemap-index for the most recent matching variant.
PRODUCT_SITEMAPS: dict[str, list[str]] = {
    "studio": [
        "studio-user-guide_<latest-r>",
        "discovering-talend-studio_8.0",
        "creating-using-metadata-talend-studio_8.0",
        "using-context-variables-talend-studio_8.0",
        "studio-getting-started-guide-data-integration_8.0",
        "joining-two-data-sources-tmap-talend-studio_8.0",
        "reading-a-file-talend-studio_8.0",
        "sorting-a-file-talend-studio_8.0",
        "access-secure-services-with-studio-and-runtime_8.0",
        "studio-components-availability_8.0",
    ],
    "tmc": [
        "management-console-user-guide_Cloud",
        "management-console-with-pipeline-designer_Cloud",
        "tmc-account-limits_Cloud",
    ],
    "remote-engine": [
        "remote-engine-user-guide-linux_Cloud",
        "remote-engine-user-guide-windows_Cloud",
        "remote-engine-gen2-quick-start-guide_Cloud",
        "dynamic-engine-configuration-guide_Cloud",
    ],
    "installation": [
        "installation-guide-linux_Cloud",
        "installation-guide-windows_Cloud",
        "installation-guide-linux_8.0",
        "installation-guide-windows_8.0",
        "hybrid-installation-guide-linux_Cloud",
        "hybrid-installation-guide-windows_Cloud",
        "migration-upgrade-guide_8.0",
    ],
    "sdlc-cicd": [
        "software-dev-lifecycle-best-practices-guide_8.0",
        "development-operational-management_Cloud",
    ],
    "cloud-platform": [
        "talend-cloud-getting-started_Cloud",
        "talend-glossary_Cloud",
    ],
    "api": [
        "api-user-guide_Cloud",
        "api-designer-getting-started-guide_Cloud",
        "api-designer-user-guide_Cloud",
        "api-portal-deployment-guide_Cloud",
        "api-services-getting-started-guide-api-services-platform_Cloud",
        "api-tester-user-guide_Cloud",
    ],
    "esb": [
        "esb-developer-guide_8.0",
        "esb-service-developer-guide_8.0",
        "esb-container-administration-guide_8.0",
        "esb-sts-user-guide_8.0",
        "esb-infra-services-configuration-guide_8.0",
        "esb-system-management_8.0",
        "esb-best-practices_8.0",
        "studio-getting-started-guide-esb_8.0",
        "esb-glossary_8.0",
    ],
}
