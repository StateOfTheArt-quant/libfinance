# -*- coding: utf-8 -*-
"""English documentation tree. Shared settings live in ``docs/_shared/conf_base.py``."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "_shared"))

from conf_base import *  # noqa: F401,F403
from conf_base import project, version

language = "en"
html_title = f"{project} {version} Documentation"

html_context = dict(globals()["html_context"], doc_language="en")
