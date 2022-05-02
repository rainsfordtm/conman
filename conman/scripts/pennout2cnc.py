#!/usr/bin/python3

# This file contains the 'script' method for transforming a Penn .out file to
# a concordance. 
# It is passed to an instance of conman.importers.PennOutImporter and then
# to an instance of treetools.transformers.Transformer as the 'script' method
# before it can be run.
# 

def script(transformer, tree, keyword_attr = '', keyword_node_regex = ''):
    # Required positional arguments for ALL scripts are:
    # self: an instance of the treetools.transformer.Transformer class
    # tree: an instance of the treetools.basetree.BaseTree class.
    # The method must return tree.
    
    # Import libraries needed by this function. 
    import re
    
    # Functions used by this script
    
    def get_keynode_comment():
        nonlocal tree
        comment_branches = tree.find_nodes('comment', '.+', regex=True)
        if not comment_branches: return ''
        full_comment = comment_branches[0].getAttribute('comment')
        m = re.search(r'/\*([^/]+)\*/\s*$', full_comment)
        if not m: return ''
        return m.group(1).strip()
    
    # 1. Deal with the comment node
    # Get the comment
    comment = get_keynode_comment()
    # Find keyword node number using keyword_node_regex
    print(comment)
    m = re.match(keyword_node_regex, comment)
    keyword_node = m.groupdict()['keyword_node']
    print(keyword_node)
    print(type(keyword_node))
    # Add the keyword attr to all branches
    tree.add_branch_attr(keyword_attr)
    # Find the keyword in the tree
    keyword_branch = tree.find_nodes('cs_id', keyword_node, regex=False)[0]
    # Set the attribute to True
    keyword_branch.setAttribute(keyword_attr, 'True')
    
    return tree
    
    
    
    
    