#!/usr/bin/python3
# Alignment algorithm

import difflib, re, csv
from tta.io import ints

class Error(Exception):
    pass

class CSVError(Error):
    pass

class AlignerError(Error):
    pass

class StringMatcher():
    
    def __init__(self, variants=[], caps=False):
        ######################################################################
        # The "variants" tuple standardizes to a particular usage.           #
        # Element [0] is the standard form                                   #
        # Element [1] is a regex pattern string which matches all variants   #
        ######################################################################
        self.variants = variants
        self.caps = False
        
    def string_matcher(self, s1, s2):
        if self.caps:
            s1 = s1.lower()
            s2 = s2.lower()
        for variant in self.variants:
            s1 = re.sub(variant[1], variant[0], s1)
            s2 = re.sub(variant[1], variant[0], s2)
        if (s1 and s2) and s1 != s2:
            return '"{}" is not "{}"'.format(s1, s2)
        if s1 and not s2:
            return '"{}" missing in b'.format(s1)
        if s2 and not s1:
            return 'additional "{}" in b'.format(s2)
        return ''
    
class SequenceMatcher(difflib.SequenceMatcher):
    
    def __init__(self, isjunk=None, a='', b='', autojunk=True):
        self.isjunk = isjunk
        self.a = self.b = None
        self.autojunk = autojunk
        self.set_seqs(a, b)
        self.aligners = []
    
    def pass1(self, threshold=20):
        # Provides a more *efficient* method for the diff by carrying out
        # a first pass with autojunk enabled, then chopping up the result
        # into smaller blocks according to the longest matching sequences.
        sm = difflib.SequenceMatcher(None, self.a, self.b, True)
        mbls = sm.get_matching_blocks()
        self.aligners = []
        last_a_ix, last_b_ix = 0, 0
        for a_ix, b_ix, length in mbls:
            if length >= threshold and a_ix > last_a_ix:
                # Found the start of a match, chop the text here.
                self.aligners.append((
                    last_a_ix, last_b_ix,
                    difflib.SequenceMatcher(
                        None, 
                        self.a[last_a_ix:a_ix], 
                        self.b[last_b_ix:b_ix],
                        None
                    )
                ))
                last_a_ix, last_b_ix = a_ix, b_ix
        # One last append (for the end of the text):
        self.aligners.append((
            last_a_ix, last_b_ix,
            difflib.SequenceMatcher(
                None, 
                self.a[last_a_ix:], 
                self.b[last_b_ix:],
                None
            )
        ))
        
    def get_opcodes(self, threshold=20):
        if not self.aligners:
            self.pass1(threshold)
        # ignore_check argument overrides the sanity check to make sure the 
        # text is split into enough small blocks.
        i, ocs = 0, []
        for a_ix, b_ix, sm in self.aligners:
            i += 1
            # print('Pass 2: Block {} of {}'.format(i, len(self.aligners)))
            these_ocs = sm.get_opcodes()
            # Combine 'equal' op_codes over block divisions.
            if these_ocs[0][0] == 'equal' and ocs and ocs[-1][0] == 'equal':
                new_oc = these_ocs.pop(0)
                last_oc = ocs[-1]
                ocs[-1] = (
                    'equal', last_oc[1], new_oc[2] + a_ix, last_oc[3], new_oc[4] + b_ix
                )
            for oc in these_ocs:
                ocs.append((
                    oc[0], oc[1] + a_ix, oc[2] + a_ix, 
                    oc[3] + b_ix, oc[4] + b_ix
                ))
        return ocs
        
class OnePassSequenceMatcher(SequenceMatcher):
    """
    Gets rid of pass1, applying pass2 to the whole sequence of text.
    """
    
    def pass1(self, threshold=20):
        self.aligners = [(
            0, 0,
            difflib.SequenceMatcher(None, self.a, self.b, None)
        )]


