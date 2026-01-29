# SPDX-FileCopyrightText: UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from .. import tokens as to
from ..models import Badge
from ._base import register_badges

register_badges(
    {
        to.GITLAB_COVERAGE: Badge(
            name="gitlab-coverage-report",
            description="Show the most recent coverage score on the default branch.",
            example="https://gitlab.com/saferatday0/badgie/badges/main/coverage.svg",
            title="coverage report",
            link="{node.url}/-/commits/{node.ref}",
            image="{node.url}/badges/{node.ref}/coverage.svg",
            weight=1,
        ),
        to.GITLAB_PIPELINE: Badge(
            name="gitlab-pipeline-status",
            description="Show the most recent pipeline status on the default branch.",
            example="https://gitlab.com/saferatday0/badgie/badges/main/pipeline.svg",
            title="pipeline status",
            link="{node.url}/-/commits/{node.ref}",
            image="{node.url}/badges/{node.ref}/pipeline.svg",
            weight=0,
        ),
        to.GITLAB_RELEASE: Badge(
            name="gitlab-latest-release",
            description="Show the latest GitLab release by date.",
            example="https://gitlab.com/saferatday0/badgie/-/badges/release.svg",
            title="latest release",
            link="{node.url}/-/releases",
            image="{node.url}/-/badges/release.svg",
            weight=2,
        ),
    }
)
