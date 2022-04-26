#!/usr/bin/python3

from lib.importers import TXMImporter

importer = TXMImporter()
importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
importer.keywds_fields = ['word', 'lemma_dmf']
cnc = importer.parse('/home/tmr/tmp.csv')
for hit in cnc:
    print(hit)
    print(hit.kw)
    for tok in hit[hit.kw[0]:hit.kw[1]]:
        print(tok)
        print(tok.tags)
    