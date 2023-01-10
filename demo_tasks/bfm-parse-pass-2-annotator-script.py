#!/usr/bin/python3
def script(annotator, hit):
    
    # Subroutines to parse the structure
    def get_kw(hit):
        # When working with real data, returns the keyword. In the case of
        # the sample data, returns the root.
        # for tok in hit:
        #    if int(tok.tags['conll_HEAD']) == 0: return tok
        return hit.kws[0]
            
    def get_children(parent):
        """
        Returns all child toks of parent.
        """
        l = []
        for tok in hit:
            if not 'conll_ID' in tok.tags: continue
            try:
                if int(tok.tags['conll_HEAD']) == int(parent.tags['conll_ID']):
                    l.append(tok)
            except:
                print(hit)
                print(tok)
                print(tok.tags)
                raise
        return l
        
    def get_descendents(parent):
        """
        Returns all descendent toks of parent.
        """
        l, newl, i = [], [parent], 0
        while newl and i < 1000:
            i += 1
            toks = newl
            newl = []
            for tok in toks:
                newl += get_children(tok)
            l += newl
        l.sort(key=lambda x: int(x.tags['conll_ID']))
        return l
        
    def get_lemma(tok, var):
        """
        Returns the lemma matching the form of token from the key: regex
        dictionary in var.
        """
        for lemma, pattern in var.items():
            if re.fullmatch(pattern, str(tok).lower()):
                return lemma
        return ''
        
    def get_string(parent):
        """
        Returns the parent and all dominated nodes as a string.
        """
        tree = get_descendents(parent)
        tree.append(parent)
        tree.sort(key=lambda x: int(x.tags['conll_ID']))
        return ' '.join([str(x) for x in tree])
        
    # First, reset the Conll IDs, since each hit is a series of small trees
    # Otherwise the search algorithm will get very muddled indeed
    i, last_id = 0, 0
    for tok in hit:
        if not 'conll_ID' in tok.tags: continue
        if int(tok.tags['conll_ID']) < last_id:
            last_id = 0
            i += 1
        last_id = int(tok.tags['conll_ID'])
        tok.tags['conll_ID'] = str(i*100 + int(tok.tags['conll_ID']))
        tok.tags['conll_HEAD'] = str(i*100 + int(tok.tags['conll_HEAD']))
        # print(tok.tags)
    
    # Main procedure
    kw = get_kw(hit)
    # 1. Find arguments dependent on kw
    args = get_children(kw)
    
    # 2. Search for direct object
    has_obj = False
    objs = []               
    for arg in args:               
        if arg.tags['conll_DEPREL'] == 'obj':
            objs.append(get_string(arg))
            has_obj = True
    hit.tags['has_obj'] = 'yes' if has_obj else 'no'
    hit.tags['obj'] = ' | '.join(objs)
    
    return hit

