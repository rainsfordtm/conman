#!/usr/bin/python3
# Parser classes for text corpus importer

import string, re

class Parser():
    # Class from which all parsers inherit
    
    def __init__(self):
        self.lr_buff = ''
        self._bn_stack = []
        self.depth = 0
        self.last_tree = ''
        self.last_nest = None
        self.last_contacts = []
        self.t_end = -1
        self.log = ''
        self.debug = ''
        self.variant = '' # some formats have minor variants; store here
        
    def _flag_tree(self, ix, line):
        self.last_tree = self.lr_buff + line[:ix+1]
        self.lr_buff = ''
        self.t_end = ix
        
    def _end_line(self, line):
        if self.t_end == -1:
            self.lr_buff += line
            return False
        elif self.t_end != len(line) - 1:
            self.lr_buff = line[self.t_end + 1:]
        self.t_end = -1
        self.last_nest = None
        self.last_contacts = []
        return True
        
    def _bn_down(self, d=None):
        # ALWAYS USE!
        # DO NOT MODIFY!
        # Down one level
        if d:
            self._bn_stack[-1].append(d)
        self._bn_stack.append([])
        
    def _bn_up(self, d=None):
        # ALWAYS USE!
        # DO NOT MODIFY!
        # Up one level
        # _bn_up(d) is confusing: suggest _bn_level(d), _bn_up()
        if d:
            self._bn_stack[-1].append(d)
        if len(self._bn_stack) > 1:
            child = self._bn_stack.pop()
            self._bn_stack[-1].append(child)
            
    def _bn_level(self, d):
        # ALWAYS USE!
        # DO NOT MODIFY!
        # Stay on same level but add a unit
        self._bn_up(d)
        self._bn_down()
            
    def _found_list(self, found_list):
        
        # Force sequential numbering of found_list
        ixs = list(set([x[1] for x in found_list]))
        ixs.sort()
        if ixs != [str(x) for x in range(1, len(ixs) + 1)]:
            ix_map = dict(zip(ixs, list(range(1, len(ixs) + 1))))
            fl2 = []
            for item in found_list:
                fl2.append((item[0], str(ix_map[item[1]]), item[2], item[3]))
            self.debug += 'Changed {} to {}\n'.format(found_list, fl2)
            found_list = fl2
               
        ix = 1
        while ix > 0:
            l = list(filter(lambda x: x[1] == str(ix), found_list))
            if len(l) > 1 and 'branch' in [x[2] for x in l]:
                # Find parent node
                l3 = l
                l1, l2 = [], []
                x = l3.pop(0)
                while x[2] == 'leaf':
                    l1.append(x)
                    x = l3.pop(0)
                while x[2] == 'leaf' or x[3] != '--':
                    l2.append(x)
                    x = None
                    if l3:
                        x = l3.pop(0)
                    else:
                        break
                # l1 contains only leaves or nothing
                # l2[0] contains the first branch
                # x is the first non-tagged branch.
                if not x:
                    x = l2.pop(0)
                parent_id = x[0]
                l1.extend(l2)
                l1.extend(l3)
                for item in l1:
                    self.last_contacts.append(dict([
                        ('parent_id', parent_id),
                        ('idref', item[0]),
                        ('type', item[3])
                    ]))
                ix += 1
            elif len(l) == 1:
                self.log += 'Warning: lone index {} in tree.\n'.format(ix)
                ix += 1
                # print(self._bn_stack[0])
            elif len(l) > 1 and 'branch' not in [x[2] for x in l]:
                self.log += 'Warning: index {} without parent in tree.\n'.\
                format(ix)
                ix += 1
            else:
                ix = 0
            
    def linereader(self, line):
        # Default method, does no parsing.
        # Must be replaced by appropriate method in subclass.
        return self._end_line(line)
        
    def parse_tree(self, id_prefix=''):
        # Default method, does nothing.
        return self.last_tree, self.last_contacts
        
    def eof(self):
        # Default, does nothing.
        # Should be replaced by a method if tree endings are implicit
        # (i.e. in syntax 2), as buffer may contain unparsed tree at EOF.
        return False