class Aligner():
    
    # DIACRITICS
    DIACRITIC_CHR = [
        ('a', list(range(224, 230))),
        ('c', [231]),
        ('e', list(range(232, 236))),
        ('i', list(range(236, 240))),
        ('n', [241]),
        ('o', list(range(242, 247))),
        ('u', list(range(249, 253))),
        ('y', [253, 255])
    ]
    
    A_IX = 0
    B_LIST = 1
    MSG = 2
    
    def __init__(self, a_list, b_list, junk=None, threshold=20, ratio=.9):
        # Input is a list of (ID, token) tuples.
        self.a_list = a_list
        self.b_list = b_list
        self.a = '\n'.join([x[1] for x in a_list])
        self.b = '\n'.join([x[1] for x in b_list])
        self.aligned = []
        self.sequence_matcher = SequenceMatcher(junk, self.a, self.b, None)
        self.string_matcher = StringMatcher()
        # self.punct_regex = re.compile(r'''[.,;:?!"'()«»]+$''')
        # For debugging...
        self.ocs = []
        self.threshold=threshold
        self.ratio=ratio
        
    def align(self, verbose=True):
        
        def get_ixs(a):
            # 2. Generate first ix list
            a_ixs = [0]
            a_ixs.extend([x.start() + 1 for x in re.finditer('\n', a)])
            if a_ixs[-1] > len(a):
                a_ixs.pop()
            return a_ixs
            
        a_ixs = get_ixs(self.a)
        b_ixs = get_ixs(self.b)
        
        def get_oc_pos(oc):
            nonlocal start_ix, end_ix
            l = []
            if oc[1] == oc[2]:
                r = [oc[1]]
            else:
                r = range(oc[1], oc[2])
            if start_ix in r and end_ix - 1 in r:
                l.append('whole')
            elif oc[1] < end_ix:
                l.append('within')
            if end_ix in r:
                l.append('end')
            if oc[1] == end_ix + 1:
                l.append('after')
            return l
            
        # Shortcut name for string matcher
        sm = self.string_matcher.string_matcher
        # Group op_codes by a_item
        
        if verbose:
            print('Running diff (may take a while)...')
            print('Pass 1')
        self.sequence_matcher.pass1(self.threshold)
        if verbose:
            print('Pass 2')
        ocs = self.sequence_matcher.get_opcodes(self.threshold)
        
        if verbose:
            print('Mapping opcodes on to tokens')
        oc_by_aix = [[a_ixs.pop(0), []]]
        while a_ixs:
            next_ix = a_ixs.pop(0)
            # OC ends before or at end of item
            while ocs and ocs[0][2] <= next_ix:
                oc_by_aix[-1][1].append(ocs.pop(0))
            # OC starts before end of item 
            # (but, implicitly, ends after the end)
            if ocs and ocs[0][1] < next_ix:
                oc_by_aix[-1][1].append(ocs[0])
            oc_by_aix.append([next_ix, []])
        # Last item
        if ocs:
            oc_by_aix[-1][1].extend(ocs)
            
        # save opcodes
        #with open('tmp.txt', 'w') as f:
        #    f.write(str(oc_by_aix).replace(']],', ']],\n'))
        #with open('a.txt', 'w') as f:
        #    f.write(self.a)
        #with open('b.txt', 'w') as f:
        #    f.write(self.b)
        
        if verbose:
            print('Iterating over {} a_tokens to match up to b_tokens'.format(len(oc_by_aix)))           
        # Iterate over tokens to assign matches
        self.aligned = []
        b_tokens = self.b_list[:]
        b_token = b_tokens.pop(0)
        for i, oc_ix in enumerate(oc_by_aix):
            if verbose and i % 1000 == 0: print('{} of {} tokens complete'.format(i, len(oc_by_aix)))
            # Set up variables 
            a_token = self.a_list[i]
            ocs = oc_ix[1]
            oc_types = [oc[0] for oc in ocs]
            start_ix = oc_ix[0]
            if i < len(oc_by_aix) - 1:
                end_ix = oc_by_aix[i + 1][0] - 1
            else:
                end_ix = len(self.a) - 1
                
            notes = []
            b_matches = set([])
                
            for oc in ocs:
                
                # First iteration: codes with no changes to A tokenisation.
                a_str = self.a[oc[1]:oc[2]]
                b_str = self.b[oc[3]:oc[4]]
                oc_pos = get_oc_pos(oc)
                if oc[0] == 'equal' and ('whole' in oc_pos or 'within' in oc_pos):
                    b_matches.add(b_token[0])
                    
                if oc[0] != 'equal' and not 'end' in oc_pos and \
                not 'after' in oc_pos:
                    # i.e. WITHIN or WHOLE replace / delete / insert codes.
                    # Here, we assume that where a_str and b_str contain several
                    # tokens, the *last* part of these strings are part of the
                    # matched tokens.
                    if oc[1] == start_ix and b_str.count('\n') > 0 and \
                    b_str[-1] != '\n':
                        b_split = b_str.split('\n')
                        # Pre-token replace
                        notes.append('add_b_tokens_before: {}'.format(
                            ' '.join([x for x in b_split[:-1]])
                        ))
                        x = sm(a_str, b_split[-1])
                        if 'whole' in oc_pos:
                            # HERE --- to put ABSENT once string_matcher has
                            # been improved.
                            notes.append(x)
                        else:
                            notes.append(x)
                        for i in range(b_str.count('\n')):
                            if b_tokens:
                                b_token = b_tokens.pop(0)
                        b_matches.add(b_token[0])
                        
                    elif 'whole' in oc_pos:
                        # The whole token is deleted/replaced (except for the 
                        # final CR.)
                        # Could it be that the whole token is missing?
                        if oc[0] == 'delete':
                            notes.append('absent')
                        else:
                            # Otherwise, it's been replaced by something else.
                            # [TODO: Is this code correct??]
                            a_split = a_str.split('\n')
                            b_split = b_str.split('\n')
                            notes.append(sm(a_split[-1], b_split[-1]))
                            b_matches.add(b_token[0])
                    
                    # NEXT: changes within the token, that don't replace the
                    # whole token, and don't replace the last CR.
                    elif a_str.count('\n') == 0 and b_str.count('\n') == 0:
                        # Change within the token, no tokenization changes.
                        notes.append(sm(a_str, b_str))
                        
                    elif a_str.count('\n') == 0 and b_str.count('\n') > 0:
                        # b_str contains token boundary(ies)
                        # CASE 1:
                        # the last character of token a is unchanged --- truly
                        # within.
                        b_split = b_str.split('\n')
                        if oc[2] < end_ix - 1 or (oc[2] == end_ix - 1 and \
                        b_str[0] == '\n'):
                            notes.append('tokenization_b')
                            notes.append(sm(a_str, b_split[0]))
                            notes.append(sm(a_str, b_split[-1]))
                            b_matches.add(b_token[0])
                            for i in range(len(b_split) - 1):
                                if b_tokens:
                                    b_token = b_tokens.pop(0)
                                    b_matches.add(b_token[0])
                        else:
                            # Changes to A
                            notes.append(sm(a_str, b_split[0]))
                            notes.append('add_b_tokens "{}"'.format(
                                ' '.join([x for x in b_split[1:]])
                            ))
                            for i in range(len(b_split) - 1):
                                if b_tokens:
                                    b_token = b_tokens.pop(0)
                        
                       
                    elif a_str.count('\n') > 0 and b_str.count('\n') > 0:
                        # By inference, this can only be a beginning-of-token
                        # replace.
                        a_str_mini = a_str.split('\n')[-1]
                        b_str_mini = b_str.split('\n')[-1]
                        notes.append(sm(a_str_mini, b_str_mini))
                        b_matches.add(b_token[0])
                        
                elif 'whole' in oc_pos and oc[0] != 'equal':
                    notes.append('absent')
                        
                if oc[0] == 'insert' and ('end' in oc_pos or \
                'after' in oc_pos):
                    b_split = b_str.split('\n')
                    if 'end' in oc_pos:
                        notes.append(sm('', b_split[0]))
                        if len(b_split) > 1:
                            notes.append('add_b_tokens: {}'.format(
                                ' '.join([x for x in b_split[1:]])    
                            ))
                    else:
                        # The 'insert_after_end_before_next' case
                        if len(b_split) > 1:
                            notes.append('add_b_tokens: {}'.format(
                                ' '.join([x for x in b_split[:-1]])
                            ))
                    for x in range(len(b_split) - 1):
                        if b_tokens:
                            b_token = b_tokens.pop(0)
                        
            for oc in ocs:
                # ANYTHING THAT AFFECTS, OR MAY AFFECT, A TOKENISATION
                a_str = self.a[oc[1]:oc[2]]
                b_str = self.b[oc[3]:oc[4]]
                oc_pos = get_oc_pos(oc)
                
                if oc[0] in ['replace', 'delete'] and 'end' in oc_pos:
                    # The CR in A is replaced or deleted.
                    if a_str.count('\n') == 1 and b_str.count('\n') == 0:
                        # The CR has been deleted. BUT it could just be that 
                        # the whole token is missing or replaced, not that
                        # two tokens are fused. Check before signalling tok
                        # error.
                        if 'whole' in oc_pos and \
                        oc[1] > 0 and self.a[oc[1] - 1] == '\n':
                            pass
                            # Do nothing. The token is missing, it's already
                            # been tagged as 'absent' in the first pass.
                        # It could also be that the FOLLOWING token is 
                        # completely missing, and that this a_token has
                        # "borrowed" the CR from the missing token. Check.
                        elif a_str[0] == '\n' and \
                        (oc[2] == len(self.a) or self.a[oc[2]] == '\n') and \
                        oc[0] == 'delete':
                            # Do nothing. The next token is completely missing.
                            # This token is unmodified by this opcode.
                            pass
                        else:
                            notes.append('tokenization_a')
                            if len(a_str) > 1:
                                if a_str[0] == '\n':
                                    pass
                                elif a_str[-1] == '\n':
                                    notes.append(sm(a_str[:-1], b_str))
                                else:
                                    notes.append('MISMATCH')
                    if b_str.count('\n') == 1 and a_str.count('\n') == 1:
                        print('UNFORSEEN CASE: one "a" \n replaced by one "b" \n')
                        print(a_token, ocs)
                    if b_str.count('\n') > 1 and a_str.count('\n') > 0:
                        # CR replaced, extra tokens inserted.
                        a_split = a_str.split('\n') # min length is 2.
                        b_split = b_str.split('\n') # min length is 3.
                        notes.append(sm(a_split[0], b_split[0]))
                        notes.append('add_b_tokens: {}'.format(
                            ' '.join([x for x in b_split[1:-1]])
                        ))
                        for x in b_split[1:-1]:
                            if b_tokens:
                                b_token = b_tokens.pop(0)
                                
                if oc[0] == 'equal' and 'end' in oc_pos:
                    # next b_token please!
                    if b_tokens:
                        b_token = b_tokens.pop(0)

            l = list(b_matches)
            l.sort()
            # Remove all empty strings from "notes"
            while '' in notes: notes.remove('')
            self.aligned.append((a_token[0], l, notes))


    def aligned_tokens(self):
        
        def next_a():
            nonlocal a_list
            x = a_list.pop(0)
            a_list.append(x)
            return x
            
        def next_b():
            nonlocal b_list
            x = b_list.pop(0)
            b_list.append(x)
            return x
        
        retval = []
        a_list, b_list = self.a_list, self.b_list
        a, b = next_a(), next_b()
        for a_ix, b_ixs, msgs in self.aligned:
            bs = []
            while a_ix != a[0]: a = next_a()
            for b_ix in b_ixs:
                while b_ix != b[0]: b = next_b()
                bs.append(b)
            retval.append(dict({
                'a_id': a[0],
                'b_ids': ' '.join([str(b[0]) for b in bs]),
                'a_token': a[1],
                'b_tokens': ' '.join([str(b[1]) for b in bs]),
                'notes': ' AND '.join([msg for msg in msgs])
            }))
        return retval
        
    def write_csv(self, f1):
        with open(f1, 'w', newline='') as f:
            writer = csv.DictWriter(f, ['a_id', 'a_token', 'b_ids', 'b_tokens',
            'notes'])
            writer.writeheader()
            writer.writerows([x for x in self.aligned_tokens()])
            
    def get_tags_for_a(self, b_tuples):
        """Takes a list of (b_id, tag) tuples and returns a dictionary keyed
        by a_id with values as a list of tags."""
        
        # 1. Check that the aligner has been run first; otherwise, raise an
        # error.
        if not self.aligned:
            raise AlignerError('Inject called but alignment not yet' +
                'carried out.')
            
        # 2a. Get the reverse alignment table
        ra = self.get_reverse_aligned()
        
        # 3. Set up output
        a_tag_dict = dict()
        
        # 4. Iterate the b_tuples list: list of 2-tuples containing (ID, tag),
        # similar to b_list.
        for b_tuple in b_tuples:
            # 5. Get corresponding a_ids from ra. Use .get() to avoid KeyError.
            a_ids = ra.get(b_tuple[0]) or []
            # 6. Copy tag to a_tag_dict for all a_ids listed
            for a_id in a_ids:
                if not a_id in a_tag_dict:
                    a_tag_dict[a_id] = [b_tuple[1]]
                else:
                    a_tag_dict[a_id].append(b_tuple[1])
                    
        # 7. Return the result
        return a_tag_dict
            
        
    def get_reverse_aligned(self):
        """Reverses self.aligned so that it is indexed by b_id."""
        if not self.aligned:
            raise AlignerError('Reverse alignment called but alignment not yet' +
                'carried out.')
        #1. Set up variables
        ra = {}
        #2. Iterate self.aligned
        for tup in self.aligned:
            # Iterate each b_id listed in the aligned tuple (index 1)
            for b_id in tup[1]: 
                # If it is not in the ra dictionary: add it with a single listed
                # value for a_id.
                if not b_id in ra:
                    ra[b_id] = [tup[0]]
                # If it is the ra dictionary, append this a_id to the list
                else:
                    ra[b_id].append(tup[0])
                    
        # 3. To conclude, return the reverse_aligned table
        return ra
        
    def ratio_check(self):
        """Checks the similarity of the two texts to compare."""
        ratio = self.sequence_matcher.real_quick_ratio()
        if ratio < self.ratio:
            raise AlignerError(
                'Texts are too dissimilar: estimate of similarity ratio ' + \
                '({}) < minimum ratio ({})'.\
                format(int(ratio * 100), int(self.ratio * 100))
            )
                
