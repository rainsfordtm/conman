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
    
    annotate(self, cnc, **kwargs):
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
          'CoreContextAnnotator': CoreContextAnnotator,
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
            **kwargs:
                **kwargs to be passed to self.annotate_hit.
                
        Returns:
            annotate(self, cnc, **kwargs) :
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
        Calls self.script on each hit in the concordance. The default 
        method does nothing else.
        
        Parameters:
            hit (conman.concordance.Hit):
                The Hit to be annotated.
        """
        return self.script(hit, **self.kwargs)
        
    def script(self, hit, **kwargs):
        """
        Default function for Annotator class applies to hit: returns the hit
        unchanged.
        
        Parameters:
            hit (conman.concordance.Hit):
                The hit to be annotated
            **kwargs:
                All further arguments must be keyword arguments.
        """
        return hit
        
class CoreContextAnnotator(Annotator):
    """
    Annotator which populates the CORE_CX list of a hit from the list of 
    tokens returned by the script.
    """
    
    def annotate_hit(self, hit):
        l = self.script(hit, **self.kwargs)
        l = list(l) # in case script has returned a hit object
        hit.core_cx = l
        return hit
        
    def script(self, hit, delim_pattern=''):
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

class KeywordTagAnnotator(Annotator):
    """
    Annotator providing a script method to project tags from the keywords up
    to the level of the hit. 
    """
    
    def script(self, hit, tags=[]):
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
        return hit
        
class LgermFilterAnnotator(Annotator):
    """
    Annotator which disambiguates LGeRM lemmas encoded as lgerm_out
    on the tokens. Calls lgerm.lgerm.LgermFilterer.
    """
    
    def script(self, hit, pos_tag='',
        kw_tag_to_hit=True,
        lower_case=True,
        prioritize_frequent=True,
        strip_numbers=True
    ):
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
            return KeywordTagAnnotator.script(None, hit, tags=[('lemma_lgerm', 'lemma_lgerm'), ('lgerm_out', 'lgerm_out')])
        else:
            return hit
            
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
    
    def get_ip_id(self, hit, tok):
        """Returns a unique identifier for the last IP node to
        dominate token tok, created from hit.ref (the CorpusSearch
        ID of the sentence) plus underscore plus the node number of
        the IP."""
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
    
    def script(self, hit, tags=[]):
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
        return hit
        
        
    
    
        
