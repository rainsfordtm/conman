#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *

importer = TableImporter()
importer.dialect = 'tab'
importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
importer.keywds_regex = r'(?P<word>[^_]+)_(?P<lemma>[^_]+)_(?P<pos>[^_]+)'
cnc = importer.parse('/home/tmr/tmp.csv')
for hit in cnc:
    print(hit)
    print(hit.tags)
    print(hit.ref)
    print(hit.kws)
    for kw in hit.kws: print(kw.tags)
    