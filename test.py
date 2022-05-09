#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *
from conman.mergers import *
from conman.concordance import load_concordance

importer = Importer()
# importer.dialect = 'tab'
# importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
# importer.ignore_header = True
# importer.keywds_regex = r'(?P<word>[^_]+)_(?P<lemma>[^_]+)_(?P<pos>[^_]+)'
importer.lcx_regex = r'(?P<word>[^/]+)/(?P<lemma>.*)'
other_cnc = importer.parse('/home/tmr/in.txt', delimiter = r'\n')
# cnc.save('/home/tmr/tmp.cnc')
cnc = load_concordance('/home/tomusr/tmp.cnc')
tok_merger = TokenMerger()
cnc_merger = ConcordanceMerger()
cnc_merger.token_merger = tok_merger
# merger.del_hits = True
# merger.match_by = 'uuid'
# merger.add_hits = True
# merger.update_tags = False
cnc = merger.merge(cnc, other_cnc)
exporter = TableExporter()
exporter.tok_fmt = r'{0}_{0.tags[lemma]}'
exporter.export(cnc, '/home/tmr/out.csv')
# exporter.fields = ['REF', 'LCX', 'KEYWORDS', 'RCX', 'UUID'] 
# for hit in cnc:
#    print(hit)
#    print(hit.tags)
#    print(hit.ref)
#    print(hit.kws)
#    for kw in hit.kws: print(kw.tags)
    