class PennPsd(Parser):
    
    def __init__(self):
        Parser.__init__(self)
        self.in_comment = False # Flag to detect multi-line comments
        
    def is_comment(self, line):
        # Detects following conditions for comments:
        # 1. Line begins with '//'
        # 2. Line begins with '/*' or '/~*'; sets self.in_comment to True
        # 3. Line contains '*/', '*~/': treat as comment but set self.in_comment
        # to False
        # 4. self.in_comment is True
        if re.match('//.*', line): return True
        if re.match('/~?\*.*', line):
            self.in_comment = True
            return True
        if re.search('\*~?/', line):
            self.in_comment = False
            return True
        if self.in_comment: return True
        return False
    
    def linereader(self, line):
        # Routine adds to buffer up until the end of a tree is reached.
        # Must call the _flag_tree method when the end of a tree is found.
        # Must return the result of the _end_line method when finished.
        # 1. Detect comments and ignore them
        if self.is_comment(line):
            return self._end_line('\n')
        # 2. Call the tree parser
        return self._linereader(line)
            
    def _linereader(self, line):
        # 2. Parse the tree
        for i, char in enumerate(line):
            if char == ')':
                self.depth -= 1
                if self.depth == 0:
                    self._flag_tree(i, line)
            if char == '(':
                self.depth += 1
        return self._end_line(line)
        
    def parse_tree(self, id_prefix='', node_numbers = False):
        # Wrapper function.
        return self._parse_tree(id_prefix, node_numbers)
        
    def _parse_tree(self, id_prefix='', node_numbers = False):
        
        def write_d():
            nonlocal buff, id_count, id_prefix, found_list
            
            def fl_populate(penn_tag, elem_tag):
                nonlocal found_list, d
                
                ###############################################################
                # Decoding Horrible Code. December 2022
                #
                # Original fl_populate tried to decide if the LAST segment of
                # the tag was a digit. If it was, it concludes it's an index.
                # Otherwise, it does nothing.
                #
                # There's a problem here, because in the MCVF corpus, the index
                # and the SPE tag are sometimes the wrong way round.
                #
                # So in the NOT HORRIBLE CODE, fl_populate has become a more
                # sophisticated Penn Cat parser, which populates the found_list
                # and sorts out this bug. It now takes a string rather than 
                # a list as its main argument.
                ###############################################################
                
                # 0. First, run a regex on the Penn tag. Note that fullmatch
                # is necessary because otherwise some IDs, which might have
                # a number in the middle of them, will cause endless grief.
                m = re.fullmatch(r'(.*)([\-=][0-9]+)(-SPE)?', penn_tag)
                # 1. Is there a match? If not, fl_populate has literally
                # nothing to do, because no index has been found
                if not m: return
                # 2. Rewrite the tag without the index.
                penn_tag = m.group(1)
                # If there's no final -SPE tag after the index, m.group(3)
                # will be None, so need to interpret this as a string
                # to avoid problems
                penn_tag += m.group(3) if m.group(3) else ''
                # 3. Store the index digit(s).
                penn_index = m.group(2)[1:]
                # 4. Store the type of relation, i.e. the punctuation
                # symbol preceding the digit.
                # A hyphen receives the null value '--'
                penn_relation = '=' if m.group(2)[0] == '=' else '--'
                # 5. Update the found_list
                found_list.append((d['id'], penn_index, elem_tag, penn_relation))
                # 6. Update the penn_tag stored in d
                key = 'cat' if elem_tag == 'branch' else 'value'
                d[key] = penn_tag
                
                ###############################################################
                # Old fl_populate is below
                ###############################################################
                
                #if len(l) > 1 and l[-1]:
                #    try:
                #        int(l[-1])
                #    except ValueError:
                #        pass
                #    else:
                #        found_list.append((d['id'], l[-1], tag, atype))
                #        # Update d
                #        if tag == 'branch':
                #            d['cat'] = l[0]
                #        elif tag == 'leaf':
                #            d['value'] = l[0]
                #        else:
                #            badtagcrash
            
            tokens = buff.split()
            buff = '' # Initialize cs_id
            if len(tokens) == 0:
                return None
                
            ###################################################################
            # Addition to Horrible Code May 2022: this deals with node numbers.
            # It assumes the first argument is a node number, which it stores
            # as cs_id.
            # Then it eliminates the node_number from tokens so the Horrible
            # Old Code can work as normal.
            ###################################################################
            
            if node_numbers:
                cs_id = tokens[0]
                tokens = tokens[1:] if len(tokens) > 1 else []
                
            ###################################################################
                
            if len(tokens) in [1, 2]:
                id_count += 1
                d = dict(
                    [('id', id_prefix + str(id_count)), 
                    ('cat', tokens[0])]
                )
                ###############################################################
                # Further addition: adds cs_id to the dictionary of node
                # properties if node_numbers is enabled.
                ###############################################################
                if node_numbers:
                    d['cs_id'] = cs_id
                ###############################################################
                
                ###############################################################
                # December 2022: Updating the Horrible Code for dealing with
                # indices
                ###############################################################
                # This call to fl_populate deals with tokens[0],
                # which is the cat tag following an open parenthesis.
                ###############################################################
                fl_populate(tokens[0], 'branch')
                
                # This bit deals with tokens.
                if len(tokens) == 2:
                    self._bn_down(d)
                    id_count += 1
                    d = dict(
                        [('id', id_prefix + str(id_count)), 
                        ('value', tokens[1])]
                    )
                    # Second call to fl_populate passes the token. Much
                    # simpler now fl_populate deals with splitting off 
                    # indices.
                    fl_populate(tokens[1], 'leaf')
                    # Old code is commented out below.
                    #l = tokens[1].rsplit('-', 1)
                    #if l[-1] and l[-1] in string.digits:
                        # Above condition is necessary to deal with the case 
                        # where a WORD is "-" (or begins "-").  If what follows
                        # the dash is not a digit, then we assume it's not an
                        # index.
                    #    fl_populate(l, 'leaf')
                    self._bn_up(d)
                    return None
                else:
                    return d
            if buff: # don't tell me anything if the buffer is empty.
                print('PARSE ERROR:', buff)
            
        if not self.last_tree:
            return None
        if self.last_nest:
            return self.last_nest
        
        self._bn_stack = []
        found_list, contacts = [], []
        buff = ''
        id_count = 0
        
        # Create listnest
        for char in self.last_tree:
            if char in '()':
                d = write_d()
                if char == '(':
                    self._bn_down(d)
                elif char == ')':
                    self._bn_up(d)
            else:
                buff += char
        
        # Process found_list for contacts
        self._found_list(found_list)
        
        # Finish
        self.last_nest = self._bn_stack[0]
        return self.last_nest, self.last_contacts
        
