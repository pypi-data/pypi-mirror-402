# Copyright (C) fregrem
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import argparse
from jinja2 import Environment, PackageLoader, select_autoescape

__version__ = "0.1.0"


def main():
    parser = argparse.ArgumentParser(
        prog="oasma",
        description="OpenAPI to single markdown file converter for in-tree documentation",
    )
    parser.add_argument("file", type=argparse.FileType("r"))
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s v{__version__}"
    )

    args = parser.parse_args()

    env = Environment(loader=PackageLoader("oasma"), autoescape=select_autoescape())
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.trim_newline = False

    def lower_boolean(value):
        if isinstance(value, bool):
            return str(value).lower()
        else:
            return value

    def rep_nl(value):
        if isinstance(value, str):
            return value.replace("\n", "<br/>")
        else:
            return value

    env.filters["lower_boolean"] = lower_boolean
    env.filters["rep_nl"] = rep_nl

    template = env.get_template("template.md.jinja")

    api = json.loads(args.file.read())

    print(template.render(api=api))
