#!/usr/bin/python3

# This file contains the 'script' function for parsing the conllu output
# tagged according to UD norms and identifying a construction in which a motion
# verb is found.

def script(annotator, hit):
    
    # Subroutines to parse the structure
    def get_kw(hit):
        # When working with real data, returns the keyword. In the case of
        # the sample data, returns the root.
        for tok in hit:
            if int(tok.tags['conll_HEAD']) == 0: return tok
            
    def get_children(parent):
        """
        Returns all child toks of parent.
        """
        l = []
        for tok in hit:
            if int(tok.tags['conll_HEAD']) == int(parent['conll_ID']):
                l.append(tok)
        return l
        
    def get_descendents(parent):
        """
        Returns all descendent toks of parent.
        """
        l, newl = [], [parent]
        while newl:
            toks = newl
            newl = []
            for tok in toks:
                newl += get_children(tok)
            l += newl
        l.sort(key=lambda x: int(x.tags['conll_ID']))
        return l
    
    # Main procedure
    kw = get_kw(hit)
    
    # 1. Find arguments dependent on kw
    args = get_children(kw)
    
    # 2. Detect PP_complement
    l = []
    for arg in args:
        if arg.tags['conll_DEPREL'] == 'obl':
            l.append(arg)
    if l:
        hit.tags['pp_head'] = '|'.join(l)
        hit.tags['pp'] = '|'.join([' '.join(get_descendents(x)) for x in l])
    
    # 3. 
        
        
    