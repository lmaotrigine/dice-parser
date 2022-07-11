from __future__ import annotations

from typing import Any

import sphinx
from docutils import nodes, utils
from docutils.nodes import Node, system_message
from docutils.parsers.rst.states import Inliner
from sphinx.application import Sphinx
from sphinx.util.nodes import split_explicit_title
from sphinx.util.typing import RoleFunction


def make_link_role(resource_links: dict[str, str]) -> RoleFunction:
    def role(
        typ: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Inliner,
        options: dict[Any, Any] | None = None,
        content: list[str] | None = None,
    ) -> tuple[list[Node], list[system_message]]:
        if options is None:
            options = {}
        if content is None:
            content = []
        has_explicit_title, title, key = split_explicit_title(utils.unescape(text))
        full_url = resource_links[key]
        if not has_explicit_title:
            title = full_url
        pnode = nodes.reference(title, title, internal=False, refuri=full_url)
        return [pnode], []

    return role


def add_link_role(app: Sphinx) -> None:
    app.add_role('resource', make_link_role(app.config.resource_links))


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value('resource_links', {}, 'env')
    app.connect('builder-inited', add_link_role)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
