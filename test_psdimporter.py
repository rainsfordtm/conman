#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *

# This is testing the parse method of the PSD importer.

# Step 1. Select the importer you need and initizalize it
importer = PennOutImporter()
# Step 2. Set the attributes of the importer to customize its behaviour
importer.keyword_attr = 'keyword' # Tells importer what tag to use (internally) to mark a token as a keyword (TODO: Set 'keyword' as default)
importer.word_lemma_regex = r'(?P<word>.*)@l=(?P<lemma>.*)$' # Tells importer how to split words from lemmas 
importer.keyword_node_regex = r'.* (?P<keyword_node>[0-9]+) V.*' # Tells importer which number in the comment preceding the tree in the out file refers to the keyword_node.
importer.dump_xml = '/home/tmr/tmp.xml' # Tells the importer to dump the processed syntactic tree as an xml file (can be disabled)
# Step 3. Launch the importer to obtain the concordance object (cnc)
cnc = importer.parse('/home/tmr/tmp.out')
# Step 4. Select the exporter you need and initialize it
exporter = TableExporter()
# exporter.tok_fmt = "{0}_{0.tags[cat]}" # Tells the exporter how to print each non-keyword token using a Python format string. You can also set .kw_fmt for the keywords
# Step 5. Launch the exporter.
exporter.export(cnc, '/home/tmr/tmp.txt')
