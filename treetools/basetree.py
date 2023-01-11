#! /usr/bin/py
# Base Tree Class
# Dependencies:
# Python 3.1

import xml.dom.minidom
import xml.sax.handler
import xml.sax
import collections
import re, random, pickle

legal_relations = [ \
('tree', 'trunk'), \
('tree', 'leaf'), \
('tree', 'branch'), \
('tree', 'knot'), \
('tree', 'contact'), \
('trunk', 'leaf'), \
('trunk', 'branch'), \
('trunk', 'knot'), \
('trunk', 'contact'), \
('branch', 'leaf'), \
('branch', 'branch'), \
('branch', 'knot'), \
('branch', 'contact') \
]

# This is the default header for a BaseForest
default_forest_header = \
"""<forest name="default">
  <header />
  <structure crossing_branches="Y" fallen_leaves="Y" fallen_branches="Y" 
    terminal_branches="Y" knots="Y" contacts="Y" min_leaves_per_branch="0" 
    max_leaves_per_branch="unbounded"/>
</forest>
"""

# This is the minimal viable StringTree
default_tree_string = \
"""<tree id="default">
  <trunk/>
</tree>"""

class Error(Exception):
    """Errors in this class."""
    pass

class ValidationError(Error):
    """Error in validating the tree."""
    def __init__(self, msg, xmlstring=''):
        self.msg = msg
        self.xmlstring = xmlstring
        
    def __str__(self):
        return repr(self.msg)

class BuildError(Error):
    pass

class StructureError(Error):
    """Tree doesn't conform to corpus structure rules."""
    pass

class ModifyTreeError(Error):
    """Some tree modification has caused a problem."""
    pass

class StructureWarning(Error):
    """Tree modification has changed the tree's structural properties."""
    def __init__(self, msg, prop):
        self.msg = msg
        self.prop = prop
    def __str__(self):
        return repr(self.msg)
        
class NonUniqueIdError(Error):
    pass

class BaseForest(collections.UserList):
    
    def __init__(self, data=[]):
        
        # handler = BaseForestContentReader()
        # parser = xml.sax.parseString(default_forest_header.encode('utf-8'), handler)
        self.data = []
        self.extend(data)
        self.name = 'default'
        self.structure_rules = {
            'contacts': True, 
            'crossing_branches': True,
            'fallen_branches': True,
            'fallen_leaves': True,
            'knots': True,
            'max_leaves_per_branch': 9999,
            'min_leaves_per_branch': 0,
            'terminal_branches': True
        }
        self.the_map = ''
        
# Methods to validate all trees when data is ADDED to the forest.
    
    def __setitem__(self, i, item):
        try:
            self.data[i] = StringTree(item)
        except ValidationError as e:
            print(e.xmlstring)
            raise
        
    def __add__(self, other):
        try:
            l = [StringTree(item) for item in list(other)]
        except ValidationError as e:
            print(e.xmlstring)
            raise
        r = self.__class__(self.data + l)
        r.name = self.name
        r.structure_rules = self.structure_rules
        return r
            
    def __radd__(self, other):
        try:
            l = [StringTree(item) for item in list(other)]
        except ValidationError as e:
            print(e.xmlstring)
            raise
        r = self.__class__(l + self.data)
        r.name = self.name
        r.structure_rules = self.structure_rules
        return r
        
    def __iadd__(self, other):
        try:
            l = [StringTree(item) for item in list(other)]
        except ValidationError as e:
            print(e.xmlstring)
            raise
        self.data += l
        return self
    
    def append(self, item):
        try:
            StringTree(item)
        except ValidationError as e:
            print(e.xmlstring)
            raise
        self.data.append(StringTree(item))
        
    def insert(self, i, item):
        try:
            StringTree(item)
        except ValidationError as e:
            print(e.xmlstring)
            raise
        self.data.insert(i, StringTree(item))
        
    def extend(self, other):
        try:
            l = [StringTree(item) for item in list(other)]
        except ValidationError as e:
            print(e.xmlstring)
            raise
        self.data.extend(l)
        
