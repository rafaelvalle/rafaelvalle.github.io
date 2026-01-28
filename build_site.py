#!/usr/bin/env python3
"""
Build static index.html from JSON data files.

Usage:
    python build_site.py --data data.json
    python build_site.py --data data_prefetched.json

This script generates a static, SEO-friendly index.html by pre-rendering
publications from the specified JSON data file and site.json structure.
"""

import argparse
import json
import os
import html
from typing import Any, Dict, List


def load_json(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def highlight_author(authors: List[str], owner_name: str, color: str) -> str:
    """Highlight the owner's name in the author list."""
    result = []
    for author in authors:
        if owner_name in author:
            result.append(f'<strong style="color: {color};">{html.escape(author)}</strong>')
        else:
            result.append(html.escape(author))
    return ", ".join(result)


def create_media_html(media: Dict[str, Any], pub_id: str) -> str:
    """Create HTML for different media types."""
    if not media:
        return ""

    media_type = media.get("type", "")

    if media_type == "youtube":
        return f'<iframe width="186" height="104" src="{media["src"]}" title="Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'

    elif media_type == "image":
        return f'<img src="{media["src"]}" alt="{pub_id}" width="75%" style="border-style: none">'

    elif media_type == "image_audio":
        result = f'<img src="{media["image_src"]}" alt="{pub_id}" width="75%" style="border-style: none">'
        if media.get("audio_caption"):
            result += f'<br>"{html.escape(media["audio_caption"])}"<br>'
        else:
            result += "<br>"
        result += f'<audio controls preload="none" style="width: 200px; height: 30px"><source src="{media["audio_src"]}" type="audio/mpeg">audio not supported</audio>'
        return result

    elif media_type == "image_audio_multiple":
        result = f'<img src="{media["image_src"]}" alt="{pub_id}" width="75%" style="border-style: none"><br>'
        for sample in media.get("audio_samples", []):
            result += f'{html.escape(sample["label"])}<audio controls preload="none" style="width: 200px; height: 30px"><source src="{sample["src"]}" type="audio/mpeg">audio not supported</audio><br>'
        return result

    elif media_type == "image_youtube":
        return f'''<img src="{media["image_src"]}" alt="{pub_id}" width="75%" style="border-style: none">
                <iframe width="186" height="104" src="{media["youtube_src"]}" title="Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'''

    elif media_type == "soundcloud":
        return f'<iframe width="100%" height="300" scrolling="yes" frameborder="no" src="{media["src"]}"></iframe>'

    return ""


def create_links_html(links: Dict[str, str], pub_id: str) -> str:
    """Create HTML for publication links."""
    if not links:
        return ""

    link_parts = []
    if links.get("paper"):
        link_parts.append(f'<a target="_blank" href="{links["paper"]}">paper</a>')
    if links.get("arxiv"):
        link_parts.append(f'<a target="_blank" href="{links["arxiv"]}">arXiv</a>')
    if links.get("website"):
        link_parts.append(f'<a target="_blank" href="{links["website"]}">website</a>')
    if links.get("code"):
        link_parts.append(f'<a target="_blank" href="{links["code"]}">code</a>')
    if links.get("audio"):
        link_parts.append(f'<a target="_blank" href="{links["audio"]}">audio</a>')

    return " | ".join(link_parts)


def render_news(section: Dict[str, Any], publications: Dict[str, Any]) -> str:
    """Render the news section."""
    items = []
    for entry in section.get("entries", []):
        pub = publications.get(entry["id"], {})
        title_part = pub.get("title", entry["id"]).split(":")[0] if pub else entry["id"]

        news_text = f'<a href="#{entry["id"]}">{html.escape(title_part)}:</a> {entry["text"]}'
        if entry.get("suffix"):
            news_text += entry["suffix"]

        items.append(f"      <li>{news_text}</li>")

    return "\n".join(items)


def render_publication(pub_id: str, pub: Dict[str, Any], config: Dict[str, str], is_new: bool) -> str:
    """Render a single publication entry."""
    lower_id = pub_id.lower()

    # Determine the main link
    links = pub.get("links", {})
    website_link = links.get("website") or links.get("paper") or links.get("arxiv") or "#"

    # Media cell
    media_html = create_media_html(pub.get("media"), pub_id)

    # Build content
    new_badge = '<img src="images/new.png" alt="[NEW]" width="6%" style="border-style: none">' if is_new else ""

    authors_html = highlight_author(pub.get("authors", []), config["ownerName"], config["highlightColor"])

    venue_html = ""
    if pub.get("venue"):
        venue_html = f'<em>{html.escape(pub["venue"])}</em>'
        if pub.get("year"):
            venue_html += f' {pub["year"]}'
        venue_html += "<br>"

    # Links and abstract/bibtex
    links_html = create_links_html(links, pub_id)

    has_abstract = bool(pub.get("abstract"))
    has_bibtex = bool(pub.get("bibtex"))

    div_parts = []
    if links_html:
        div_parts.append(links_html)
    if has_abstract:
        div_parts.append(f"<a href=\"javascript:toggleblock('{lower_id}_abs')\">abstract</a>")
    if has_bibtex:
        div_parts.append(f"<a shape=\"rect\" href=\"javascript:togglebib('{lower_id}')\" class=\"togglebib\">bibtex</a>")

    div_content = " | ".join(div_parts)

    abstract_html = ""
    if has_abstract:
        abstract_html = f'<p align="justify"><i id="{lower_id}_abs">{html.escape(pub["abstract"])}</i></p>'

    bibtex_html = ""
    if has_bibtex:
        bibtex_html = f'<pre xml:space="preserve">{html.escape(pub["bibtex"])}</pre>'

    return f'''<tr>
    <td width="33%" valign="top" align="center">
      <a target="_blank" href="{website_link}">{media_html}</a>
    </td>
    <td width="67%" valign="top">
      <p>
        <a target="_blank" href="{website_link}" id="{pub_id}">{new_badge}<heading>{html.escape(pub.get("title", ""))}</heading></a><br>
        {authors_html}<br>
        {venue_html}
      </p>
      <div class="paper" id="{lower_id}">
        {div_content}
        {abstract_html}
        {bibtex_html}
      </div>
    </td>
  </tr>'''


def render_publications(section: Dict[str, Any], publications: Dict[str, Any], config: Dict[str, str], new_badge_ids: List[str]) -> str:
    """Render all publications."""
    rows = []
    for pub_id in section.get("entries", []):
        pub = publications.get(pub_id)
        if not pub:
            print(f"Warning: Publication not found: {pub_id}")
            continue

        is_new = pub_id in new_badge_ids
        rows.append(render_publication(pub_id, pub, config, is_new))

    return "\n".join(rows)


def build_html(data_file: str, site_file: str = "site.json") -> str:
    """Build the complete HTML page."""

    # Load data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data = load_json(os.path.join(script_dir, data_file))
    site = load_json(os.path.join(script_dir, site_file))

    publications = data.get("publications", {})
    config = site.get("config", {"ownerName": "Rafael Valle", "highlightColor": "deeppink"})
    new_badge_ids = site.get("newBadgeIds", [])

    # Render sections
    news_html = ""
    publications_html = ""

    for section in site.get("sections", []):
        if section["type"] == "news":
            news_html = render_news(section, publications)
        elif section["type"] == "publications":
            publications_html = render_publications(section, publications, config, new_badge_ids)

    # Build full HTML
    html_template = f'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>

<head>
  <meta charset="UTF-8">
  <meta name="generator" content="HTML Tidy for Linux/x86 (vers 11 February 2007), see www.w3.org">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/academicons/1.8.6/css/academicons.min.css" integrity="sha256-uFVgMKfistnJAfoCUQigIl+JfUaP47GrRKjf6CTPVmw=" crossorigin="anonymous">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.11.2/css/all.min.css" integrity="sha256-+N4/V/SbAFiW1MPBCXnfnP9QSN3+Keu+NlB+0ev/YKQ=" crossorigin="anonymous">

  <style type="text/css">
  /* Design Credits: Deepak Pathak, Jon Barron and Abhishek Kar and Saurabh Gupta*/
  a {{
  color: #1772d0;
  text-decoration:none;
  }}
  a:focus, a:hover {{
  color: #f09228;
  text-decoration:none;
  }}
  body,td,th {{
    font-family: 'Titillium Web', Verdana, Helvetica, sans-serif;
    font-size: 16px;
    font-weight: 400
  }}
  heading {{
    font-family: 'Titillium Web', Verdana, Helvetica, sans-serif;
    font-size: 19px;
    font-weight: 1000
  }}
  strong {{
    font-family: 'Titillium Web', Verdana, Helvetica, sans-serif;
    font-size: 16px;
    font-weight: 800
  }}
  strongred {{
    font-family: 'Titillium Web', Verdana, Helvetica, sans-serif;
    color: 'red' ;
    font-size: 16px
  }}
  sectionheading {{
    font-family: 'Titillium Web', Verdana, Helvetica, sans-serif;
    font-size: 22px;
    font-weight: 600
  }}
  </style>
  <link rel="icon" type="image/png" href="images/seal_icon.png">
  <script type="text/javascript" src="js/hidebib.js"></script>
  <title>Rafael Valle</title>
  <meta name="Rafael Valle's Homepage" http-equiv="Content-Type" content="Rafael Valle's Homepage">
  <link href='https://fonts.googleapis.com/css?family=Titillium+Web:400,600,400italic,600italic,300,300italic' rel='stylesheet' type='text/css'>
  <!-- Start : Google Analytics Code -->
  <script>
    (function(i,s,o,g,r,a,m){{i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){{
    (i[r].q=i[r].q||[]).push(arguments)}},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    }})(window,document,'script','//www.google-analytics.com/analytics.js','ga');
    ga('create', 'UA-99756592-1', 'auto');
    ga('send', 'pageview');
  </script>
  <!-- End : Google Analytics Code -->
  <!-- Scramble Script by Jeff Donahue -->
  <script src="js/scramble.js"></script>
