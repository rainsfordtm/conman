#!/usr/bin/python3

import re
from lgerm.lgerm import LgermFilterer

class Annotator():
    """
    Base class used to add annotation to a hit. The class method "script",
    which does nothing by default, can be updated to provide custom 
    annotation.
    
    Class method:
    -------------
    create(cls, annotator_type):  
        Creates an instance of annotator_type and returns it.
    
    Attributes:
    -----------
    kwargs (dict):
        Dictionary of keyword arguments to be passed to script.

    Methods:
    --------
    
    annotate(self, cnc):
        Adds annotation to the concordance using the script function.
        
    annotate_hit(self, hit):
        Run before script on each hit in the concordance.
        
    script(self, hit, **kwargs):
        Returns updated hit.
    """
    
    @classmethod
    def create(cls, annotator_type):
        """
        Creates an instance of annotator_type and returns it.
        """
        
        ANNOTATOR_TYPE_TO_CLASS_MAP = {
          'Annotator':  Annotator,
          'ConllAnnotator': ConllAnnotator,
          'CoreContextAnnotator': CoreContextAnnotator,
          'EvaluationAnnotator': EvaluationAnnotator,
          'KeywordTagAnnotator': KeywordTagAnnotator,
          'LgermFilterAnnotator': LgermFilterAnnotator,
          'PennAnnotator': PennAnnotator
        }
        if annotator_type not in ANNOTATOR_TYPE_TO_CLASS_MAP:
              raise ValueError('Bad annotator type {}'.format(annotator_type))
        return ANNOTATOR_TYPE_TO_CLASS_MAP[annotator_type]()
        
    def __init__(self):
        self.kwargs = {}
    
    def annotate(self, cnc):
        """
        Calls self.annotate_hit on each hit in the concordance.
            
        Parameters:
            cnc (conman.concordance.Concordance):
                The concordance to be annotated.
                
        Returns:
            annotate(self, cnc) :
                An updated concordance.
        """
        for i, hit in enumerate(cnc):
            # counter for very large cncs
            if len(cnc) > 10000 and i // 10000 == i / 10000 and i > 0:
                print('Annotating hit {} of {}'.format(str(i), str(len(cnc))))
            hit = self.annotate_hit(hit)
        return cnc
        
    def annotate_hit(self, hit):
        """
        Sets the "hit" attribute of the Annotator to the current hit,
        then calls self.script.
        
        Parameters:
            hit (conman.concordance.Hit):
                The Hit to be annotated.
        """
        self.hit = hit
        self.script(**self.kwargs)
        return self.hit
        
    def script(self, **kwargs):
        """
        Default function for Annotator class applies to hit: returns the hit
        unchanged.
        
        Parameters:
            **kwargs:
                All further arguments must be keyword arguments.
        """
        pass
        
class ConllAnnotator(Annotator):
    """
    Annotator with methods for parsing the structure of a CONLL-U
    file.
    """
    
    def get_children(self, parent):
        """
        Returns all child toks of tok.
        
        Parameters:
            parent (conman.concordance.Token)
                The token for which descendents should be found.
                
        Returns:
            self.get_children(hit, parent)
                A list of Tokens which are the children of parent.
        """
        l = []
        for tok in self.hit:
            if not 'conll_ID' in tok.tags: continue
            try:
                if int(tok.tags['conll_HEAD']) == int(parent.tags['conll_ID']):
                    l.append(tok)
            except:
                print(self.hit)
                print(tok)
                print(tok.tags)
                raise
        return l
        
    def get_descendents(self, parent):
        """
        Returns all descendent toks of parent.
        
        Parameters:
            parent (conman.concordance.Token)
                The token for which descendents should be found.
                
        Returns:
            self.get_descendents(parent)
                A list of Tokens which depend on parent.
        """
        l, newl, i = [], [parent], 0
        while newl and i < 1000:
            i += 1
            toks = newl
            newl = []
            for tok in toks:
                newl += self.get_children(tok)
            l += newl
        l.sort(key=lambda x: int(x.tags['conll_ID']))
        return l
        
    def get_parent(self, tok):
        """
        Returns the parent tok of a given token using the conll_HEAD
        entry in the dictionary.
        
        Parameters:
            parent (conman.concordance.Token)
                The token for which the parent should be found.
                
        Returns:
            self.get_parent(tok)
                The parent token identified by the conll_HEAD tag.
        """
        head_id = int(tok.tags.get('conll_HEAD', '0'))
        if head_id == 0: return None
        l = list(filter(lambda x: int(x.tags.get('conll_ID', '0')) == head_id, self.hit))
        if not l: return None
        return l[0]
    
    def get_string(self, parent):
        """
        Returns the parent and all dominated nodes as a string.
        
        Parameters:
            parent (conman.concordance.Token)
                The token for which descendents should be found.
                
        Returns:
            self.get_string(parent)
                A string representing the tokens in the subtree
                depending on parent.
        """
        tree = self.get_descendents(parent)
        tree.append(parent)
        tree.sort(key=lambda x: int(x.tags['conll_ID']))
        return ' '.join([str(x) for x in tree])
        
    def reset_ids(self):
        """
        Resets the conll_IDs in the hit, since they may have been
        derived from several subtrees.
        """
        i, last_id = 0, 0
        for tok in self.hit:
            if not 'conll_ID' in tok.tags: continue
            if int(tok.tags['conll_ID']) < last_id:
                last_id = 0
                i += 1
            last_id = int(tok.tags['conll_ID'])
            tok.tags['conll_ID'] = str(i*100 + int(tok.tags['conll_ID']))
            tok.tags['conll_HEAD'] = str(i*100 + int(tok.tags['conll_HEAD']))

