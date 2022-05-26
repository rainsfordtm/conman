#!/usr/bin/python3

# This file contains the 'script' method for transforming a Penn .out file to
# a concordance. 
# It is passed to an instance of conman.importers.PennOutImporter and then
# to an instance of treetools.transformers.Transformer as the 'script' method
# before it can be run.
# 

def script(transformer, tree, 
    keyword_attr = 'KEYWORDS',
    keyword_node_regex = '',
    word_lemma_regex = '(?P<word>.*)'):
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
            nodes = tree.get_child_leaves(xjs[0])
            return nodes[0] if nodes else None
        else:
            nodes = ic.getElementsByTagName('leaf')
            tree.order_nodes(nodes)
            return nodes[0] if nodes else None
        
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
    # Add the keyword attr to all branches
    tree.add_branch_attr(keyword_attr)
    # Find keyword node numbers using keyword_node_regex
    for i, m in enumerate(re.finditer(keyword_node_regex, comment))
        keyword_node = m.groupdict()['keyword_node']
        # Find the keyword in the tree
        keyword_branch = tree.find_nodes('cs_id', keyword_node, regex=False)[0]
        # Set the attribute to str(i + 1) on the keyword branch
        keyword_branch.setAttribute(keyword_attr, str(i + 1))
        # Get all descendents
        branches = keyword_branch.getElementsByTagName('branch')
        for branch in branches:
            branch.setAttribute(keyword_attr, str(i + 1))
    
    ###############################
    # 2. Remove all code nodes
    ###############################
    nodes = tree.find_nodes('cat', 'CODE', regex=False)
    while nodes:
        tree.del_node_deep(nodes.pop(0))
    
    ####################################################################
    # 3. Deal with the reference node
    # It's the final leaf in the tree
    # Updates the tree ID.
    # Then the node is deleted.
    #####################################################################
    tree.sort()
    node = tree.leaves[-1]
    tree.trunk.parentNode.setAttribute('id', node.getAttribute('value'))
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
            head = get_head(ic)
            if head:
                leaf.setAttribute('conll_HEAD', str(head.getAttribute('order')))
            
    ###################################################################
    # 7. Use the word-lemma regex to split word from lemmas
    ###################################################################
    tree.add_leaf_attr('lemma')
    for leaf in tree.leaves:
        m = re.match(word_lemma_regex, leaf.getAttribute('value'))
        if m and 'lemma' in m.groupdict():
            leaf.setAttribute('lemma', m.groupdict()['lemma'])
        if m and 'word' in m.groupdict():
            leaf.setAttribute('value', m.groupdict()['word'])
     
    return tree
    
    
    
    
    