</head>

<body>
<table width="840" border="0" align="center" border="0" cellspacing="0" cellpadding="20">
  <tr><td>

<table width="100%" align="center" border="0" cellspacing="0" cellpadding="20">
  <p align="center"><font size="7">Rafael Valle</font><br>
    <b>Email</b>:
    <font id="email" style="display:inline;">
      <noscript><i>Please enable Javascript to view</i></noscript>
    </font>
    <script>
    emailScramble = new scrambledString(document.getElementById('email'),
        'emailScramble', 'lfbkae@araeeeyvlled.lure',
        [5, 2, 12, 15, 7, 13, 11, 3, 14, 1, 4, 10, 16, 19, 6, 8, 17, 21, 22, 20, 9, 23, 0, 18]);
    </script>
  </p>

  <tr>
    <td width="67%" valign="middle" align="justify">
    <p>Prophet spreading visions of Superintelligence in Multimodal Generation
    and Understanding. My focus is on enabling multimodal intelligence that
    treats audio as a first-class modality rather than an afterthought.</p>

    <p>I currently work at Meta Superintelligence Labs (MSL), where I lead Audio
    Foundations—building the first audio capabilities (music, speech, and
    beyond) for Meta's frontier models and advising teams across the
    organization on audio understanding, generation, and editing.</p>

    <p>Previously, I worked as a polymath research scientist and manager at <a target="_blank" href="http://www.nvidia.com/">NVIDIA</a>,
    where I represented <a target="_blank" href="https://research.nvidia.com/labs/adlr/projects/">ADLR's</a>
    (Applied Deep Learning Research) audio team. ADLR&ndash;Audio focuses on
    generative models with intelligence in audio understanding and synthesis,
    with occasional explorations in vision.

    <p>I am passionate about generative modeling, machine perception and machine
    improvisation. Over the years, I have had the opportunity to collaborate
    with fantastic researchers and co-invent
    <a href="#FUGATTO">Fugatto</a>,
    <a href="#AUDIOFLAMINGO">Audio Flamingo</a>,
    <a href="#OMCAT">OMCAT</a>,
    <a href="#ETTA">ETTA</a>,
    <a href="#KOELTTS">Koel-TTS</a>,
    <a href="#PFLOW">P-Flow</a>,
    the <a href="#RADMMM">RAD*</a> family of models with the <a href="#OTA">One Aligner To Rule Them All</a>,
    <a href="#FLOWTRON">Flowtron</a> and
    <a href="#WAVEGLOW">WaveGlow</a>.<br>

    <p>During my PhD at <a target="_blank" href="http://www.berkeley.edu/">UC Berkeley</a> I was
    advised mainly by <a target="_blank"
        href="https://people.eecs.berkeley.edu/~sseshia/">Prof. Sanjit Seshia</a> and <a target="_blank"
        href="http://edmundcampion.com/">Prof. Edmund Campion</a> and my research
    focused on machine listening and improvisation. At <a target="_blank"
        href="http://www.berkeley.edu/">UC Berkeley</a>, I was part of the <a
        target="_blank" href="https://www.terraswarm.org/">TerraSwarm Research
        Center</a>, where I worked on problems related to <a target="_blank"
    href="https://blog.openai.com/adversarial-example-research/">adversarial
    attacks</a> and <a target="_blank" href="https://arxiv.org/abs/1606.08514">verified artificial intelligence.</a></p>

    <p>During Fall 2016 I was a Research Intern at <a target="_blank"
        href="http://www.gracenote.com/">Gracenote</a> in Emeryville, where I
    worked on audio classification using Deep Learning. Previously I was a
    Scientist Intern at <a target="_blank"
    href="http://www.pandora.com">Pandora</a> in Oakland, where I investigated
