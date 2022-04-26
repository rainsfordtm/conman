#!/usr/bin/python3

from lib.importers import TXMImporter

importer = TXMImporter()
importer.ref_regex = r'(?P<text>[^,]+), (?P<position>.*)'
cnc = importer.parse('tmp.csv')
print(cnc)