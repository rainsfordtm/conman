#!/usr/bin/python3
# Builder for a BST file.
# Designed to work with text-based file formats that can't be treated with
# XSLT.

import argparse
import treetools.parsers
import os, sys
from treetools.basetree import BaseForest, BaseTree, StringTree

def main(in_file, out_file, format):
    """Writes the forest to file."""
    forest = build_forest(in_file, format)
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(forest.toxml())
    
def build_forest(in_file, format, encoding='utf-8', errors='replace'):
    
    #########################################################################
    # Subprocs for BUILD_FOREST                                             #
    #########################################################################
    def addlistnest(tree_id, listnest, contacts=[]):
        # First element of top-level list is read as trunk. This item
        # must be a list.
        # All dictionaries which contain a 'value' are read as leaves.
        # All dictionaries which contain 'children' are read as branches.
        # Order is taken to be the order in which tokens appear in the file.
        nonlocal forest
        
        ###################################################################
        # Subproc for addlistnest
        ###################################################################
        
        def writer(item):
            nonlocal id_count, order_count, t
            # The line below provokes KeyError if a listnest is malformed.
            d = item[0]
            if 'id' in d:
                an_id = d['id']
            else:
                an_id = 't{}_{}'.format(self.tree_id_counter, id_count)
                id_count += 1
            if 'value' in d:
                t += '<leaf id="{}" order="{}" relation="{}" value="{}"'.\
                format(
                    an_id, 
                    order_count, 
                    xmlent(d['relation']) if 'relation' in d else '--',
                    xmlent(d['value'])
                )
                order_count += 1
                for key in d:
                    if key not in ['id', 'order', 'relation', 'value']:
                        t += ' {}="{}"'.format(key, xmlent(d[key]))
                t += '/>\n'
            else:
                t += '<branch id="{}" relation="{}"'.format(
                    an_id,
                    xmlent(d['relation']) if 'relation' in d else '--'
                )
                for key in d:
                    if key not in ['id', 'relation']:
                        t += ' {}="{}"'.format(key, xmlent(d[key]))
                t += '>\n'
                cs = list(filter(lambda x: x['parent_id'] == an_id, contacts))
                for c in cs:
                    t += '<contact idref="{}" type="{}"/>\n'.format(
                        c['idref'],
                        xmlent(c['type']) if 'type' in c else '--'
                    )
                if len(item) > 1:
                    for item in item[1:]: writer(item)
                t += '</branch>\n'
                
        #####################################################################
        # addlistnest CODE                                                  #
        #####################################################################
                
        id_count = 1
        order_count = 1
        t = '<tree id="{}">\n'.format(tree_id)
        # Write the trunk
        t += '<trunk>\n'
        writer(listnest[0])
        t += '</trunk>\n'
        # Write the fallen leaves / branches
        if len(listnest) > 0:
            for item in listnest[1:]:
                writer(item)
        t += '</tree>'
        # Add the tree
        try:
            forest.append(t)
        except:
            print(t)
            raise
        
    def parse_func():
        nonlocal i, tree_id_counter, listnest, contacts, parser
        tree_id = 't_' + str(tree_id_counter + 1)
        try:
            listnest, contacts = parser.parse_tree(tree_id + '_')
        except:
            print('Parse failed while reading tree ending line {}.'.\
                format(i + 1))
            print('TREE:')
            print(parser.last_tree)
            raise
            
        # Print log messages from the parser
        if parser.log:
            print('Errors found in tree ending line {}:'.format(i + 1))
            print(parser.log)
            # Reset the parser's log
            parser.log = ''
            
        # Run addlistnest
        if listnest and listnest[0]:
            # Check it's not empty --- may occasionally happen with final tree
            # in syntax2
            try:
                addlistnest(tree_id, listnest, contacts)
            except:
                print('ListNest from tree ending line {} is malformed:'.\
                    format(i + 1)
                )
                print('LISTNEST')
                print(listnest)
                raise
    
    #########################################################################
    # MAIN CODE                                                             #
    #########################################################################
    # Check files:
    if not os.access(in_file, os.R_OK):
        print('Input file does not exist or cannot be read.')
        sys.exit()
    # if not os.access(out_file, os.W_OK):
        # print('Output file write permissions denied.')
        # sys.exit()
        
    # Create a new forest:
    forest = BaseForest()
    forest.name = os.path.splitext(os.path.basename(in_file))[0]
    
    if format == 'penn-psd':
        parser = treetools.parsers.PennPsd()
        forest.structure_rules = {
            'contacts': True, 
            'crossing_branches': False,
            'fallen_branches': True,
            'fallen_leaves': True,
            'knots': True,
            'max_leaves_per_branch': 1,
            'min_leaves_per_branch': 0,
            'terminal_branches': False
        }
    elif format == 'penn-psd-out':
        parser = treetools.parsers.PennPsdOut()
        forest.structure_rules = {
            'contacts': True, 
            'crossing_branches': False,
            'fallen_branches': True,
            'fallen_leaves': True,
            'knots': True,
            'max_leaves_per_branch': 1,
            'min_leaves_per_branch': 0,
            'terminal_branches': False
        }
    elif format == 'syntax2':
        parser = treetools.parsers.Syntax2()
        forest.structure_rules = {
            'contacts': True, 
            'crossing_branches': False,
            'fallen_branches': False,
            'fallen_leaves': False,
            'knots': True,
            'max_leaves_per_branch': 1,
            'min_leaves_per_branch': 0,
            'terminal_branches': False
        }
    else:
        print('No parser available.')
        sys.exit()
        
    # Feed parser the file line-by-line
    tree_id_counter = 0
    listnest = contacts = []
    with open(in_file, 'r', encoding=encoding, errors=errors) as f:
        for i, l in enumerate(f.readlines()):
            end_tree = parser.linereader(l)
            if end_tree:
                parse_func()
                tree_id_counter += 1
        # Tell parser it's EOF.
        end_tree = parser.eof()
        if end_tree: parse_func()
        
    print(parser.variant)
    return forest
        
def xmlent(s):
    s = s.replace('&', '&amp;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    s = s.replace("<", '&lt;')
    s = s.replace(">", '&gt;')
    return s
   
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = \
        'Parses a (probably text-based) corpus file and saves a basetree XML.'
        )
    parser.add_argument('infile', help='Input text file.')
    parser.add_argument('parser', choices=['penn-psd', 'penn-psd-out', 'syntax2'], 
        help='Parser to use for text file.'
    )
    parser.add_argument('-o', '--output', default='out.xml', 
        help='XML output file.'
    )
    # Convert Namespace to dict.
    args = vars(parser.parse_args())
    main(args.pop('infile'), args.pop('output'), args.pop('parser'))