class CoreContextAnnotator(Annotator):
    """
    Annotator which populates the CORE_CX list of a hit from the list of 
    tokens returned by the script.
    """
    
    def annotate_hit(self, hit):
        self.hit = hit
        l = self.script(**self.kwargs)
        l = list(l) # in case script has returned a hit object
        self.hit.core_cx = l
        return self.hit
        
    def script(self, delim_pattern=''):
        hit = self.hit
        # If no kws, return empty list.
        if not hit.kws: return []
        # Set flag
        core = False
        # Compile regex
        regex = re.compile(delim_pattern)
        # Iterate forwards, then backwards over the tokens
        passes = []
        for seq in [hit, reversed(hit)]:
            l = []
            for tok in seq:
                # If tok is a delimiter, set core to False (end of seq)
                if regex.fullmatch(str(tok)):
                    # not in core...
                    core = False
                # ...provided it's not a kw, for which core is always True.
                if hit.is_kw(tok):
                    core = True
                l.append(core)
            passes.append(l)
        # Reverse the second pass in place
        passes[1].reverse()
        # Merge into a single list of boolean values
        bools = []
        for pass1, pass2 in zip(passes[0], passes[1]):
            bools.append(True) if pass1 or pass2 else bools.append(False)
        # Make token list
        l = []
        for tok, val in zip(list(hit), bools):
            if val: l.append(tok)
        return l
        
class EvaluationAnnotator(Annotator):
    """
    As the parent class, but prints a summary of key statistics and
    changes made by the annotation script once the annotation procedure
    is complete.
    """
    
    def __init__(self):
        # Run the parent class method.
        Annotator.__init__(self)
        # Add an extra dictionary attribute for storing basic
        # statistics.
        self.summary = {}
        
    def annotate(self, cnc):
        """
        Calls the parent annotate() method and then prints a summary of
        statistics.
            
        Parameters:
            cnc (conman.concordance.Concordance):
                The concordance to be annotated.
                
        Returns:
            annotate(self, cnc) :
                An updated concordance.
        """
        cnc = Annotator.annotate(self, cnc)
        self.summary['total_hits'] = len(cnc)
        self.print_summary()
        return cnc
        
    def print_summary(self):
        """
        Prints the contents of the self.summary dictionary in 
        tabular form to standard out.
        """
        s = 'SUMMARY OF ANNOTATION:\n'
        s += '**********************\n'
        max_key = max([len(key) for key in self.summary.keys()])
        for key, value in self.summary.items():
            s += '{} {!s: >7}\n'.format(key + ' ' * (max_key - len(key)), value)
        print(s)

class KeywordTagAnnotator(Annotator):
    """
    Annotator providing a script method to project tags from the keywords up
    to the level of the hit. 
    """
    
    def script(self, tags=[]):
        hit = self.hit
        # Tags should be a list of (kw_tag, hit_tag) pairs
        for kw_tag, hit_tag in tags:
            l = []
            for kw in hit.kws:
                if kw_tag in kw.tags:
                    l.append(kw.tags[kw_tag])
                else:
                    l.append('')
            try:
                hit.tags[hit_tag] = '_'.join(l)
            except:
                print(hit)
                print(hit.tags)
                print(l)
                print(hit.kws)
                raise
        
