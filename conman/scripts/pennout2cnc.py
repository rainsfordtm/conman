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
        # NOW REMOVE COMMENT ATTRIBUTE
        comment_branches[0].removeAttribute('comment')
        tree._refresh_lists()
        # DONE
        m = re.search(r'/\*([^/]+)\*/\s*$', full_comment)
        if not m: return ''
        return m.group(1).strip()
    
    ################################
    # 1. Deal with the comment node
    ################################
    # Get the comment
    comment = get_keynode_comment()
    # Find keyword node number using keyword_node_regex
    m = re.match(keyword_node_regex, comment)
    keyword_node = m.groupdict()['keyword_node']
    # Add the keyword attr to all branches
    tree.add_branch_attr(keyword_attr)
    # Find the keyword in the tree
    keyword_branch = tree.find_nodes('cs_id', keyword_node, regex=False)[0]
    # Set the attribute to True
    keyword_branch.setAttribute(keyword_attr, 'True')
    
    ###############################
    # 2. Remove all code nodes
    ###############################
    nodes = tree.find_nodes('cat', 'CODE', regex=False)
    while nodes:
        tree.del_node_deep(nodes.pop(0))
    
    ####################################################################
    # 3. Deal with the reference node
    # It's the final leaf in the tree
    # In order to save it for posterity, it is stored as transformer.ref
    # Then the node is deleted.
    #####################################################################
    tree.sort()
    node = tree.leaves[-1]
    transformer.ref = node.getAttribute('value')
    tree.del_node_deep(node.parentNode)
    
    ####################################################################
    # 4. Project all branch_attrs, except relation, on to the leaf.
    ####################################################################
    attrs = list(set(tree.branch_attrs) - set(tree.leaf_attrs) - set(['relation']))
    for attr in attrs:
        tree.add_leaf_attr(attr)
    for leaf in tree.leaves:
        for attr in attrs:
            leaf.setAttribute('attr', leaf.parentNode.getAttribute('attr'))
    
    
    
    
    
    return tree
    
    
    
    
    