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
            try:
                tree.order_nodes(nodes)
            except:
                print(tree.trunk.toprettyxml())
                raise
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
    # Add KN_cat attribute
    tree.add_branch_attr('KN_cat')
    # Find keyword node numbers using keyword_node_regex
    for i, m in enumerate(re.finditer(keyword_node_regex, comment)):
        # Iterate over the named groups in groupdict()
        for key, value in m.groupdict().items():
            # Rename the key 'keyword_node' to keyword_attr
            if key == 'keyword_node':
                key = keyword_attr
            else:
                key = 'KEYNODE_' + key
            # Add the key attribute to the branch if this is the first
            # parse
            if i == 0: tree.add_branch_attr(key)
            # Find the node in the tree
            branches = tree.find_nodes('cs_id', value, regex=False)
            if not branches:
                transformer.script_error('Node {} not a branch id'.format(value))
            branch = branches[0]
            cat = branch.getAttribute('cat')
            # Set the attribute to str(i + 1) on the keyword branch
            branch.setAttribute(key, str(i + 1))
            branch.setAttribute('KN_cat', cat)
            # Get all descendents
            desc_branches = branch.getElementsByTagName('branch')
            for desc_branch in desc_branches:
                desc_branch.setAttribute(key, str(i + 1))
                desc_branch.setAttribute('KN_cat', cat)
            
    ###############################
    # 2. Remove all code nodes
    ###############################
    nodes = tree.find_nodes('cat', 'CODE', regex=False)
    while nodes:
        # An extremely rare annotation error causes CODE nodes
        # to be nested. This causes problems when a nested node is
        # deleted as a child of the higher node before the deletion
        # method is called.
        # So here we'll make sure that CODE nodes with <branch/>
        # children are only removed using del_node, not del_node_deep.
        node = nodes.pop(0)
        if tree.get_child_branches(node):
            tree.del_node(node)
        else:
            tree.del_node_deep(node)
    # Very occasionally, CODE nodes replace a terminal. One case of the code
    # "Latin Prayer omitted" which is tagged as NP-PRN. So make sure all
    # branches left without terminals are also deleted to prevent .sort()
    # failing below.
    tree.restructure(terminal_branches=False)
        
    ####################################################################
    # 3. Deal with the reference node
    # It's the final leaf in the tree
    # Updates the tree ID.
    # Then the node is deleted.
    #####################################################################
    try:
        tree.sort()
    except:
        print('When error occurs, tree looks like this:')
        print(tree.toprettyxml())
        raise
    node = tree.leaves[-1]
    old_id = tree.trunk.parentNode.getAttribute('id')
    new_id = node.getAttribute('value') + '|' + old_id
    tree.trunk.parentNode.setAttribute('id', new_id)
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
    
    #######################################################################
    # 5. Create ancestors and ancestors_cs_id attribute (records hierarchy)
    #######################################################################
    tree.add_leaf_attr('ancestors')
    tree.add_leaf_attr('ancestors_cs_id')
    for leaf in tree.leaves:
        l1, l2 = [], []
        node = leaf.parentNode.parentNode
        while node is not tree.trunk:
            l1.append(node.getAttribute('cat'))
            l2.append(node.getAttribute('cs_id'))
            node = node.parentNode
        l1.reverse()
        l2.reverse()
        leaf.setAttribute('ancestors', '|'.join(l1))
        leaf.setAttribute('ancestors_cs_id', '|'.join(l2))
        
    ############################################################################
    # 6. Create deep_ancestors and deep_ancestors_cs_id (records trace hierarchy
    ############################################################################
    tree.add_leaf_attr('deep_ancestors')
    tree.add_leaf_attr('deep_ancestors_cs_id')
    tree.add_leaf_attr('deep_ancestor_type')
    for leaf in tree.leaves:
        l1, l2, ds_types = [], [], []
        # Need to start at parent node: sometimes heads appear to be scrambled
        # without an IP. But we don't want to store this cat as an ancestor,
        # so set a flag to be cleared after the first non-contact pass.
        node = leaf.parentNode
        first_pass = True
        # Repeat the same iteration, but follow all contacts to build a
        # ds hierarchy.
        while node is not tree.trunk: 
            if len(ds_types) > 100:
                # This is necessary. Rare annotation errors can cause an *ICH*
                # trace to be embedded within itself. So these must be ignored
                # or we end up with infinite recursion.
                print('WARNING: Ignoring deep structure in tree {}: Infinite recursion.'.format(tree.get_id()))
                l1, l2, ds_types = [], [], []
                break
            contacts = tree.get_contacts(node)
            if contacts and contacts[0].getAttribute('type') != '=':
                # This is triggered if the node has contacts and the relationship
                # is not of Penn '=' type, which I'll assume is not relevant for
                # deep structure, since it indicates equivalency.
                target = tree.get_target(contacts[0])
                # target is a leaf; its value is the type of link
                ds_types.append(target.getAttribute('value'))
                node = target.parentNode # branching containing *T*, *ICH*
            elif first_pass:
                # Clear the "don't add this constituent" tag after the first
                # pass at which no contacts were found.
                first_pass = False
                node = node.parentNode
            else:
                # NOTE: it is CORRECT that no appending takes place if a 
                # contact is found. The Penn format decrees that the
                # constituent with the index has the same status as the 
                # constituent containing the trace or ICH, so to get a 
                # true deep hierarchy, in which immediate dominance is
                # correctly interpreted, it must be skipped.
                l1.append(node.getAttribute('cat'))
                l2.append(node.getAttribute('cs_id'))
                node = node.parentNode
        l1.reverse()
        l2.reverse()
        ds_types.reverse()
        # Only do anything with this if some kind of contact has been found,
        # i.e. ds_types has some values. Otherwise it's just the same as
        # the standard constituency hierarchy.
        if ds_types:
            leaf.setAttribute('deep_ancestors', '|'.join(l1))
            leaf.setAttribute('deep_ancestors_cs_id', '|'.join(l2))
            leaf.setAttribute('deep_ancestor_type', '|'.join(ds_types))
            
    ###################################################################
    # 7. Do some very basic head identification to preserve structure for CoNLL
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
    # 8. Use the word-lemma regex to split the tokens.
    ###################################################################
    for leaf in tree.leaves:
        m = re.match(word_lemma_regex, leaf.getAttribute('value'))
        if m:
            d = m.groupdict()
            for key in d:
                if key == 'word':
                    leaf.setAttribute('value', d['word'])
                else:
                    if not key in tree.leaf_attrs:
                        tree.add_leaf_attr(key)
                    if key not in ['order', 'relation', 'value', 'id']:
                        # can't update core tree attributes.
                        leaf.setAttribute(key, d[key])
    return tree
