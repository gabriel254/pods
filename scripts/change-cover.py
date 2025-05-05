#! /usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from github import gh
from utils import load_xml, save_xml

# for pod_type in ["audio", "video"]:
for pod_type in ["video"]:
    for xml in Path(pod_type).glob("*.xml"):
        data = load_xml(xml.as_posix())
        items = data["rss"]["channel"].get("item")
        if isinstance(items, dict):
            items = [items]
        cover = data["rss"]["channel"]["itunes:image"]
        data["rss"]["channel"]["itunes:image"] = f"https://101.34.68.162/pods/cover/{xml.stem}.jpg"
        save_xml(data, items, xml.as_posix())
        gh.upload_release(xml.as_posix(), pod_type, clean=False)
