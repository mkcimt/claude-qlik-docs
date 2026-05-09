"""MS1 crawler configuration: which Talend sitemaps to crawl.

Each entry maps a logical product name → list of sub-sitemap names (without
.xml suffix). The crawler resolves these against
`https://help.qlik.com/talend/sitemap_<name>_en-US.xml`.

Studio User Guide is special: its sitemap name embeds the R-code. We resolve
the latest R-code at runtime by inspecting the Talend sitemap-index.
"""
from __future__ import annotations

USER_AGENT = "qlik-docs-skill-builder/0.1 (personal use; +contact: mirco.kriesten@cimt-ag.de)"
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
}
