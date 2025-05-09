#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
import dateparser
import feedparser
from github import gh
from loguru import logger
from videogram.utils import load_json
from videogram.utils import load_json, save_json


def main():
    if not Path(args.config).exists():
        return

    if args.platform == "youtube":
        check_youtube()
    elif args.platform == "bilibili":
        check_bilibili()
    else:
        raise NotImplementedError


def check_youtube():
    configs = load_json(args.config)
    for conf in configs:
        logger.info(f"Processing {conf['title']}")
        db_path = f"{args.metadata_dir}/{conf['name']}.json"
        database: list = load_json(db_path, default=[])  # type: ignore
        processed_vids = {x["vid"] for x in database}
        remote = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={conf['yt_channel']}")
        remote_vids = {x["yt_videoid"] for x in remote["entries"]}
        if remote_vids.issubset(processed_vids):
            logger.info(f"No new videos found for {conf['title']}")
            continue
        for x in remote["entries"]:
            if x["yt_videoid"] in processed_vids:
                continue
            logger.info(f"New video found: [{x['yt_videoid']}] {x['title']}")
            publish_time = dateparser.parse(x["published"], settings={"TO_TIMEZONE": os.getenv("TZ", "UTC")})
            database.insert(0, {"title": x["title"], "vid": x["yt_videoid"], "shorts": False, "time": f"{publish_time:%a, %d %b %Y %H:%M:%S %z}"})
        save_json(database, db_path)


def check_bilibili():
    configs = load_json(args.config)

    for conf in configs:
        logger.info(f"Processing {conf['title']}")
        db_path = f"{args.metadata_dir}/{conf['name']}.json"
        database: list = load_json(db_path, default=[])  # type: ignore
        processed_vids = {x["vid"] for x in database}
        remote = feedparser.parse(f"{os.getenv('RSSHUB_URL', 'https://rsshub.app')}/bilibili/user/video/{conf['uid']}")
        remote_vids = {Path(x["link"]).stem for x in remote["entries"]}
        if remote_vids.issubset(processed_vids):
            logger.info(f"No new videos found for {conf['title']}")
            continue
        for x in remote["entries"]:
            if Path(x["link"]).stem in processed_vids:
                continue
            logger.info(f"New video found: {x['title']}")
            publish_time = dateparser.parse(x["published"], settings={"TO_TIMEZONE": os.getenv("TZ", "UTC")})
            database.insert(0, {"title": x["title"], "vid": Path(x["link"]).stem, "time": f"{publish_time:%a, %d %b %Y %H:%M:%S %z}"})
        save_json(database, db_path)




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description="Sync YouTube to Telegram")
    parser.add_argument("--log-level", type=str, default="INFO", required=False, help="Log level")
    parser.add_argument("--metadata-dir", type=str, default="metadata", required=False, help="Path to metadata directory.")
    parser.add_argument("--config", type=str, default="config/youtube.json", required=False, help="Path to mapping json file.")
    parser.add_argument("--platform", type=str, default="youtube", required=False, help="Social media platform.")
    args = parser.parse_args()

    # loguru settings
    logger.remove()  # Remove default handler.
    logger.add(
        sys.stderr,
        colorize=True,
        level=args.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green>| <level>{level: <7}</level> | <cyan>{name: <10}</cyan>:<cyan>{function: ^30}</cyan>:<cyan>{line: >4}</cyan> - <level>{message}</level>",
    )
    main()
