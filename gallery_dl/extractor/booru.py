# -*- coding: utf-8 -*-

# Copyright 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Base classes for extractors for danbooru and co"""

from .common import Extractor, Message
from .. import text
import xml.etree.ElementTree as ET
import json
import os.path
import urllib.parse

class BooruExtractor(Extractor):

    api_url = ""

    def __init__(self, match, info):
        Extractor.__init__(self)
        self.info = info
        self.tags = text.unquote(match.group(1))
        self.page = "page"
        self.params = {"tags": self.tags}
        self.headers = {}

    def items(self):
        yield Message.Version, 1
        yield Message.Directory, self.get_job_metadata()
        yield Message.Headers, self.headers
        for data in self.items_impl():
            try:
                yield Message.Url, self.get_file_url(data), self.get_file_metadata(data)
            except KeyError:
                continue

    def items_impl(self):
        pass

    def update_page(self, reset=False):
        """Update the value of the 'page' parameter"""
        # Override this method in derived classes if necessary.
        # It is usually enough to just adjust the 'page' attribute
        if reset is False:
            self.params[self.page] += 1
        else:
            self.params[self.page] = 1

    def get_job_metadata(self):
        """Collect metadata for extractor-job"""
        return {
            "category": self.info["category"],
            "tags": self.tags
        }

    def get_file_metadata(self, data):
        """Collect metadata for a downloadable file"""
        data["category"] = self.info["category"]
        data["filename"] = text.unquote(
            text.filename_from_url(self.get_file_url(data))
        )
        name, ext = os.path.splitext(data["filename"])
        data["name"] = name
        data["extension"] = ext[1:]
        return data

    def get_file_url(self, data):
        """Extract download-url from 'data'"""
        url = data["file_url"]
        if url.startswith("/"):
            url = urllib.parse.urljoin(self.api_url, url)
        return url


class JSONBooruExtractor(BooruExtractor):

    def items_impl(self):
        self.update_page(reset=True)
        while True:
            images = json.loads(
                self.request(self.api_url, verify=True, params=self.params,
                             headers=self.headers).text
            )
            if len(images) == 0:
                return
            for data in images:
                yield data
            self.update_page()


class XMLBooruExtractor(BooruExtractor):

    def items_impl(self):
        self.update_page(reset=True)
        while True:
            root = ET.fromstring(
                self.request(self.api_url, verify=True, params=self.params).text
            )
            if len(root) == 0:
                return
            for item in root:
                yield item.attrib
            self.update_page()
