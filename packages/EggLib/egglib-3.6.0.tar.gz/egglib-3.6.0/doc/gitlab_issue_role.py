"""
Role to insert a link to a GitLab issue.

cf. https://www.sphinx-doc.org/en/master/development/tutorials/extending_syntax.html
and: https://docutils.sourceforge.io/docs/howto/rst-roles.html
"""

from __future__ import annotations

import pathlib

from docutils import nodes, utils

from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util.typing import ExtensionMetadata

class GitLabIssueRole(SphinxRole):
    """A role to insert a link to an issue"""

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        ref = self.config.gitlab_base_url + self.text
        node = nodes.reference(self.text, f'#{self.text}', refuri=ref)
        return [node], []

def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value('gitlab_base_url', False, 'html', types=[str])
    app.add_role('issue', GitLabIssueRole())

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
