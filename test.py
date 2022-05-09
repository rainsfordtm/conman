#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *
from conman.mergers import *
from conman.concordance import load_concordance

importer = TableImporter()
# importer.dialect = 'tab'
# importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
# importer.keywds_regex = r'(?P<word>[^_]+)_(?P<lemma>[^_]+)_(?P<pos>[^_]+)'
other_cnc = importer.parse('/home/tomusr/in.csv')
cnc = load_concordance('/home/tomusr/tmp.cnc')
merger = ConcordanceMerger()
# merger.del_hits = True
merger.match_by = 'uuid'
merger.add_hits = True
merger.update_tags = False
cnc = merger.merge(cnc, other_cnc)
exporter = TableExporter()
exporter.fields.extend(['lang', 'text'])
exporter.export(cnc, '/home/tomusr/out2.csv')
# exporter.fields = ['REF', 'LCX', 'KEYWORDS', 'RCX', 'UUID'] 
for hit in other_cnc:
    print(hit)
    print(hit.tags)
    print(hit.ref)
    print(hit.kws)
    for kw in hit.kws: print(kw.tags)
for hit in cnc:
    print(hit)
    print(hit.tags)
    print(hit.ref)
    print(hit.kws)
    for kw in hit.kws: print(kw.tags)
    