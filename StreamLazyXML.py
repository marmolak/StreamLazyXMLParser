
import lxml.etree as ET
import urllib3
urllib3.disable_warnings()
import os
import io
import sys
import copy
import tempfile
from pprint import pprint

class LocalParser(object):
    def __init__(self, file, elem_tag = 'SHOPITEM'):
        self.file = file
        self.codes = dict()
        self.elem_tag = elem_tag

    def elements(self):
        r = open(self.file)
        content = open(self.file)
        context = ET.iterparse(content, events=('end',), tag=self.elem_tag)
        for event, elem in context:
            yield copy.deepcopy(elem)
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        r.close()

class Parser(object):
    def __init__(self, url, elem_tag = 'SHOPITEM', local_cache = False):
        self.url = url
        self.codes = dict()
        self.elem_tag = elem_tag
        self.local_cache = local_cache
        self.content = None
        self._cached = False
        self.cache_name = None

    def cache(self):
        if self._cached:
            self.content.seek(0)
            return

        # support for local files
        if not self.url.startswith('http'):
            self.content = open(self.url)
            self._cached = True
            return

        http = urllib3.PoolManager()
        r = http.request('GET', self.url, preload_content=False)
        self.content = io.BufferedReader(r, 2048)
        if not self.local_cache:
            return

        fd, self.cache_name = tempfile.mkstemp()
        output = os.fdopen(fd, 'w+')
        output.write(self.content.read())
        output.flush()
        output.seek(0)
        self.content = output
        self._cached = True

    def elements(self):
        self.cache()
        context = ET.iterparse(self.content, events=('end',), tag=self.elem_tag)
        try:
            for event, elem in context:
                # return element
                yield copy.deepcopy(elem)
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
        except ValueError:
            # ok... we have some issues with EOF of stream
            pass

    def __del__(self):
        if not self.local_cache:
            return
        self.content.close()
        os.unlink(self.cache_name)
