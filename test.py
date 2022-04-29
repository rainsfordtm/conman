#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *

importer = BaseTreeImporter()
# importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
# importer.keywds_fields = ['word', 'lemma_dmf']
importer.keyword_attr = 'is_keyword'
cnc = importer.parse('/home/tmr/tmp.xml')
for hit in cnc:
    print(hit)
    print(hit.kws)
    for kw in hit.kws: print(kw.tags)
exporter = ConllExporter()
exporter.feats = ['relation']
# exporter.lemma = 'lemma_dmf'
exporter.export(cnc, '/home/tmr/tmp.conll')
    