# Non-list based methods.
        
    def validate(self, arg=None):
        if arg:
            try:
                self._validate(StringTree(arg))
            except ValidationError as e:
                print(e.xmlstring)
                raise
        else:
            ids = []
            for string_tree in self.data:
                try:
                    ids.append(string_tree.get_id())
                except AttributeError:
                    print('Weird...')
                    print("Can't find ID for tree:\n{}".format(string_tree))
                    raise
                self._validate(string_tree)
            if len(set(ids)) < len(ids):
                print(ids)
                raise StructureError('Forest contains duplicate tree IDs; see ' + \
                    'list above.')
                
    def _validate(self, string_tree):
        tree = string_tree.to_base_tree()
        for key in self.structure_rules:
            if key == 'knots':
                prop = 'has_knots'
            elif key == 'contacts':
                prop = 'has_contacts'
            else:
                prop = key
            try:
                val = eval('tree.' + prop + '()')
            except:
                print(prop)
                raise
            if val != self.structure_rules[key]:
                if (key == 'min_leaves_per_branch' and val < self.structure_rules[key]) \
                or (key == 'max_leaves_per_branch' and val > self.structure_rules[key]):
                    x = 'Tree {} has a branch with {} leaves; violates BaseForest rules.'.format( \
                    tree.documentElement.getAttribute('id'), str(val))
                    print(string_tree)
                    raise StructureError(x)
                if key not in ['min_leaves_per_branch', 'max_leaves_per_branch'] \
                and val == True and self.structure_rules[key] == False:
                    x = 'Tree {} has "{}"; violates BaseForest rules.'.format( \
                    tree.documentElement.getAttribute('id'), key)
                    print(string_tree)
                    raise StructureError(x)
        
    def toxml(self, decl=False, validate=True):
        """Serialize forest to basetree.xml"""
        # Pre-validation can be disabled, but this should only be used for debugging.
        if validate:
            self.validate()
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n' if decl else ''
        xml += '<forest name="{}">\n<header />\n{}<structure '.format(
            self.name, self.the_map
        )
        xml += ' '.join([key + '="' + \
        str(value).replace('True', 'Y').replace('False', 'N') + '"' \
        for key, value in self.structure_rules.items()])
        xml += '/>\n'
        xml += '\n'.join([str(tree) for tree in self])
        xml += '\n</forest>'
        return xml
        
    def to_leaf_dict(self, leaf_id_only=False):
        """Convert all trees to a dictionary of dictionaries."""
        d = {}
        if leaf_id_only and not self.unique_terminal_ids():
            raise NonUniqueIdError(
                'Cannot make terminals dictionary without tree ID prefix:' + \
                ' terminal IDs in this forest are not unique.'
            )
        for stree in self.data:
            tid = stree.get_id()
            id_prefix = tid + '#' if not leaf_id_only else ''
            tree = stree.to_base_tree()
            ts = tree.leaves
            ts.extend(tree.knots)
            for t in ts:
                x = []
                for attr in tree.leaf_attrs:
                    x.append((attr, t.getAttribute(attr)))
                d[id_prefix + t.getAttribute('id')] = dict(x)
        return d
        
    def to_id_value_list(self, leaf_id_only=False):
        """Converts a forest to a list of (id, value) tuples suitable for use
        with the aligner library.
        By default, tree id and leaf id are combined; this can be disabled
        with add_t_id=False."""
        
        regex_val = re.compile(
            r'<(leaf|knot)[^>]*\sid\s*=\s*"([^"]+)"[^>]*\svalue\s*=\s*"([^"]+)"', 
            re.MULTILINE
        )
        regex_ord = re.compile(
            r'<(leaf|knot)[^>]*\sid\s*=\s*"[^"]+"[^>]*\sorder\s*=\s*"([0-9]+)"', 
            re.MULTILINE
        )
        
        tid_regex = re.compile(r'<tree[^>]*\sid="([^"]+)"')
        
        tup_list = []
        for stree in self.data:
            l = []
            t_id = tid_regex.search(str(stree)).group(1)
            id_prefix = t_id + '#' if not leaf_id_only else ''
            m = regex_val.search(str(stree), 0)
            while m:
                m2 = regex_ord.search(str(stree), m.start())
                l.append([m2.group(2), (id_prefix + m.group(2), m.group(3))])
                m = regex_val.search(str(stree), m.end())
            l.sort(key=lambda x: int(x[0]))
            tup_list.extend([x[1] for x in l])
            
        return tup_list
        
    def build_map(self, remove_knots=False):
        """Creates the 'map' element of the BaseForest, based on XML code 
        contained in the knots of the tree. If remove_knots is true,
        simultaneously deletes the knots from the tree."""
        self.the_map = '<map>\n'
        for i, string_tree in enumerate(self.data):
            tree = string_tree.to_base_tree()
            t_id = string_tree.get_id()
            terminals = [l for l in tree.leaves]
            terminals.extend([k for k in tree.knots])
            terminals = tree.order_nodes(terminals)
            while terminals:
                t = terminals.pop(0)
                if t.tagName == 'leaf':
                    self.the_map += '<ptr target="#{}/{}"/>\n'.format(
                        t_id, t.getAttribute('id')
                    )
                else:
                    self.the_map += xmlent_resolve(
                        t.getAttribute('value') + '\n'
                    )
            if remove_knots:
                tree.del_nodes(tree.knots)
                new_string_tree = tree.to_string_tree()
                self.data[i] = new_string_tree
        self.the_map += '</map>\n'
        # Check that the map is well-formed XML (it may well not be...)
        # If not, don't include it in the file!
        handler = xml.sax.handler.ContentHandler()
        try:
            parser = xml.sax.parseString(self.the_map.encode('utf-8'), handler)
        except Exception as e:
            print('Map creation failed: Code in knots does not form valid XML.')
            with open('map', 'wb') as f:
                pickle.dump(self.the_map, f)
            self.the_map = ''
            
    def unique_terminal_ids(self, show_doublets=False):
        """Checks whether the terminal IDs in the forest are unique or not."""
        ids = [x[0] for x in self.to_id_value_list(leaf_id_only=True)]
        unique = list(set(ids))
        if show_doublets: 
            l = list(set([x for x in ids if ids.count(x) > 1]))
            print(l)
        return len(unique) == len(ids)

class StringTree(collections.UserString):
    
    def __init__(self, seq=default_tree_string):
        if isinstance(seq, str):
            self.data = seq
        else:
            self.data = str(seq)
        self.validate()

    def get_id(self):
        m = re.search(r'(?<=tree\sid=)"(.*?)"', self.data)
        if m.group(1):
            return m.group(1)
        else: 
            return ''
            
    def update_id(self, s):
        re.sub(r'(?<=tree\sid=")[^"]+', s, self.data)
            
    def validate(self):
        """Class-internal SAX-based validation of trees loaded from XML
        text file.
        If successful, returns the tree's unique ID.
        Otherwise, ValidationError will be raised."""
        handler = StringTreeContentHandler()
        try:
            parser = xml.sax.parseString(self.data.encode('utf-8'), handler)
        except ValidationError as e:
            with open('treedump', 'wb') as f:
                pickle.dump(self.data, f)
            raise
        except Exception:
            with open('treedump', 'wb') as f:
                pickle.dump(self.data, f)
            raise
            
    def to_base_tree(self):
        # Strip out all whitespace
        clean = re.sub(r'>\s+<', '><', self.data)
        # Empty document
        tree = BaseTree()
        # Parse the text_tree into a real DOM object
        dom = xml.dom.minidom.parseString(clean)
        # Copy the Doc element across to the BaseTree object
        tree.appendChild(dom.childNodes[0])
        tree._refresh_lists()
        return tree
        
    def large_flat_tree_splitter(self):
        # Splits a very large StringTree into trees of max. 1000 tokens.
        # This immeasurably improves the performance of most tools.
        # At the moment, it can only work on trees without branches.
        def ssearch():
            nonlocal count, leaves, m, last_ix
            # Start by searching only near last_ix
            m = re.search(
                '<(leaf|knot)[^>]*order="{}".*?(/>|</leaf>|</knot>)'.\
                format(count + 1), 
                self.data[last_ix:min(len(self.data), last_ix+1000)], re.DOTALL
            )
            
            if not m:
                # Search all self.data
                m = re.search(
                    '<(leaf|knot)[^>]*order="{}".*?(/>|</leaf>|</knot>)'.\
                    format(count + 1), self.data, re.DOTALL
                )
                
            if m:
                count += 1
                order_ix = m.group().find('order="') + 7
                x = count % 1000 or 1000
                leaves += m.group()[:order_ix] + str(x) + \
                m.group()[order_ix + len(str(count)):] + '\n'
                last_ix = m.end()
                
                
        if self.data.find('<branch') != -1:
            print('Tree contains branches; cannot split.')
            return [self]
            
        trees, leaves, m = [], '', None
        count = n = last_ix = 0
        m = 'something'
        while m:
            n += 1
            ssearch()
            print('Group {} thousand items'.format(n))
            while m and count % 1000 != 0: ssearch()
            trees.append(
                '<tree id="{}">\n<trunk>\n{}\n</trunk></tree>'.format(
                    self.get_id() + '_' + str(n), leaves
                )
            )
            leaves = ''
            
        return trees
    
