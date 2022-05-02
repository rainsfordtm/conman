#!/usr/bin/python3

from conman.importers import *
from conman.exporters import *
from treetools.syn_importer import build_forest
from treetools.transformers import Transformer
from conman.scripts.pennout2cnc import script

# This is testing the parse method of the PSD importer.

# 1. Call syn_importer on the .out file. to create a BaseForest.
forest = build_forest('/home/tmr/tmp.out', 'penn-psd-out')
# 2. Initialize a transformer
transformer = treetools.transformers.Transformer()
# 3. Set the script method from self.script
transformer.script = conman.scripts.pennout2cnc.script
# 4. Transform the forest (in situ)
forest = transformer.transform(forest,
   keyword_attr = 'keyword',
   keyword_node_regex = r'.*\s+(?P<keyword_node>[0-9]+) V.*',
   word_lemma_regex = r'(?P<word>.*)@l=(?P<lemma>)$'
)
with open('/home/tmr/tmp.xml', 'w') as f:
    f.write(forest.toxml())
    
    