class PennPsdOut(PennPsd):
    
    def __init__(self):
        Parser.__init__(self)
        # Buffer to store all comments preceding the tree.
        # Flushed by self.add_comment.
        self.comments = '' 
        
    def add_comment(self):
        # Has to store the comment somewhere, so adds it to 
        # self.last_nest[0][0], i.e. the top node in the tree, as a comment
        # attribute, replacing all whitespace with simple spaces
        # TECHNICALLY, this is a malformed basetree because all nodes should
        # have the same attributes but hey...
        self.last_nest[0][0]['comment'] = re.sub(r'\s+', ' ', self.comments)
        self.comments = ''
        
    def linereader(self, line):
        if self.is_comment(line):
            self.comments += line + '\n'
            return self._end_line('\n')
        # 2. Call the tree parser
        return self._linereader(line)
        
    def parse_tree(self, id_prefix='', node_numbers = True):
        # 1. Run the normal _parse_tree method with line numbers.  
        self._parse_tree(id_prefix, node_numbers)
        # 2. Add comments as a COMMENT node in the tree
        self.add_comment()
        return self.last_nest, self.last_contacts

class Syntax2(Parser):
    
    def eof(self):
        if self.lr_buff and not self.lr_buff.isspace() and \
        not self.lr_buff[-1] in ['9', '#'] and \
        not self.lr_buff[-2:] in ['9\n', '#\n']:
            if not self.lr_buff[-1] == '\n': self.lr_buff += '\n'
            if self.variant == 'C-tag':
                line = '.\t\n'
                self._flag_tree(2, line)
            else:
                line = '.\n'
                self._flag_tree(1, line)
        return self._end_line('\n')
    
    def linereader(self, line):
        # Routine adds to buffer up until the end of a tree is reached.
        # Must call the _flag_tree method when the end of a tree is found.
        # Must return the result of the _end_line method when finished.
        if self.variant == '' and re.match(r'[#96]\S*\t\S+$', line):
            self.variant = 'C-tag'
        elif self.variant == '' and re.match(r'[#96]\S*$', line):
            self.variant = 'normal'
        if line[0] in '!?' and line[1] != '!' and self.lr_buff:
            self._flag_tree(0, line)
        elif line[0] in '#96' and self.lr_buff:
            if self.variant == 'C-tag':
                line = '.\t' + line
                self._flag_tree(1, line)
            else:
                line = '.' + line
                self._flag_tree(0, line)
            
        # Ignore whitespace lines
        if not line.isspace():
            return self._end_line(line)
        else:
            return False
        
    def parse_tree(self, id_prefix=''):
        
        def next_id():
            nonlocal id_count, id_prefix
            id_count += 1
            return id_prefix + str(id_count)
            
        def tag_proc(item, the_id):
            # This routine processes all word / branch tagging elements
            # and populates the found_list.
            nonlocal found_list, line, used_links
            last_char, buff, parts = '', '', []
            for char in item:
                if (char == '<' and last_char != '<') or \
                (char == '>' and last_char != '>') or \
                (char == '!' and last_char != '!' and len(item) > 1) or \
                char == '@' or char == '&':
                    parts.append(buff)
                    buff = char
                    last_char = char
                else:
                    buff += char
            parts.append(buff)
             
            relation, index = '--', 0
            # parts[0] will be the WORD, if there is one.
            value = parts[0]
            for part in parts[1:]:
                if part[0] == '@':
                    relation = part[1:]
                elif part == '&':
                    relation = '&'
                elif part[0] == '<':
                    if part == part[0] * len(part):
                        n = str(len(part))
                    else:
                        n = part[1:]
                    if n in used_links:
                        self.log += \
                        'WARNING: Second use of link level {}. line:\n {}'.\
                        format(n, line) + '\nLink will be ignored.\n'
                    else:
                        found_list.append((the_id, n, 'branch', '--'))
                        used_links.append(n)
                elif part[0] == '>':
                    if part == part[0] * len(part):
                        index = str(len(part))
                    else:
                        index = part[1:]
                         
            # if both a relation and an index, the relation refers to the 
            # contact, not the hierarchical parent.
            if relation != '--' and index:
                found_list.append((the_id, index, 'branch', relation))
                relation = '--'
            elif index:
                found_list.append((the_id, index, 'branch', 'UNK'))
                  
            if '!!' in parts:
                relation += '!!'
              
            return value, relation
        
        # General check code
        if not self.last_tree:
            return None
        if self.last_nest:
            return self.last_nest
        
        self._bn_stack = [[]]
        found_list, contacts = [], []
        buff = ''
        id_count = 0
        last_indent = 0
        used_links = []
        
        lines = self.last_tree.splitlines()
        
        # 1. Process the first line of the tree for phrase-type / linking
        # properties
        t_head = dict([('id', next_id())])
        if lines[0][0] in '#69':
            if self.variant == 'C-tag':
                x = lines[0].rstrip().split('\t')
                t_head['relation'] = x[0]
                t_head['cat'] = x[1]
            else:
                t_head['relation'] = lines[0].rstrip()
            lines = lines[1:]
        else:
            t_head['relation'] = '###'
        
        for line in lines:
            # Calculate header, indent and contents
            blocks = line.split('\t')
            header, indent, content = '', 1, ''
            
            # Take out the cat tag for C-tagged files.
            if self.variant == 'C-tag':
                try:
                    cat = blocks.pop(1)
                except:
                    print(line)
                    raise
                
            if len(blocks) == 1:
                # No tab, sentence end.
                header = blocks[0]
                content = ''
                indent = 0
            else:
                for i, block in enumerate(blocks):
                    if i == 0:
                        header = block
                    elif block:
                        content = block
                    elif not content:
                        indent += 1
                    else:
                        pass
                    
            # Calculate indent change
            if indent > last_indent + 1:
                # Error
                self.log += 'WARNING: indent too deep: {}\n'.format(line)
                indent = last_indent + 1
            
            if indent <= last_indent:
                for i in range(last_indent - indent + 1):
                    self._bn_up()
                    
            if indent == 0:
                # finish the tree
                if header == '!':
                    # inverted !
                    self._bn_stack[0][0]['relation'] = \
                    self._bn_stack[0][0]['relation'] + chr(161)
                if header == '?':
                    # inverted ?
                    self._bn_stack[0][0]['relation'] = \
                    self._bn_stack[0][0]['relation'] + chr(191)
                
                # First process found_list.
                self._found_list(found_list)
                # Then return the tree.
                self.last_nest = self._bn_stack
                return self.last_nest, self.last_contacts
            
            if t_head:
                self._bn_down(t_head)
                t_head = {}
            else:
                self._bn_down()
                
            # Process line header
            the_id = next_id()
            x, relation = tag_proc(header, the_id)
            
            # token by token processing
            tokens = content.split()
            
            # Deal with curly braces.  They must be at the extremities of the
            # line.
            if tokens[0] == '{':
                d = {'id': next_id(), 'relation': '+'}
                if self.variant == 'C-tag': d['cat'] = 'CrdP'
                self._bn_down(d)
                tokens = tokens[1:]
                
            for i, token in enumerate(tokens):
                if i == 0:
                    d = {'id': the_id, 'relation': relation}
                    if self.variant == 'C-tag': d['cat'] = cat
                    self._bn_down(d)
                elif token == '}':
                    self._bn_up()
                    break
                else:
                    self._bn_down()
                
                # Process token tag
                the_id = next_id()
                value, relation = tag_proc(token, the_id)
                d = {'id': the_id, 'relation': relation}
                if self.variant == 'C-tag':
                    d['cat'] = '--'
                self._bn_down(d)
                self._bn_up(dict([('id', next_id()), ('value', value)]))
                self._bn_up()
            
            last_indent = indent