segments and scores that describe novelty seeking behavior in listeners.

    <p>Before coming to Berkeley, I completed a master's in Computer Music from <a target="_blank" href="https://www.hmdk-stuttgart.de">HMDK Stuttgart</a> in Germany and a bachelor's in Orchestral Conducting from <a target="_blank" href="http://www.ufrj.br">UFRJ</a> in Brazil.</p>

    </td>

    <td width="33%"><a target="_blank" href="images/rafael_valle.png"><img src="images/rafael_valle.png" width="90%"></a>
      <ul class="network-icon" aria-hidden="true" style="text-align: left; padding-left: 5;">
        <!-- <a href="valle_resume_info_en_nopic_smaller.pdf" target="_blank" rel="noopener"> <i class="ai ai-cv ai-2x big-icon" style="padding-right:5"></i> </a> --->
        <a href="https://twitter.com/rafaelvalleart" target="_blank" rel="noopener">
          <i class="fab fa-twitter fa-2x big-icon" style="padding-right:5"></i>
        </a>
        <a href="https://scholar.google.com/citations?user=SktxU8IAAAAJ&hl" target="_blank" rel="noopener">
          <i class="ai ai-google-scholar ai-2x big-icon" style="padding-right:5"></i>
        </a>
        <a href="https://www.linkedin.com/in/vallerafael" target="_blank" rel="noopener">
          <i class="fab fa-linkedin fa-2x big-icon" style="padding-right:5"></i>
        </a>
        <a href="https://github.com/rafaelvalle" target="_blank" rel="noopener">
          <i class="fab fa-github fa-2x big-icon"></i>
        </a>
      </ul>
    </td> </tr>
