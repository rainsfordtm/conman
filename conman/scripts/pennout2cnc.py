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
        
    def get_head(ic):
        nonlocal tree
        is_ip = True if re.match('IP.*', ic.getAttribute('cat')) else False
        xjs = tree.find_child_nodes('cat', '.*J', ic, regex=True)
        if is_ip and xjs:
            return tree.get_child_leaves(xjs[0])[0]
        else:
            nodes = ic.getElementsByTagName('leaf')
            tree.order_nodes(nodes)
            return nodes[0]
        
    def is_head(leaf, ic):
        nonlocal tree
        # Returns True if leaf is the head of this constituent.
        # Convoluted expression finds all descendent leaves
        return True if leaf is get_head(ic) else False  
    
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
            leaf.setAttribute(attr, leaf.parentNode.getAttribute(attr))
    
    ####################################################################
    # 5. Create ancestors attribute (records hierarchy)
    ####################################################################
    tree.add_leaf_attr('ancestors')
    for leaf in tree.leaves:
        l = []
        node = leaf.parentNode.parentNode
        while node is not tree.trunk:
            l.append(node.getAttribute('cat'))
            node = node.parentNode
        l.reverse()
        leaf.setAttribute('ancestors', '|'.join(l))
            
    ###################################################################
    # 6. Do some very head identification to preserve structure for CoNLL
    # Uses the 'order' attribute, so will fail if leaves are removed
    # Head of an IP is the first leaf whose tag is .J, head of anything
    # else is the first word in the constituent.
    ###################################################################
    
    tree.add_leaf_attr('conll_HEAD')    
    for leaf in tree.leaves:
        ic = leaf.parentNode.parentNode
        while is_head(leaf, ic) and ic.parentNode is not tree.trunk:
            ic = ic.parentNode
        if is_head(leaf, ic):
            # Head is sentence root
            leaf.setAttribute('conll_HEAD', '0')
        else:
            leaf.setAttribute('conll_HEAD', str(get_head(ic).getAttribute('order')))
    
    return tree
    
    
    
    
    