class BaseTree(xml.dom.minidom.Document):

    def _refresh_lists(self):
        self.trunk = self.getElementsByTagName('trunk')[0]
        self.leaves = self.getElementsByTagName('leaf')
        self.knots = self.getElementsByTagName('knot')
        self.contacts = self.getElementsByTagName('contact')
        self.branches = self.getElementsByTagName('branch')
        nodes = self.leaves[:]
        nodes.extend(self.knots)
        self._orders = [int(x.getAttribute('order')) for x in nodes]
        nodes.extend(self.branches[:])
        self.ids = set([x.getAttribute('id') for x in nodes])
        try:
            self.branch_attrs = [self.branches[0].attributes.item(i).nodeName 
            for i in list(range(self.branches[0].attributes.length))]
        except IndexError:
            # No branches
            self.branch_attrs = ['id', 'relation']
        try:
            self.leaf_attrs = [self.leaves[0].attributes.item(i).nodeName
            for i in list(range(self.leaves[0].attributes.length))]
        except IndexError:
            # No leaves
            self.leaf_attrs = ['id', 'value', 'order', 'relation']
        
    def leafless_branches(self):
        for branch in self.branches:
            if not self.get_child_leaves(branch):
                return True
        return False
        
    def get_child_leaves(self, structure):
        l = []
        for child_node in structure.childNodes:
            if child_node.localName in ['leaf', 'knot']:
                l.append(child_node)
        return l
        
    def get_child_branches(self, structure):
        l = []
        for child_node in structure.childNodes:
            if child_node.localName == 'branch':
                l.append(child_node)
        return l
        
    def get_child_structures(self, structure):
        l = []
        for child_node in structure.childNodes:
            if child_node.localName in ['branch', 'leaf', 'knot']:
                l.append(child_node)
        return l
        
    def get_contacts(self, structure):
        l = []
        for child_node in structure.childNodes:
            if child_node.localName == 'contact':
                l.append(child_node)
        return l
        
    def get_id(self):
        return self.trunk.parentNode.getAttribute('id')
        
    def fallen_leaves(self):
        return True if self.get_child_leaves(self) else False 
        
    def fallen_branches(self):
        return True if self.get_child_branches(self) else False
        
    def terminal_branches(self):
        for branch in self.branches:
            if not self.get_child_structures(branch):
                return True
        return False
        
    def has_knots(self):
        return True if self.knots else False
        
    def has_contacts(self):
        return True if self.contacts else False
        
    def crossing_branches(self, track=False):
        for branch in self.branches:
            if self._is_discontinuous(branch, track): return True
        return False
        
    def _is_discontinuous(self, node, track=False):
        terminals = node.getElementsByTagName('leaf')
        terminals.extend(node.getElementsByTagName('knot'))
        orders = [int(terminal.getAttribute('order')) for terminal in terminals]
        orders.sort()
        if orders and orders != list(range(orders[0], orders[-1] + 1)):
            if track: print(orders, branch.getAttribute('id'))
            return True
        
    def min_leaves_per_branch(self):
        n = 9999
        for branch in self.branches:
            i = 0
            for child_node in branch.childNodes:
                i += 1 if child_node.localName in ['leaf', 'knot'] else 0
            n = min(n, i)
        return n
        
    def max_leaves_per_branch(self):
        n = 0
        for branch in self.branches:
            i = 0
            for child_node in branch.childNodes:
                i += 1 if child_node.localName in ['leaf', 'knot'] else 0
            n = max(n, i)
        return n
        
    def make_id(self, prefix = '', length = 4):
        """Returns a random number of x characters not given in ID."""
        import random
        random.seed()
        while True:
            newId = prefix + str(random.randint(0, 10 ** length))
            if newId not in self.ids:
                return newId
                
    def update_id(self, node, new_id):
        """Changes the ID on a specified node, including all idrefs."""
        if node.localName not in ['branch', 'leaf', 'knot']:
            raise ModifyTreeError('Node type "{}" has no ID'.format(node.localName))
        if new_id in self.ids:
            raise ModifyTreeError('ID "{}" already in use.'.format(new_id))
        old_id = node.getAttribute('id')
        node.setAttribute('id', new_id)
        for contact in self.contacts:
            if contact.getAttribute('idref') == old_id:
                contact.setAttribute('idref', new_id)
        self._refresh_lists()
        
    def find_nodes(self, key, value, ancestor = None, regex=True):
        """Returns a list of nodes with attribute 'key' = 'value'.
        The 'ancestor' property permits specification of a common ancestor.
        The 'regex' property enables regex matching of value. """
        import re
        if not ancestor:
            ancestor = self
        if not isinstance(value, str):
            try:
                value = str(value)
            except:
                raise TypeError('"value" must be a string')
        if regex:
            return list(filter(lambda x: re.match(value, x.getAttribute(key)), \
            ancestor.getElementsByTagName('*')))
        else:
            return list(filter(lambda x: x.getAttribute(key) == value, \
            ancestor.getElementsByTagName('*')))
        
    def find_child_nodes(self, key, value, parent, regex=True):
        """Returns a list of child nodes with attribute 'key' = 'value'.
        The 'parent' property permits specification of the parent.
        The 'regex' property enables regex matching of value. """
        import re
        l = []
        if not isinstance(value, str):
            try:
                value = str(value)
            except:
                raise TypeError('"value" must be a string')
        for child_node in parent.childNodes:
            if child_node.localName in ['leaf', 'knot', 'branch', 'contact']:
                if child_node.getAttribute(key) == value or \
                (regex and re.match(value, child_node.getAttribute(key))):
                    l.append(child_node)
        return l
        
    def new_leaf(self, iid = '', value = '--', ignore_warnings = True):
        """Appends a new leaf element to the trunk."""
        return self._new_terminal('leaf', iid=iid, value=value, \
        ignore_warnings = ignore_warnings)
        
    def new_knot(self, iid = '', value = '--', ignore_warnings = True):
        """Appends a new knot element to the trunk."""
        return self._new_terminal('knot', iid=iid, value=value, \
        ignore_warnings = ignore_warnings)
        
    def _new_terminal(self, t_type, iid = '', value = '--', ignore_warnings = True):
        """Appends a new leaf or knot element to the trunk."""
        if iid and iid in self.ids:
            raise ModifyTreeError('ID "{}" already in use.'.format(iid))
        if not iid:
            iid = self.make_id()
        order = len(self._orders) + 1
        attrs = dict([(key, '--') for key in self.leaf_attrs])
        attrs['id'], attrs['value'], attrs['order'] = iid, value, str(order)
        new_node = self._new_node(t_type, attrs)
        # Add node to the trunk
        self.trunk.appendChild(new_node)
        # Update lists
        self._refresh_lists()
        return new_node
        
    def new_branch(self, iid='', child_nodes = [], ignore_warnings = True):
        """Adds a new branch element to the tree."""
        if iid and iid in self.ids:
            raise ModifyTreeError('ID "{}" already in use.'.format(iid))
        if not iid:
            iid = self.make_id()
        if not child_nodes and not self.terminal_branches and not ignore_warnings:
            raise StructureWarning('Creating first terminal_branch.', \
            'terminal_branches')
        attrs = dict([(key, '--') for key in self.branch_attrs])
        attrs['id'] = iid
        new_node = self._new_node('branch', attrs)
        # Add node to the trunk
        self.trunk.appendChild(new_node)
        # Update lists
        self._refresh_lists()
        # Copy child nodes across
        # COMMON ERROR: pass a node not a node list, if only one child node
        # Correct this.
        if child_nodes:
            if type(child_nodes) == xml.dom.minidom.Element:
                child_nodes = [child_nodes]
            for child_node in child_nodes:
                new_node.appendChild(child_node)
        return new_node
        
    def new_contact(self, from_node, to_node):
        """Adds a new contact element to the tree between parent and child
        node."""
        if from_node.localName != 'branch' or \
        to_node.localName not in ['branch', 'leaf', 'knot']:
            raise ModifyTreeError(
            'Cannot put a contact from a {} to a {}.'.
            format(from_node.localName, to_node.localName)
            )
        new_node = self._new_node('contact', \
        {'idref': to_node.getAttribute('id'), 'type': '--'})
        from_node.appendChild(new_node)
        return new_node
        
    def _new_node(self, tag, attrib={}):
        """Creates a new element node, does not place it in the tree."""
        new_node = self.createElement(tag)
        for key, value in attrib.items():
            if not isinstance(value, str):
                raise ModifyTreeError( \
                'Value for attribute "{}" must be of type "str"'.format(key))
            new_node.setAttribute(key, value)
        return new_node
        
    def move_node(self, node, new_parent):
        """SHALLOW moves a node to be the last child of new_parent."""
        self._move_validate(node, new_parent)
        for child_structure in self.get_child_structures(node):
            self._move_validate(child_structure, node.parentNode)
            
        # move the node
        for child_node in self.get_child_structures(node):
            node.parentNode.appendChild(child_node)
        # contacts, whitespace copied with the node
        new_node = new_parent.appendChild(node)
        
        return new_node
        
    def move_node_deep(self, node, new_parent):
        """DEEP moves a node to be the last child of new_parent."""

        self._move_validate(node, new_parent)
        
        # move the node
        #print('Appending child with child nodes: {}'.format(repr(node.childNodes)))
        new_node = new_parent.appendChild(node)
        #print('Nodes new childNodes: {}'.format(repr(node.childNodes)))
        #print('new_node childNodes: {}'.format(repr(new_node.childNodes)))
        return new_node

    def _move_validate(self, node, new_parent):
        # First a well-formedness check.
        if (new_parent.localName, node.localName) not in legal_relations:
            raise ModifyTreeError('A {} cannot be the child of a {}.'.format( \
            node.localName, new_parent.localName))
        if node == new_parent:
            raise ModifyTreeError('A node cannot be its own parent.')
        return
        # Next, raise forest structure warnings.
