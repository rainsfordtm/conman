#!/usr/bin/python3

# This file contains the 'script' method for processing Conllu files
# for word order information relative to the V2 constraint.
# The keyword must be a finite verb.

import re

def script(an, lang='french'):
    
    ##################################################################
    # SUBROUTINES
    ##################################################################
    
    # Getters
    # -------
    def get_head():
        # finds the head of the clause on which everything depends.
        nonlocal hit, T
        if re.match(r'aux.*|cop', T.tags['DEPREL']):
            return an.get_parent()
        else:
            # V-to-T
            return T
    
    def get_w1(tok):
        # find leftmost word in clause
        nonlocal hit
        l = an.get_descendents(tok)
        # Return either the first descendent or the token itself
        # whichever comes first in the hit.
        return l[0] if l and hit.index(l[0]) < hit.index(tok) else tok
        
    # Functions for detecting special tokens (universal)
    # --------------------------------------------------
    
    # could_be_prefield_clitic() uses structural properties and the prefield to
    # identify if a word is a clitic on the T head (and therefore
    # not to be counted).
    
    def could_be_prefield_clitic(tok):
        nonlocal prefield
        if not tok in prefield: return False # not in prefield > not a clitic.
        if an.get_children(tok): return False # has children > not a clitic.
        if not an.get_parent(tok).tags['UPOS'] != 'VERB': return False # doesn't depend on a verb > not a clitic.
        if not tok.tags['UPOS'] in ['PRON', 'ADV']: return False # not a pronoun or an adverb > not a clitic.
        l = [could_be_prefield_clitic(x) for x in prefield[prefield.index(tok):]]
        if False in l: return False # if there are non-clitics after it > not a clitic
        return True # Checks complete: this could be a prefield clitic
    
    # Functions for detecting special tokens (language-specific)
    # -----------------------------------------------
    
    # is_prefield_clitic is the language-specific clitic-finding function
    
    def is_prefield_clitic(tok):
        nonlocal lang, prefield
        if lang == 'french': return _is_clitic_fr(tok)
        return False # not handled
        
    def _is_prefield_clitic_fr(tok):
        nonlocal prefield
        if not could_be_prefield_clitic(tok): return False # Possible clitic?
        if tok.tags['UPOS'] == 'PRON':
            if re.match(
                r"([mtsl][e']?)|l[aiyou]|l[aeo][sz]|l(o|u|ou|eu)r|lu[iy]", # pronominal forms which are always clitic
                tok.lower()
            ):
                return True # yes it's a clitic
            elif not re.match(r'nsubj.*', tok.tags['DEPREL']) and \
            re.match(r"[nv](o|u|ou)[sz]", tok.lower()):
                return True # yes it's a clitic nous/vous
            else:
                return False
        if tok.tags['UPOS'] == 'ADV':
            if re.match(
                r"n[eo']?|ne[lmns]|[ae][nm]|[iy]", tok.lower()
            ):
                return True # yes it's negation or "ne" or "y" or "en"
            else:
                return False
        return False # we shouldn't get here but just in case.
     
    ##################################################################
    # SCRIPT
    ##################################################################
    
    ##################################################################
    # Locators
    # Identify some key nodes.
    ##################################################################
    
    an.reset_ids() # Resets the conll IDs in the hit, first step.
    hit = an.hit # Find the hit
    T = hit.kws[0] # Find the T head
    head = get_head() # Find the head of the clause (in a UD sense)
    w1 = get_w1(head) # Find the left-most word in the clause
    prefield = hit[hit.index(w1):hit.index(T)] # Get all tokens in the prefield
    
    # Test code to test subroutines
    l = []
    for tok in hit:
        if is_prefield_clitic(tok):
            l.append(str(tok))
    hit.tags['prefield_clitics'] = ' '.join(l)
    
