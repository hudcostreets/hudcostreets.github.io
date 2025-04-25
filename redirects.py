#!/usr/bin/env python

from functools import partial
from os import makedirs
from os.path import join
from sys import stdout

from bs4 import BeautifulSoup
from click import command, option
import requests
import yaml
from requests import RequestException

REDIRECTS_YML_PATH = 'redirects.yml'
DEFAULT_OUT_DIR = 'out'

err = partial(print, file=stdout)


def parse_opengraph_meta(bs):
    """
    Parses Open Graph meta tags from a BeautifulSoup object.

    Args:
        bs (BeautifulSoup): The BeautifulSoup object representing the HTML.

    Returns:
        dict: A dictionary of Open Graph properties and their values, or an empty dict if no OG tags are found.
    """
    og_meta = {}
    for tag in bs.find_all('meta', property=lambda p: p and p.startswith('og:')):
        property_name = tag.get('property')
        content = tag.get('content')
        if property_name and content:
            og_meta[property_name] = content
    return og_meta


def generate_redirect_html(url, og_tags):
    """Generates the HTML content for a redirect page.

    Args:
        url (str): The URL to redirect to.
        og_tags (dict): A dictionary of Open Graph meta tags.

    Returns:
        str: The HTML content of the redirect page.
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0; url={url}">
"""
    for prop, content in og_tags.items():
        html += f'    <meta property="{prop}" content="{content}">\n'
    html += f"""</head>
<body><p>Redirecting to <a href="{url}">{url}</a>.</p></body>
</html>
"""
    return html


@command
@option('-o', '--out-dir', default=DEFAULT_OUT_DIR, help='Directory to write static site to')
def redirects(
    out_dir: str
):
    with open(REDIRECTS_YML_PATH, 'r') as f:
        redirects = yaml.safe_load(f)

    makedirs(out_dir, exist_ok=True)
    for src, dst in redirects.items():
        try:
            res = requests.get(dst)
        except RequestException as e:
            raise RuntimeError(f"Error fetching {dst}: {e}")

        bs = BeautifulSoup(res.text, features="html.parser")
        opengraph_meta_tags = parse_opengraph_meta(bs)
        name = src
        if not src.endswith('.html'):
            name += '.html'
        out_path = join(out_dir, name)
        with open(out_path, 'w') as f:
            f.write(generate_redirect_html(dst, opengraph_meta_tags))
            err(f"Wrote {out_path}: redirect to {dst}")


if __name__ == '__main__':
    redirects()