#        if new_parent == self.tree:
#           # if node.localName == 'branch' and not self.fallen_branches:
#                # raise StructureWarning('Creating first fallen branch.', \
#                # 'fallen_branches')
#        if node.localName in ['leaf', 'knot'] and not self.fallen_leaves:
#            raise StructureWarning('Creating first fallen leaf.', \
#            'fallen_leaves')
#        if not crossing_branches and node.localName in ['leaf', 'knot']:
#            terminals = node.parentNode.getElementsByTagName('leaf')
#            terminals.extend(node.parentNode.getElementsByTagName('knot'))
#            orders = [int(node.getAttribute('order')) for node in terminals]
#            orders.append(int(node.getAttribute('order')))
#            orders.sort()
#            if orders != list(range(orders[0], orders[-1] + 1)):
#                raise StructureWarning('Creating first discontinuous branch.',
#                'crossing_branches')

    def del_node(self, node):
        """Shallow deletes a node."""
        if not node.localName in ['branch', 'leaf', 'knot']:
            raise ModifyTreeError('del_node cannot delete element "{}"'.format(node.localName))
        for child_node in self.get_child_structures(node):
            self._move_validate(child_node, node.parentNode)
        # copy the children
        for child_node in self.get_child_structures(node):
            node.parentNode.appendChild(child_node)
            
        # remove the node
        self._del_node(node)
        return None
        
    def del_node_deep(self, node):
        """Deep deletes a node."""
        if not node.localName in ['branch', 'leaf', 'knot']:
            raise ModifyTreeError('del_node cannot delete element "{}"'.format(node.localName))
            
        terminals = node.getElementsByTagName('leaf')
        terminals.extend(node.getElementsByTagName('knot'))
        for leaf in terminals:
            self._del_node(leaf)
        # remove the node
        self._del_node(node)
        return None
        
    def del_contact(self, contact):
        if not contact.localName == 'contact':
            raise ModifyTreeError('del_contact cannot delete element "{}"'.format(contact.localName))
        contact.parentNode.removeChild(contact)
        contact.unlink()
        self._refresh_lists()
        return None
        
    def _del_node(self, node):
        if node.localName in ['leaf', 'knot']:
            for leaf in self.leaves:
                if int(leaf.getAttribute('order')) > int(node.getAttribute('order')):
                    leaf.setAttribute('order', str(int(leaf.getAttribute('order')) - 1))
                    
            for knot in self.knots:
                if int(knot.getAttribute('order')) > int(node.getAttribute('order')):
                    knot.setAttribute('order', str(int(knot.getAttribute('order')) - 1))
                    
        for contact in self.contacts:
            if contact.getAttribute('idref') == node.getAttribute('id'):
                contact.parentNode.removeChild(contact)
                contact.unlink()
        node.parentNode.removeChild(node)
        node.unlink()
        self._refresh_lists()
        
    def del_nodes(self, nodes):
        """Shallow deletes multiple nodes in a tree."""
        orders = []
        for node in nodes:
            if not node.localName in ['branch', 'leaf', 'knot']:
                raise ModifyTreeError('del_node cannot delete element "{}"'.format(node.localName))
            for child_node in self.get_child_structures(node):
                self._move_validate(child_node, node.parentNode)
            # copy the children
            for child_node in self.get_child_structures(node):
                node.parentNode.appendChild(child_node)
        self._del_nodes(nodes)
        return None
         
    def _del_nodes(self, nodes):
        lost_orders = []
        lost_ids = []
        for node in nodes:
            if node.localName in ['leaf', 'knot']:
                lost_orders.append(int(node.getAttribute('order')))
            lost_ids.append(node.getAttribute('id'))
            
            node.parentNode.removeChild(node)
            node.unlink()
        
        lost_orders.sort()
        self._refresh_lists()
        for l in [self.leaves, self.knots]:
            for term in l:
                order = int(term.getAttribute('order'))
                i = 0
                while i < len(lost_orders) and lost_orders[i] < order:
                    i += 1
                term.setAttribute('order', str(order - i))
        
        for contact in self.contacts:
            if contact.getAttribute('idref') in lost_ids:
                contact.parentNode.removeChild(contact)
                contact.unlink()
        self._refresh_lists()
        
    def shuffle_leaf(self, node, new_order):
        new_order = int(new_order)
        if node.localName not in ['leaf', 'knot']:
            raise ModifyTreeError('"shuffle_leaf" requires leaf or knot node,' + \
                ' {} provided.'.format(node.localName))
        if new_order < 1 or new_order > len(self._orders):
            raise ModifyTreeError('For this sentence, new_order must be ' + \
            'between 1 and {} inclusive.'.format(len(self._orders)))
        old_order = int(node.getAttribute('order'))
        for l in [self.leaves, self.knots]:
            for leaf in l:
                leaf_order = int(leaf.getAttribute('order'))
                if leaf_order < old_order and leaf_order < new_order:
                    # Do nothing
                    pass
                elif leaf_order > old_order and leaf_order > new_order:
                    # Do nothing
                    pass
                elif leaf_order > old_order: # <= new_order implicit
                    leaf.setAttribute('order', str(int(leaf.getAttribute('order')) - 1))
                elif leaf_order < old_order: # >= new_order implicit
                    leaf.setAttribute('order', str(int(leaf.getAttribute('order')) + 1))
        node.setAttribute('order', str(new_order))
        
    def restructure(self, **kwargs):
        """Restructures the tree so that it meets the properties in kwargs."""
        # remove fallen_leaves
        fallen_leaves = kwargs.get('fallen_leaves', True)
        if not fallen_leaves and self.fallen_leaves():
            self._no_fallen_leaves()
        # remove fallen_branches
        fallen_branches = kwargs.get('fallen_branches', True)
        if not fallen_branches and self.fallen_branches():
            self._no_fallen_branches()
        # remove terminal_branches
        terminal_branches = kwargs.get('terminal_branches', True)
        if not terminal_branches and self.terminal_branches():
            self._no_terminal_branches()
        # remove contacts
        contacts = kwargs.get('contacts', True)
        if not contacts and self.has_contacts():
            self._no_contacts()
        # rename knots
        knots = kwargs.get('knots', True)
        if not knots and self.has_knots():
            self._knot2leaf()
        # eliminate discontinuous branches
        crossing_branches = kwargs.get('crossing_branches', True)
        if not crossing_branches and self.crossing_branches():
            self._no_crossing_branches()
        # min_leaves_per_branch
        min_leaves_per_branch = kwargs.get('min_leaves_per_branch', 0)
        if min_leaves_per_branch > self.min_leaves_per_branch():
            self._set_min_leaves_per_branch(min_leaves_per_branch)
        # max_leaves_per_branch
        max_leaves_per_branch = kwargs.get('max_leaves_per_branch', 9999)
        if max_leaves_per_branch < self.max_leaves_per_branch():
            self._set_max_leaves_per_branch(max_leaves_per_branch)
        self._refresh_lists()
            
    def _no_fallen_leaves(self):
        """Attaches each fallen leaf or knot directly to the trunk."""
        fallen_leaves = self.get_child_leaves(self)
        for leaf in fallen_leaves:
            self.move_node(leaf, self.trunk)
            
    def _no_fallen_branches(self):
        """Attaches each fallen branch directly to the trunk."""
        fallen_branches = self.get_child_branches(self)
        for branch in fallen_branches:
            self.move_node_deep(branch, self.trunk)
            
    def _no_terminal_branches(self):
        """Removes all terminal branches."""
        x = self.branches[:]
        while x:
            branch = x.pop(0)
            if not self.get_child_structures(branch):
                self.del_node(branch)
                
    def _no_contacts(self):
        """Removes all contacts."""
        x = self.contacts[:]
        while x:
            contact = x.pop(0)
            self.del_contact(contact)
            
    def _knot2leaf(self):
        """Converts all knots to leaves."""
        x = self.knots[:]
        while x:
            knot = x.pop(0)
            leaf = self.createElement('leaf')
            node_map = knot.attributes
            for i in list(range(node_map.length)):
                attr = node_map.item(i)
                leaf.setAttribute(attr.name, attr.value)
            knot.parentNode.insertBefore(leaf, knot)
            knot.parentNode.removeChild(knot)
            knot.unlink()
        self._refresh_lists()
        
    def _set_min_leaves_per_branch(self, minl):
        """USE WITH CAUTION: will remove all branches with less than the
        required number of leaves, moving child nodes to grandparents."""
        stack = self.branches
        while stack:
            branch = stack.pop(0)
            leaves = self.get_child_leaves(branch)
            if len(leaves) < minl:
                self.del_node(branch)
                
    def _set_max_leaves_per_branch(self, maxl, minl=1):
        """USE WITH CAUTION: adds branches to contain smallest possible group of 
        leaves."""
        # print('set_max_leaves_per_branch called.')
        minl = 1 if minl < 1 else minl # must be at least 1 for this subroutine.
        for branch in self.branches:
            leaves = self.get_child_leaves(branch)
            if len(leaves) > maxl:
                # print('branch {} has {} leaves'.format(branch.getAttribute('id'), \
                # len(leaves)))
                leaves.sort(key=lambda x: x.getAttribute('order'))
                for i in list(range(maxl, len(leaves), minl)):
                    # print('i = {}'.format(i))
                    child_nodes = leaves[i:i+minl] if len(leaves) > i+minl else leaves[i:]
                    # print('Identified {} child_nodes'.format(len(child_nodes)))
                    new_branch = self.new_branch(child_nodes=child_nodes, ignore_warnings=True)
                    self.move_node_deep(new_branch, branch)
                    new_branch.setAttribute('relation', '_PART')
                    
    def _no_crossing_branches(self):
        blacklist = []
        for branch in self.branches:
            if self._is_discontinuous(branch):
                blacklist.append(branch)
        for node in blacklist:
            self.del_node(node)
                    
    def format_conll(self):
        """Creates a CoNLL compatible tree structure:
        - exactly one leaf or knot per branch;
        - identical properties on leaf and branch nodes;
        - no relation between leaf and branch nodes.
        
        If leaf and branch have a property with the same name, conflicts are
        resolved in favour of the *leaf*"""
        self.restructure(fallen_leaves=False, terminal_branches=False, \
        leafless_branches=False, max_leaves_per_branch=1, \
        min_leaves_per_branch=1)
        copy_to_branch = (set(self.branch_attrs) & set(self.leaf_attrs)) \
        - set(['id', 'relation', 'order'])
        add_to_branch = set(self.leaf_attrs) - set(self.branch_attrs)
        add_to_leaf = set(self.branch_attrs) - set(self.leaf_attrs)
        for attr in add_to_branch:
            self.add_branch_attr(attr)
        for attr in add_to_leaf:
            self.add_leaf_attr(attr)
        for branch in self.branches:
            leaves = self.get_child_leaves(branch)
            leaf = leaves[0]
            for attr in list(copy_to_branch | add_to_branch):
                branch.setAttribute(attr, leaf.getAttribute(attr))
            for attr in list(add_to_leaf):
                leaf.setAttribute(attr, branch.getAttribute(attr))
            leaf.setAttribute('relation', '--')
        self._refresh_lists()
        
    def order_nodes(self, node_list):
        """Places a list of nodes in text order, based on the position of the
        first word.  
        Where two nodes in the list have the same first word, ordering is
        random (but carried out).
        Will return None if one of the nodes to be ordered has no terminal
        children."""
        pos_list = []
        for node in node_list:
            if node.tagName in ['leaf', 'knot']:
                node_terminals = [node]
            else:
                node_terminals = node.getElementsByTagName('leaf')
                node_terminals.extend(node.getElementsByTagName('knot'))
            if not node_terminals:
                print('No terminals under\n {}'.format(node.toxml()))
                return None
            orders = [int(x.getAttribute('order')) for x in node_terminals]
            pos_list.append(min(orders))
        # if len(set(pos_list)) != len(pos_list): return None
        order_list = list(zip(pos_list, node_list))
        order_list.sort(key=lambda x: x[0])
        return [x[1] for x in order_list]
        
    def sort(self):
        """Ensures that leaf / knot nodes occur are in text order in
        the XML file."""
        if self.crossing_branches():
            raise ModifyTreeError("Can't linearize: tree has crossing branches.")
        self._sort(self.trunk)
        
    def _sort(self, node):
        children = self.get_child_structures(node)
        for child in children:
            node.removeChild(child)
        children_ordered = self.order_nodes(children)
        if children_ordered == None:
            raise ModifyTreeError(
                'Cannot order node containing no leafs or knots:\n{}'.format(node.toxml())
            )
        for child in children_ordered:
            self._sort(child)
            node.appendChild(child)
        
    def remove_branch_attr(self, attr):
        """Removes a branch attribute from the tree"""
        if attr in ['id', 'relation']:
            raise ModifyTreeError('Removal of required attribute "{}" not permitted.'.\
            format(attr))
        if attr not in self.branch_attrs:
            raise ModifyTreeError('Branches have no "{}" attribute.'.format(attr))
        self._remove_attr(self.branches, attr)
        return
    
    def remove_leaf_attr(self, attr):
        if attr in ['id', 'relation', 'order', 'value']:
            raise ModifyTreeError('Removal of required attribute "{}" not permitted'.\
            format(attr))
        if attr not in self.leaf_attrs:
            raise ModifyTreeError('Leaves have no "{}" attribute.'.format(attr))
        self._remove_attr(self.leaves, attr)
        self._remove_attr(self.knots, attr)
        return
        
    def _remove_attr(self, node_list, attr):
        for node in node_list:
            node.removeAttribute(attr)
        self._refresh_lists()
        
    def add_branch_attr(self, attr):
        """Adds new branch attr to the tree."""
        if attr not in self.branch_attrs:
            self._add_attr(self.branches, attr)
            
    def add_leaf_attr(self, attr):
        """Adds new leaf attr to the tree."""
        if attr not in self.leaf_attrs:
            self._add_attr(self.leaves, attr)
            
    def _add_attr(self, node_list, attr):
        if not is_valid_attr(attr):
            raise ModifyTreeError('Attribute name "{}" is not valid'.format(attr))
        for node in node_list:
            node.setAttribute(attr, '--')
        self._refresh_lists()
        
    def get_target(self, node):
        """Returns the target node of a contact."""
        if node not in self.contacts:
            return None
        x = self.find_nodes('id', node.getAttribute('idref'), regex=False)
        return x[0]
                    
    def to_string_tree(self):
        """Returns XML of tree as string without declaration."""
        return StringTree(self.toprettyxml()[22:])
        
