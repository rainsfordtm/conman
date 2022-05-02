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
cnc = importer.parse('/home/tmr/test-achim.out')
exporter = ConllExporter()
exporter.lemma = 'lemma'
exporter.cpostag = 'cat'
exporter.postag = 'cat'
exporter.deprel = 'cat'
exporter.feats.append('keyword')
exporter.export(cnc, '/home/tmr/tmp.conll')