class BasicAligner(Aligner):
    # Works like an aligner, but it assumes identical tokenization.
    # So basically does nothing special except ensure that the library is 
    # compatible with all scripts.
    
    def align(self):
        
        if len(self.a_list) != len(self.b_list):
            print('WARNING: Basic aligner called on texts with unequal number of tokens!')
        for a, b in zip(self.a_list, self.b_list):
            self.aligned.append((a[0], [b[0]], []))
            
class FixedAligner(Aligner):
    # Aligner initialized with a CSV file containing token alignment.
    
    def align(self):
        # Does nothing: alignment is read from the CSV file.
        print('WARNING: "Align" method called but alignment already read ' + \
            'from CSV file. Doing nothing.')
        pass
    
    def ratio_check(self):
        # Does nothing: alignment is read from the CSV file.
        print('WARNING: "ratio_check" method called but alignment already read ' + \
            'from CSV file. Doing nothing.')
        pass
    
    def sanity_check(self, a_list, b_list=[]):
        """Performs a sanity check to ensure that the texts for which the
        aligner was initialized are the same as the texts loaded in memory."""
        if not self.a_list == a_list:
            raise AlignerError('Text A in alignment data file does not match text A in file.')
        if b_list:
            if not set(self.b_list) <= set(b_list):
                raise AlignerError('Text B in alignment data file contains tokens not in text B in file.')
            