class StringTreeContentHandler(xml.sax.handler.ContentHandler):
    
    def __init__(self):
        self.trunks = 0
        self.tree_id = ''
        self.tree_attrs = []
        self.branch_attrs = []
        self.leaf_attrs = []
        self.knot_attrs = []
        self.contact_attrs = []
        self.parent_child = []
        self._current_hierarchy = []
        self.structure_ids = []
        self.structure_idrefs = []
        self.orders = []
        self.num_leaves_knots = 0
        
    def startElement(self, name, attrs):
        if name == 'tree':
            if len(self.parent_child) > 0:
                raise ValidationError('<tree /> is not parent element')
            self.tree_attrs = attrs.getNames()
            if 'id' not in self.tree_attrs:
                raise ValidationError('<tree /> missing required attribute "id".')
            self.tree_id = attrs.getValue('id')
        
        elif name == 'trunk':
            self.trunks += 1
            if attrs.getLength() > 0:
                raise ValidationError('Error in tree ' + str(self.tree_id) + ': ' \
                + '<trunk /> must not have attributes.')
                
        elif name == 'branch':
            for attr in ['id', 'relation']:
                if attr not in attrs.getNames():
                    raise ValidationError('Error in tree ' + str(self.tree_id) \
                    + ': <branch /> missing required attribute "' + attr + '".')
            for attr in attrs.getNames():
                if attr not in self.branch_attrs:
                    self.branch_attrs.append(attr)
            self.structure_ids.append(attrs.getValue('id'))
                    
        elif name == 'leaf':
            for attr in ['id', 'order', 'relation', 'value']:
                if attr not in attrs.getNames():
                    raise ValidationError('Error in tree ' + str(self.tree_id) \
                    + ': <leaf /> missing required attribute "' + attr + '".')
            try:
                x = int(attrs.getValue('order'))
            except ValueError:
                raise ValidationError('Error in tree ' + str(self.tree_id) \
                + ': ' + name + ' id ' + str(attrs.getValue('id')) + \
                ' has non-integer order attribute.')
            if x in self.orders:
                raise ValidationError('Error in tree ' + str(self.tree_id) \
                + ': more than one element with order ' + str(x) + '.')
            self.orders.append(x)
            for attr in attrs.getNames():
                if attr not in self.leaf_attrs:
                    self.leaf_attrs.append(attr)
            self.structure_ids.append(attrs.getValue('id'))
            self.num_leaves_knots += 1

                    
        elif name == 'knot':
            for attr in ['id', 'order', 'value']:
                if attr not in attrs.getNames():
                    raise ValidationError('Error in tree ' + str(self.tree_id) \
                    + ': <knot /> missing required attribute "' + attr + '".')
            for attr in attrs.getNames():
                if attr not in self.knot_attrs:
                    self.knot_attrs.append(attr)
            self.structure_ids.append(attrs.getValue('id'))
            try:
                x = int(attrs.getValue('order'))
            except ValueError:
                raise ValidationError('Error in tree ' + str(self.tree_id) \
                + ': ' + name + ' id ' + str(attrs.getValue('id')) + \
                ' has non-integer order attribute.')
            if x in self.orders:
                raise ValidationError('Error in tree ' + str(self.tree_id) \
                + ': more than one element with order ' + str(x) + '.')
            self.orders.append(x)
            self.num_leaves_knots += 1
                    
        elif name == 'contact':
            for attr in ['idref', 'type']:
                if attr not in attrs.getNames():
                    raise ValidationError('Error in tree ' + str(self.tree_id) \
                    + ': <contact /> missing required attribute "' + attr + '".')
            for attr in attrs.getNames():
                if attr not in self.contact_attrs:
                    self.contact_attrs.append(attr)
            self.structure_idrefs.append(attrs.getValue('idref'))
                    
        else:
            raise ValidationError('Error in tree ' + str(self.tree_id) \
            + ': element "' + name + '" not recognized.')
                    
        self._current_hierarchy.append(name)
        if len(self._current_hierarchy) > 1:
            self.parent_child.append((self._current_hierarchy[-2], \
            self._current_hierarchy[-1]))
            
    def endElement(self, name):
        del self._current_hierarchy[-1]
        
    def endDocument(self):
        if self.trunks != 1:
            raise ValidationError('Error in tree ' + str(self.tree_id) \
            + ': must have 1 <trunk /> (not ' + str(self.trunks) + ').')
            
        if self.num_leaves_knots == 0:
            raise ValidationError('Error in tree ' + str(self.tree_id) \
            + ': tree has no leaves or knots.')
            
        for relation in self.parent_child:
            if relation not in legal_relations:
                raise ValidationError('Error in tree ' + str(self.tree_id) \
                + ': ' + relation[0] + ' dominates ' + relation[1] + '.')
                
        if len(self.structure_ids) != len(set(self.structure_ids)):
            for an_id in self.structure_ids:
                if self.structure_ids.count(an_id) > 1:
                    raise ValidationError('Error in tree ' + str(self.tree_id) \
                    + ': element id ' + str(an_id) + ' used by ' + \
                    str(self.structure_ids.count(an_id)) + ' elements.')
                    
        for an_idref in self.structure_idrefs:
            if an_idref not in self.structure_ids:
                raise ValidationError('Error in tree ' + str(self.tree_id) \
                + ': idref ' + str(an_idref) + ' matches no element.')
                
        self.orders.sort()
                
        if self.orders != list(range(len(self.orders) + 1))[1:]:
            raise ValidationError('Error in tree ' + str(self.tree_id) \
            + ': order attributes do not form a continuous sequence.')
            
