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

To extend coverage with another guide:
1. Look up the sub-sitemap name in https://help.qlik.com/talend/sitemap.xml
   (filter for `_<latest-version>_en-US.xml`).
2. Add `<sitemap-name>_<version>` to the appropriate group below.
3. Add the corresponding entry URL to the list above for documentation.
4. Run `make fresh` (or just `make crawl && make build` if the raw mirror
   is otherwise current — ETag/hash cache skips unchanged pages).
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
    "api": [
        "api-user-guide_Cloud",
    ],
}