def aligner_from_csv(csvfile, enc='utf-8'):
    # Initializes an aligner with values read from a CSV file.
    # Note that for the moment, the "tags" column is ignored: it is not part of
    # the core aligner module.
    
    with open(csvfile, 'r', encoding=enc) as f:
        reader=csv.DictReader(f)
        
        # Check that the CSV file contains the necessary columns
        if not set(['a_id', 'a_token', 'b_ids', 'b_tokens']) <= \
        set(reader.fieldnames):
            raise CSVError(
                'CSV must contain the following fieldnames:' + \
                '"a_id", "a_token", "b_ids", "b_tokens"'
                )
        a_ids_all, a_list, b_ids_all, b_list, aligned = [], [], [], [], []
        for row in reader:
            notes = row['notes'].split(' AND ') if 'notes' in row and row['notes'] else []
            b_ids = row['b_ids'].split(' ') if row['b_ids'] else []
            # Convert to integer iff string integer
            b_ids = [ints(x) for x in b_ids]
            b_tokens = row['b_tokens'].split(' ') if row['b_tokens'] else []
            a_list.append((ints(row['a_id']), row['a_token']))
            if len(b_ids) == len(b_tokens):
                b_list.extend(list(zip(b_ids, b_tokens)))
            # Some weird cases where there is a space in b_token; accept if
            # only one matching token
            elif len(b_ids) == 1:
                b_list.append((b_ids[0], row['b_tokens']))
            else:
                x = 'Number of b_ids ({})'.format(len(b_ids)) + \
                ' not equal to number of b_tokens ({})'.format(len(b_tokens)) + \
                ' for a_id "{}".'.format(row['a_id']) + \
                ' b_ids:["{}"], b_tokens:["{}"]'.format(
                    '", "'.join([str(x) for x in b_ids]), '", "'.join([x for x in b_tokens])
                )
                raise CSVError(x)
            a_ids_all.append(ints(row['a_id']))
            b_ids_all.extend(b_ids)
            aligned.append((ints(row['a_id']), b_ids, notes))
            
    al = FixedAligner(a_list, b_list)
    al.aligned = aligned
    return al
    