class LgermFilterAnnotator(Annotator):
    """
    Annotator which disambiguates LGeRM lemmas encoded as lgerm_out
    on the tokens. Calls lgerm.lgerm.LgermFilterer.
    """
    
    def script(self, pos_tag='',
        kw_tag_to_hit=True,
        lower_case=True,
        prioritize_frequent=True,
        strip_numbers=True
    ):
        hit = self.hit
        # initialize filterer
        filterer = LgermFilterer()
        for tok in hit:
            # Check the necessary information is tagged on the token
            if not 'lgerm_out' in tok.tags or not pos_tag in tok.tags: continue
            lemmas = filterer.filter_lemmas(
                str(tok), tok.tags[pos_tag], tok.tags['lgerm_out'],
                filterer.MAPPING_CATTEX, filterer.MAPPING_LGERM
            )
            lemmas = filterer.refine_lemmas(
                lemmas, 
                lower_case=lower_case,
                prioritize_frequent=prioritize_frequent,
                strip_numbers=strip_numbers
            )
            tok.tags['lemma_lgerm'] = '|'.join(lemmas)
        if kw_tag_to_hit:
            KeywordTagAnnotator.script(None, tags=[('lemma_lgerm', 'lemma_lgerm'), ('lgerm_out', 'lgerm_out')])
            
class PennAnnotator(Annotator):
    """
    Annotator containing methods for performing analysis on corpora
    imported from Penn Treebank format.
    Default script prints (i) the cat of the keynode and (ii) the
    form and the cat of all nodes of interest identified in the 
    keyword_node_regex.
    Like KeywordTagAnnotator, also raises tags given in the 
    tags argument to the level of the hit.
    """
    
    def get_ip_id(self, tok):
        """Returns a unique identifier for the last IP node to
        dominate token tok, created from hit.ref (the CorpusSearch
        ID of the sentence) plus underscore plus the node number of
        the IP."""
        hit = self.hit
        # Check the token has ancestors.
        if not 'ancestors' in tok.tags: return hit.ref
        # Check that the token itself isn't an IP (unlikely)
        if tok.tags['cat'].startswith('IP'):
            return hit.ref + '_' + tok.tags['cs_id']
        # Turn ancestor attributes into lists
        ancestors = tok.tags['ancestors'].split('|')
        ancestors_cs_id = tok.tags['ancestors_cs_id'].split('|')
        # Iterate to find IP
        for cs_id, cat in zip(ancestors_cs_id, ancestors):
            if cat.startswith('IP'):
                return hit.ref + '_' + cs_id
        # Found no IP (unlikely), must return something
        return hit.ref
    
    def script(self, tags=[]):
        hit = self.hit
        # Tags is a list of kw tags.
        # 1. Get keywords
        kws = hit.kws
        # Quit if no keywords
        if not kws: return hit
        # 2. Find keys beginning 'KEYNODE_'
        keynode_keys = []
        for tag in kws[0].tags.keys():
            # In case trees were split, need to read back KW number.
            kw_no = kws[0].tags['KEYWORDS']
            if tag.startswith('KEYNODE_'): keynode_keys.append(tag)
        # 3. Build tag, token_list tuples for each KEYNODE tags
        keynodes = []
        for key in keynode_keys:
            l = []
            for tok in hit:
                if tok.tags[key] == kw_no: l.append(tok)
            keynodes.append((key, l))
        # 4. Add form and cat of each keynode as a hit tag
        # Begin with keyword cat
        hit.tags['kw_cat'] = kws[0].tags['KN_cat']
        # Other keynodes
        for key, toks in keynodes:
            hit.tags[key[8:] + '_' + 'form'] = ' '.join([str(tok) for tok in toks])
            hit.tags[key[8:] + '_' + 'cat'] = toks[0].tags['KN_cat'] if toks else ''
        # 6. Iterate over tags and add each one
        for tag in tags:
            hit.tags['kw_' + tag] = ' '.join([tok.tags[tag] for tok in kws])
            for key, toks in keynodes:
                hit.tags[key[8:] + '_' + tag] = ' '.join([tok.tags[tag] for tok in toks])
        # 7. Create ip_id tag to uniquely identify the IP containing
        # the hit. For compatibility with AS's coding tables.
        hit.tags['ip_id'] = self.get_ip_id(hit, kws[0])
