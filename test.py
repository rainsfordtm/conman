#!/usr/bin/python3

from conman.importers import TXMImporter
from conman.exporters import ConllExporter

importer = TXMImporter()
importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
importer.keywds_fields = ['word', 'lemma_dmf']
cnc = importer.parse('/home/tmr/tmp.csv')
for hit in cnc:
    print(hit)
    print(hit.kws)
    for kw in hit.kws: print(kw.tags)
exporter = ConllExporter()
exporter.lemma = 'lemma_dmf'
exporter.export(cnc, '/home/tmr/tmp.conll')
    