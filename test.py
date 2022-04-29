#!/usr/bin/python3

from conman.importers import TXMImporter
from conman.exporters import ConllExporter

importer = BaseTreeImporter()
# importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
# importer.keywds_fields = ['word', 'lemma_dmf']
cnc = importer.parse('/home/tmr/Code/py3/treetools/samples/basetree.xml')
for hit in cnc:
    print(hit)
    print(hit.kws)
    for kw in hit.kws: print(kw.tags)
exporter = ConllExporter()
exporter.feats = ['relation']
# exporter.lemma = 'lemma_dmf'
exporter.export(cnc, '/home/tmr/tmp.conll')
    