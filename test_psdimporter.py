#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *
from treetools.syn_importer import build_forest
from treetools.transformers import Transformer

# This is testing the parse method of the PSD importer.

importer = PennOutImporter()
importer.keyword_attr = 'keyword'
importer.word_lemma_regex = r'(?P<word>.*)@l=(?P<lemma>.*)$'
importer.keyword_node_regex = r'.* (?P<keyword_node>[0-9]+) V.*'
importer.dump_xml = '/home/tmr/tmp.xml'
cnc = importer.parse('/home/tmr/tmp.out')
exporter = TableExporter()
# exporter.tok_delimiter='\n'
# exporter.tok_fmt = "{0}_{0.tags[cat]}"
exporter.export(cnc, '/home/tmr/tmp.txt')