class BaseForestStructureReader(xml.sax.handler.ContentHandler):
    """Reads the <structure/> node of a BaseForest while loading."""
    
    def __init__(self):
        self.structure = dict()
        self.name = ''
        
    def startElement(self, name, attrs):
        
        if name == 'structure':
            for attr in ['crossing_branches', 'terminal_branches', \
            'fallen_leaves', 'fallen_branches', 'knots', 'contacts']:
                if attr not in attrs.getNames():
                    raise ValidationError('Forest missing attribute "{}"'.format( \
                    attr))
                if attrs.getValue(attr) not in ['Y', 'N']:
                    x = 'Forest attribute "{}" must be "Y" or "N".'.format( \
                    attr)
                    raise ValidationError(x)
                self.structure[attr] = True if attrs.getValue(attr) == 'Y' else False
            for attr in ['min_leaves_per_branch', 'max_leaves_per_branch']:
                if attr not in attrs.getNames():
                    raise ValidationError('Forest missing attribute "{}"'.format( \
                    attr))
                try:
                    self.structure[attr] = int(attrs.getValue(attr))
                except ValueError:
                    if attrs.getValue(attr) == 'unbounded':
                        self.structure[attr] = 9999
                    else:
                        x = 'Forest attribute "{}" '.format(attr) 
                        x += 'must be integer or string "unbounded"'
                        raise ValidationError(x)
            
