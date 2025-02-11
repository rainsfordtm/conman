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
        if re.fullmatch(r'aux.*|cop', T.tags['DEPREL']):
            return an.get_parent(T)
        else:
            # V-to-T
            return T
    
    def get_w1(tok):
        # find leftmost word in clause
        nonlocal hit
        l = an.get_descendents(tok)
        l = [x for x in l if x.tags['UPOS'] != 'PUNCT'] # don't count punctuation
        # Return either the first descendent or the token itself
        # whichever comes first in the hit.
        return l[0] if l and an.get_ix_from_tok(l[0]) < an.get_ix_from_tok(tok) else tok
        
    # Function Group 1: detection of special tokens (universal)
    # ---------------------------------------------------------
    # These functions don't make use of DEPRELs, just structure and
    # POS tagging.
    
    # could_be_prefield_clitic() uses structural properties and the prefield to
    # identify if a word is a clitic on the T head (and therefore
    # not to be counted).
    
    def could_be_prefield_clitic(tok):
        nonlocal prefield
        if not tok in prefield: return False # not in prefield > not a clitic.
        if an.get_children(tok): return False # has children > not a clitic.
        if not tok.tags['UPOS'] in ['PRON', 'ADV']: return False # not a pronoun or an adverb > not a clitic.
        # Next function is recursive.
        next_tok = an.get_next_tok(tok)
        if next_tok in prefield and not could_be_prefield_clitic(next_tok): return False
        return True # Checks complete: this could be a prefield clitic
        
    # is_c_element() identifies conventional complementizers: SCONJs and
    # WH elements like relative pronouns.
    def could_be_c_head(tok):
        nonlocal T, head, prefield
        if not tok in prefield: return False # not in prefield > not a c element
        if not is_dephead(tok): return False # not a child of head > not a c head
        if not tok.tags['UPOS'] in ['SCONJ', 'PRON', 'ADV']: return False # not a conjunction, pronoun or adverb: return False
        return True
        
    # is_dephead is a simple function to determine if the parent is the head
    def is_dephead(tok):
        nonlocal T, head
        # Handle the special case of the copula, promoting it to a dephead.
        if tok is head and not T is head and T.tags['DEPREL'] == 'cop': return True
        return an.get_parent(tok) is head if tok.tags['UPOS'] != 'PUNCT' else False
    
    def is_prefield_conjunction(tok):
        nonlocal T, head, prefield
        if not tok in prefield: return False # not in prefield > not a conjunction
        if not is_dephead(tok): return False # not dependent on head > not a conjunction
        if an.get_children(tok): return False # if children > not a conjunction
        if not tok.tags['UPOS'] == 'CCONJ': return False # If not a CCONJ > not a conjunction
        return True
    
    def is_prefield_interjection(tok):
        nonlocal prefield
        if not tok in prefield: return False # not in prefield > not an interjection
        if not tok.tags['UPOS'] == 'INTJ': return False # not an interjection
        return True
        
    # Function Group 2: detection of special deprels (universal)
    # ----------------------------------------------------------
    # These functions detect special deprels and apply only to depheads
    
    def is_parenthetical(tok):
        nonlocal T, head
        if not is_dephead(tok): return False
        if not tok.tags['DEPREL'] == 'parataxis': return False
        return True
        
    def is_vocative(tok):
        nonlocal T, head
        if not is_dephead(tok): return False
        if not tok.tags['DEPREL'] == 'vocative': return False
        return True
        
    # Functions for detecting special tokens (language-specific)
    # ----------------------------------------------------------
    
    def is_c_element(tok):
        nonlocal T, head, lang, prefield
        if lang == 'french': return _is_c_element_fr(tok)
        return False # not handled
    
    # is_prefield_clitic is the language-specific clitic-finding function
    def is_prefield_clitic(tok):
        nonlocal lang, prefield
        if lang == 'french': return _is_prefield_clitic_fr(tok)
        return False # not handled
        
    def _is_c_element_fr(tok):
        nonlocal T, head, prefield
        if not could_be_c_head(tok):
            # Check if parent is a C element, in which case this is too.
            parent = an.get_parent(tok)
            return True if parent and is_c_element(parent) else False
        # From here, it could be a C element
        # SCONJ: definitely
        if tok.tags['UPOS'] == 'SCONJ': return True
        # PRON: check the form
        if tok.tags['UPOS'] == 'PRON':
            # qu- words
            if re.match(r"k|qu?", str(tok).lower()): return True
            # cui
            if re.fullmatch(r"cu[iy]", str(tok).lower()): return True
            # (X)quel words
            # DISABLED: not clear that these are C elements
            # if re.match(r".{,3}(k|qu)ei?[ul]", str(tok).lower()): return True
            # dont
            if re.match(r"d[ou][nm]", str(tok).lower()): return True 
            # où
            if re.fullmatch(r"u|o[uù]?", str(tok).lower()): return True
            # Otherwise False
            return False
        if tok.tags['UPOS'] == 'ADV':
            # comment
            if re.match(r"comm?[ae]nt", str(tok).lower()): return True
            # combien
            if re.match(r"combien", str(tok).lower()): return True
            return False
    
    def _is_prefield_clitic_fr(tok):
        nonlocal prefield
        if not could_be_prefield_clitic(tok): return False # Possible clitic?
        if tok.tags['UPOS'] == 'PRON':
            if re.fullmatch(
                r"([mtsl][e']?)|l[aiyou]|l[aeo][sz]|l(o|u|ou|eu)r|lu[iy]", # pronominal forms which are always clitic
                str(tok).lower()
            ):
                return True # yes it's a clitic
            elif not re.match(r'nsubj', tok.tags['DEPREL']) and \
            re.fullmatch(r"[nv](o|u|ou)[sz]", str(tok).lower()):
                return True # yes it's a clitic nous/vous
            else:
                return False
        if tok.tags['UPOS'] == 'ADV':
            if re.fullmatch(
                r"n[eo']?|ne[lmns]|[ae][nm]|[iy]", str(tok).lower()
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
    T_ix = an.get_ix_from_tok(T)
    head = get_head() # Find the head of the clause (in a UD sense)
    head_ix = an.get_ix_from_tok(head)
    w1 = get_w1(head) # Find the left-most word in the clause
    w1_ix = an.get_ix_from_tok(w1)
    prefield = hit[w1_ix:T_ix] # Get all tokens in the prefield
    # Calculate interjection status for every item in prefield
    prefield_interjection_status = [is_prefield_interjection(x) for x in prefield]
    # Calculate clitic status for every item in prefield
    prefield_clitic_status = [is_prefield_clitic(x) for x in prefield]
    # Calculate conjunction status for every item in prefield
    prefield_conjunction_status = [is_prefield_conjunction(x) for x in prefield]
    # Calculate C-status for every item in prefield
    prefield_c_status = [is_c_element(x) for x in prefield]
    # Get head status for remaining items in prefield after conjunctions
    # C elements
    l = []
    for i, (is_interjection, is_clitic, is_conjunction, is_c, tok) in enumerate(zip(
        prefield_interjection_status,
        prefield_clitic_status,
        prefield_conjunction_status,
        prefield_c_status,
        prefield
    )):
        # We disregard everything BEFORE conjunctions and C elements
        # as being outside the clause
        if is_conjunction or is_c:
            # Reset list
            l = [False] * (i + 1)
        elif is_clitic or is_interjection:
            l.append(False)
        else:
            l.append(is_dephead(tok))
    prefield_dephead_status = l
    # Some depheads are still not interesting for word order even though
    # they're constituents. This applies to parenthetical and vocatives.
    prefield_parenthetical_status = [is_parenthetical(x) for x in prefield]
    prefield_vocative_status = [is_vocative(x) for x in prefield]
    # Now we can calculate the "countable" heads for word order
    l = []
    for parenthetical, vocative, dephead, tok in zip(
        prefield_parenthetical_status,
        prefield_vocative_status,
        prefield_dephead_status,
        prefield
    ):
        if dephead and not parenthetical and not vocative:
            l.append(True)
        else:
            l.append(False)
    prefield_countable_head_status = l
    
    # Next stage: Tag the countable heads as a basis for the WO analysis.
    
    
    # Test code to test subroutines
    l = []
    for status, tok in zip(prefield_clitic_status, prefield):
        if status: l.append(str(tok))
    hit.tags['prefield_clitics'] = ' '.join(l)
    l = []
    for status, tok in zip(prefield_conjunction_status, prefield):
        if status: l.append(str(tok))
    hit.tags['prefield_conjunctions'] = ' '.join(l)
    l = []
    for status, tok in zip(prefield_c_status, prefield):
        if status: l.append(str(tok))
    hit.tags['prefield_cs'] = ' '.join(l)
    l = []
    for status, tok in zip(prefield_countable_head_status, prefield):
        if status: l.append(str(tok))
    hit.tags['prefield_countable_heads'] = ' '.join(l)
    hit.tags['T'] = str(T)
    hit.tags['head'] = str(head)
    hit.tags['w1'] = str(w1)
    hit.tags['prefield'] = [str(x) for x in prefield]
    