</table>

<!-- News Section -->
<table width="100%" align="center" border="0" cellspacing="0" cellpadding="20">
  <tr><td>
    <sectionheading>News</sectionheading>
    <ul>
{news_html}
    </ul>
  </td></tr>
</table>

<!-- Publications Section -->
<table width="100%" align="center" border="0" cellspacing="0" cellpadding="20">
  <tr><td><sectionheading>Publications</sectionheading></td></tr>
</table>
<table width="100%" align="center" border="0" cellspacing="0" cellpadding="20">
{publications_html}
</table>

<!-- Initialize hidebib -->
<script>
if (typeof hideallbibs === 'function') {{
  hideallbibs();
}}
document.querySelectorAll('[id$="_abs"]').forEach(el => {{
  if (typeof hideblock === 'function') {{
    hideblock(el.id);
  }}
}});
</script>

</td></tr>
</table>
</body>

</html>
'''

    return html_template


def main():
    parser = argparse.ArgumentParser(
        description="Build static index.html from JSON data files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python build_site.py --data data.json
    python build_site.py --data data_prefetched.json
    python build_site.py --data data.json --output index.html
        """
    )
    parser.add_argument(
        "--data",
        default="data.json",
        help="JSON file containing publication data (default: data.json)"
    )
    parser.add_argument(
        "--site",
        default="site.json",
        help="JSON file containing site structure (default: site.json)"
    )
    parser.add_argument(
        "--output",
        default="index.html",
        help="Output HTML file (default: index.html)"
    )

    args = parser.parse_args()

    print(f"Building site...")
    print(f"  Data file: {args.data}")
    print(f"  Site file: {args.site}")
    print(f"  Output: {args.output}")

    html_content = build_html(args.data, args.site)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, args.output)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nDone! Generated {args.output}")
    print(f"  - SEO-friendly static HTML with pre-rendered publications")
    print(f"  - All content is now crawlable by search engines")


if __name__ == "__main__":
    main()