def parse_file(file_name):
    """Function to create a BaseForest object from a basetree.xml file.
       file_name may be string or file object."""
    
    if isinstance(file_name, str):
        with open(file_name, 'rb') as f:
            return _parse_file(f)
            
    else:
        return _parse_file(file_name)
        
def _parse_file(f):

    # 1. READ CONTENTS OF <tree> ELEMENTS AS STRINGS.
    # SPLIT INTO A LIST OF TREES STORED AS UNICODE STRINGS.
    # NO PARSING AND NO VALIDATION.
    data = []
    # Read file encoding from XML declaration
    decl = str(f.readline(), 'utf-8')
    x = decl.index('"', decl.index('encoding')) + 1
    codec = decl[x:decl.index('"', x)].lower()
    # Set up to read file.
    part_tree = ''
    in_tree = False
    in_preamble = True
    in_the_map = False
    preamble = ''
    # Parseline subfunction
    def _parse_line(s):
        nonlocal in_tree, in_preamble, preamble, part_tree, data
        start_trees = s.split('<tree')
        for i, string in enumerate(start_trees):
            if in_preamble and i == 0:
                preamble += string
            # add '<tree' element back again
            if i > 0:
                string = '<tree' + string
                in_tree = True
                in_preamble = False
            # re-split segment at end tags
            x = string.rsplit('</tree>', 1)
            if len(x) == 1 and in_tree:
                part_tree += x[0]
            elif len(x) == 2 and in_tree:
                part_tree += x[0]
                data.append(part_tree + '</tree>')
                in_tree = False
                part_tree = ''
    _parse_line(decl.split('?>')[1])
    # Read subsequent lines of file line by line.
    # Concatenate lines to give a single string for each tree.
    for line in f:
        # convert bytes to string
        s = str(line, codec)
        _parse_line(s)
    # Create the forest.
    forest = BaseForest()
    # Parse the Structure node using BaseForestStructureReader.
    m = re.search(r'<structure [^/>]+/>', preamble)
    if m:
        handler = BaseForestStructureReader()
        parser = xml.sax.parseString(m.group(), handler)
        forest.structure_rules = dict([x for x in handler.structure.items()])
    else:
        raise ValidationError('Forest has no structure node.')
    # Give the forest its data.
    forest.extend([x for x in data])
    # Chop up preamble into preamble and map.
    x = preamble.split('<map')
    if len(x) > 1:
        forest.the_map = '<map' + x[1]
    # Validate the forest
    forest.validate()
    return forest
    
def xmlent_resolve(s):
    """Replaces the five standard XML entities with the XML symbols."""
    s = s.replace('&amp;', '&')
    s = s.replace('&quot;', '"')
    s = s.replace('&apos;', "'")
    s = s.replace('&lt;', '<')
    s = s.replace('&gt;', '>')
    return s
    
def is_valid_attr(s):
    """
    Returns True if s is a valid attribute name.
    """
    if not s: return False
    for char in ['&', '"', "'", '<', '>']:
        if char in s: return False
    return True
    
def tostring(tree):
    return xml.etree.ElementTree.tostring(tree.getroot(), 'utf-8').decode('utf-8')
