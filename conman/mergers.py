#!/usr/bin/python3

from conman.concordance import Concordance, Hit
import tta.aligner
import difflib # needed to change the SequenceMatcher when aligning short seqs

class Merger():
    """
    Parent class to merge two concordances.
    
    Attributes:
    -----------
    cnc (concordance.Concordance):
        Concordance to merge into
    other_cnc (concordance.Concordance):
        Concordance to merge from.
        
    Method:
    -------
    merge:
        Return self.cnc unmodified and prints a warning. The parent class
        cannot do any merging.
    """
    
    @classmethod
    def create(cls, merger_type):
        """
        Creates an instance of merger_type and returns it.
        """
        
        MERGER_TYPE_TO_CLASS_MAP = {
          'TextMerger': TextMerger,
          'ConcordanceMerger': ConcordanceMerger
        }
        if merger_type not in MERGER_TYPE_TO_CLASS_MAP:
              raise ValueError('Bad merger type {}'.format(merger_type))
        return MERGER_TYPE_TO_CLASS_MAP[merger_type]()
        
    def __init__(self):
        """
        Initializes base attributes for all instances of the class.
        """
        self.cnc, self.other_cnc = None, None
        
    def merge(self):
        """
        Dummy method in parent class, does nothing except return self.cnc
        and print a warning.
        """
        print('WARNING: Merger parent class does nothing, select a subclass.')
        return self.cnc

class TextMerger(Merger):
    """
    Class used to merge two concordance.Concordance objects at the level of
    the Token rather than at the level of the Hit, i.e. it ignores the Hits
    in other_cnc. The two concordances must contain (more or less) the same
    tokens in the same order.
    
    Attributes:
    -----------
    aligner (tta.aligner.Aligner):
        The aligner object
    core_cx (bool):
        other_hit contains only tokens from the core context of hit.
        Default is False.
    cnc (concordance.Concordance):
        Concordance to merge into
    other_cnc (concordance.Concordance):
        Concordance to merge from.
    threshold (int):
        The threshold to pass to the aligner. Default is 20 (aligner default).
    ratio (float):
        The minimum similarity ratio. Default is .95 (i.e. basically identical).
    hit_end_token (string):
        A dummy token used to mark the end of each original hit in other_cnc.
        Used to segment the texts before calling the aligner. Actual hit
        divisions in other_cnc are still ignored. Default is '', i.e. no
        hit_end_tokens.
    
    Methods:
    --------
    merge(self, cnc, other_cnc):
        Modifies the concordance cnc by adding data from concordance
        other_cnc.
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Merger.__init__(self)
        self.aligner = None
        self.core_cx = False
        self.cnc, self.other_cnc = None, None
        self.threshold, self.ratio = 20, .95
        self.hit_end_token = ''
        self._cnc_map, self._other_cnc_map = [], []
        self._cnc_list, self._other_cnc_list = [], []
        
    def _build_maps(self, cnc_chunk, other_cnc_chunk):
        # Builds (other_)cnc_map and (other_)cnc_list objects
        # First, reset the maps, in case we're calling this multiple times
        # - _list attributes are (ix, token) tuples, where ix is the 
        #         cumulative index of the token in the chunk, ignoring
        #         hit boundaries.
        # - _map attributes are (hit_ix, tok_ix) tuples for every token
        #         in the chunk. The index of the tuple in _map corresponds
        #         to the "a_id" attribute that the aligner uses and to
        #         the "ix" in _list.
        self._cnc_map, self._other_cnc_map = [], []
        self._cnc_list, self._other_cnc_list = [], []
        # Now, turn the concordance into a list of tokens, sensitive to 
        # core_cx setting. Note that for other_cnc, core_cx is always False,
        # the idea being of course that it contains only toks in the core_cx.
        for cnc, l, mp, core_cx in [
            (cnc_chunk, self._cnc_list, self._cnc_map, self.core_cx),
            (other_cnc_chunk, self._other_cnc_list, self._other_cnc_map, False)
        ]:
            # k keeps a running tally of the total number of tokens
            # in previous hits in the concordance if chunk contains
            # multiple hits.
            k = 0
            for j, hit in enumerate(cnc):
                toks = hit.get_tokens(hit.CORE_CX if core_cx else hit.TOKENS)
                # Set the offset if the core context doesn't start at
                # the first token by incrementing k
                if core_cx:
                    offset = hit.get_ix('start', hit.CORE_CX)
                else:
                    offset = 0
                i = 0
                while toks:
                    # Pop the first token.
                    tok = toks.pop(0)
                    # Create l_item
                    l_item = (i + k + offset, tok.form)
                    # Increment i
                    i += 1
                    # If l_item has a form, add it to the list
                    if tok.form:
                        l.append(l_item)
                    else: # Forget about it
                        pass
                # Map must include an entry for every token in the cnc
                # even if running in core context mode.
                mp += [(j, i) for i in range(len(hit))]
                # Increment k by the full length of the hit, not length of
                # toks.
                k += len(hit)
                
    def _align(self):
        # Sets up and runs the aligner. cnc_list and other_cnc_list must be set.
        self.aligner = tta.aligner.Aligner(
            self._cnc_list, self._other_cnc_list,
            threshold=self.threshold,
            ratio=self.ratio
        )
        if self.hit_end_token:
            # Switches off two-pass parsing for short sequences.
            self.aligner.sequence_matcher = tta.aligner.OnePassSequenceMatcher(
                None, self.aligner.a, self.aligner.b, None
            )
        try:
            self.aligner.ratio_check()
        except tta.aligner.AlignerError:
            print('Text A:' + ' '.join([x[1] for x in self._cnc_list[:100]]))
            print('Text B:' + ' '.join([x[1] for x in self._other_cnc_list[:100]]))
            raise
        if self.hit_end_token:
            # Turn off aligner messages if it's being run 1000s of times
            self.aligner.align(verbose=False)
        else:
            self.aligner.align(verbose=True)
        
    def _chunk(self, cnc):
        # Splits a concordance into chunks using self.hit_end_token
        chunks, hit = [], Hit()
        while cnc:
            l = cnc.pop(0)
            for tok in l:
                if str(tok) == self.hit_end_token:
                    chunks.append(hit)
                    hit = Hit()
                else:
                    hit.append(tok)
        return chunks
        
    def _merge_chunk(self, cnc_chunk, other_cnc_chunk):
        
        def get_hit_tok_from_address(cnc_chunk, address, offset=0):
            hit = cnc_chunk[address[0]]
            tok = hit[address[1] + offset]
            return hit, tok
        
        def get_toks_from_span(hit, tok, span, core_cx):
            l = hit.get_following_tokens(
                tok, hit.CORE_CX if core_cx else hit.TOKENS
            )[:span - 1]
            l.insert(0, tok)
            return l
        
        self._build_maps(cnc_chunk, other_cnc_chunk)
        self._align()
        # The .aligned attribute of the aligner is a list of tuples:
        # - First item: token in main text
        # - Second item: list of matching tokens in second text
        # - Third item: comments on mismatches (which we're going to ignore here).
        # As we inject, so we retokenize in case of different spans.
        # cnc_address_offset corrects the indices in the _maps.
        cnc_address_offset = 0
        last_cnc_hit = None
        for cnc_ix, other_cnc_ixs, x in self.aligner.aligned:
            ###########################################################
            # CALCULATE CNC_TOKS
            ###########################################################
            # Get hit and tok from original concordance
            cnc_hit, cnc_tok = get_hit_tok_from_address(
                cnc_chunk, self._cnc_map[cnc_ix], offset=cnc_address_offset
            )
            # Reset the address offset if we've changed hits
            if not cnc_hit == last_cnc_hit:
                cnc_address_offset = 0
                last_cnc_hit = cnc_hit
            # Calculate span
            cnc_tok_span = cnc_hit.get_form_span(cnc_tok)
            # If span > 1, we need to get all cnc_toks
            if cnc_tok_span > 1:
                cnc_toks = get_toks_from_span(
                    cnc_hit, cnc_tok, cnc_tok_span,
                    core_cx = self.core_cx
                )
            # If span == 1 (0 is not an option; will not have been
            # passed to aligner): it's just cnc_tok
            else:
                cnc_toks = [cnc_tok]
            ###########################################################
            # CALCULATE OTHER_CNC_TOKS
            ###########################################################
            # If there are between one and three matching tokens: get them
            if 0 < len(other_cnc_ixs) < 4:
                # Get other_cnc_address of first token
                other_cnc_address = self._other_cnc_map[other_cnc_ixs[0]]
                # Get hit and tok from other concordance
                other_cnc_hit, other_cnc_tok = get_hit_tok_from_address(
                    other_cnc_chunk, other_cnc_address
                )
                # **Calculate span**
                if len(other_cnc_ixs) == 1:
                # If only one matched, we need its span
                    other_cnc_tok_span = other_cnc_hit.get_form_span(other_cnc_tok)
                # With multiple matches, the span is equal to the no. of matches
                else:
                    other_cnc_tok_span = len(other_cnc_ixs)
                # **Calculate other_cnc_toks**
                if other_cnc_tok_span > 1:
                    other_cnc_toks = get_toks_from_span(
                        other_cnc_hit, other_cnc_tok, other_cnc_tok_span,
                        core_cx = False
                    )
                else:
                    other_cnc_toks = [other_cnc_tok]
            else:
                other_cnc_toks = []
            ############################################################
            # RECALCULATE CNC_TOKS BY RETOKENIZING TO GET A MATCH
            ############################################################
            if len(other_cnc_toks) > len(cnc_toks) and len(cnc_toks) == 1:
                cnc_toks = cnc_hit.split_token(cnc_toks[0], len(other_cnc_toks))
                cnc_address_offset += len(cnc_toks) - 1
            else:
                # Do nothing
                pass
            ###########################################################
            # UPDATE TAGS
            ###########################################################
            if len(cnc_toks) == len(other_cnc_toks) == 1:
                # Most common case, just update dictionary, no looping
                cnc_toks[0].tags.update(other_cnc_toks[0].tags)
            elif len(cnc_toks) == len(other_cnc_toks):
                for cnc_tok, other_cnc_tok in zip(cnc_toks, other_cnc_toks):
                    cnc_tok.tags.update(other_cnc_tok.tags)
                    # Update data only for multiple matches
                    cnc_tok.data = other_cnc_tok.data
            else: # Unequal nos of tokens; do nothing
                pass
        return cnc_chunk
        
    def merge(self):
        """
        Modifies the concordance self.cnc by adding token-level data only from
        concordance self.other_cnc.
        
        Parameters:
        
        Returns:
            merge(self):
                A modified cnc concordance.
        """
        other_cnc_chunks = self._chunk(self.other_cnc)
        if len(other_cnc_chunks) != len(self.cnc):
            # Not the same number of hits; can't use chunking. Run on
            # whole concordance
            print('WARNING! not the same number of hits: {} and {}'. format(len(self.cnc), len(other_cnc_chunks)))
            self.cnc = self._merge_chunk(self.cnc, self.other_cnc)
        else:
            for i, hit in enumerate(self.cnc):
                other_cnc_chunk = other_cnc_chunks.pop(0)
                cnc_chunk = self._merge_chunk([hit], [other_cnc_chunk])
                # Update the hit in self.cnc
                self.cnc[i] = cnc_chunk[0]
        return self.cnc
        
class ConcordanceMerger(Merger):
    """
    Class used to merge two concordance.Concordance objects. Matching
    hits are identified using hit.uuid, hit.ref or order of hits and this
    may be specified using the uuid, ref and order parameters of the concordance.
    The default settings modify the concordance minimally by updating the
    hit.tags dictionary only.
    
    Attributes:
    -----------
    add_hits (bool):
        Adds hits to the concordance from the merging concordance. Default
        is True.
    del_hits (bool):
        Delete hits from the concordance which aren't found in the merging
        concordance. Uses UUIDs and therefore only applies where use_uuid is
        set to True. Default is False.
    match_by (str):
        A string telling the merger how to match hits. Possible values
        are 'uuid', 'ref' and 'refandtext'. If the value is an empty
        string (default), it assumes the two concordances contain the
        same hits in the same order (i.e. list index).
    update_tags (bool):
        Update values already present in hit.tags with new values from the
        merging concordance. Default is False.
    token_merger (mergers.TokenMerger) :
        Provides a TokenMerger to add token-level data from other_cnc to cnc.
        If None provided, tokens are left unchanged. Default is None.
    cnc (concordance.Concordance):
        Concordance to merge into
    other_cnc (concordance.Concordance):
        Concordance to merge from.
    
    Methods:
    --------
    check_settings(self):
        Performs a sanity check on the merger parameters and prints a 
        warning if something is not compatible.
    match_hit(self, cnc, other_hit):
        Finds the hit in cnc which corresponds to other_hit. Returns
        None if nothing can be found.
    merge(self, cnc, other_cnc):
        Modifies the concordance cnc by adding data from concordance
        other_cnc.
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Merger.__init__(self)
        self.add_hits, self.del_hits = False, False
        self.update_tags = False
        self.match_by = ''
        self.token_merger = None
        
    def check_settings(self):
        """
        Performs a sanity check on the merger parameters and prints a 
        warning if something is not compatible.
        """
        if self.del_hits and not self.match_by in ['uuid', 'ref']:
            print("WARNING: Merger not set to match by UUID or REF. Hits will not be deleted.")
        
    def match_hit(self, other_hit, ix):
        """
        Finds the hit in cnc which corresponds to other_hit. Returns
        None if nothing can be found.
        
        Parameters:
            other_hit (concordance.Hit):        The hit to be matched.
            ix (int):                           The index of other_hit.
            
        Returns:
            match_hit(self, other_hit):
                The corresponding hit in self.cnc, or None if not found.
        """
        if self.match_by == 'uuid':
            # Calculate cnc_uuids only once and store in merger.
            if not hasattr(self, '_cnc_uuids'): self._cnc_uuids = self.cnc.get_uuids()
            l = self._cnc_uuids
            return self.cnc[l.index(other_hit.uuid)] if other_hit.uuid in l else None
        if self.match_by in ['ref', 'refandtext']:
            # Calculate refs only once and store.
            if not hasattr(self, '_cnc_refs'): self._cnc_refs = self.cnc.get_refs()
            # Count number of matching references
            n = self._cnc_refs.count(other_hit.ref)
        if self.match_by == 'ref':
            # If there are any matching refs, return the final one.
            # Why?
            # Because we don't check other_cnc for duplicate refs. So
            # in a one-to-many merge, we'll merge the final hit from
            # other_cnc rather than complaining about duplicates.
            # If there are duplicate REFs, we shouldn't be using this
            # method.
            if n > 0:
                # To get the index of the LAST occurrence, we reverse
                # the list, use index() to return the FIRST occurrence,
                # and then express this as a negative index.
                # I.e. index 0 in the reversed list is index -1 in the
                # normal list, index 1 is index -2, etc.
                return self.cnc[
                    -1 - list(reversed(self._cnc_refs)).index(other_hit.ref)
                ]
            else:
                # no matches
                return None
        if self.match_by == 'refandtext':
            #l = self._cnc_refs
            #matches = list(filter(lambda x: x[0] == other_hit.ref, l))
            if self._cnc_refs.count(other_hit.ref):
                # At least one matching reference. Now check KW.
                # 1. Get possible_hits
                possible_hit_ixs = [i for i, x in enumerate(self._cnc_refs) if x == other_hit.ref]
                possible_hits = [self.cnc[i] for i in possible_hit_ixs]
                # 2. Check the keywords if there are keywords in both hits.
                if other_hit.kws and possible_hits[0].kws:
                    possible_hits = match_by_kw(possible_hits, other_hit)
                    # Return None if kw matching failed.
                    if not possible_hits: return None
                # 3. Check the text.
                possible_hits = match_by_text(possible_hits, other_hit)
                # If we're left with just one hit, use that
                if len(possible_hits) == 1:
                    return possible_hits[0]
                # Nothing matches despite matching references, or 
                # multiple matches that we can't disambiguate. In
                # either case, matching has failed.
                else:
                    return None
            else:
                # No matching references; return None
                return None
        # Assume match by list index
        return self.cnc[ix] if ix < len(self.cnc) else None

    def merge(self):
        """
        Modifies the concordance self.cnc by adding data from concordance
        self.other_cnc.
        
        Parameters:
        
        Returns:
            merge(self):
                A modified cnc concordance.
        """
        self.check_settings()
        # Optimization: if we're matching by position in list, just use a 
        # stack to prevent endless calls to self.match_hit.
        for i, other_hit in enumerate(self.other_cnc):
            # Here a counter for very large merges
            if len(self.other_cnc) > 10000 and i // 10000 == i / 10000 and i > 0:
                print('Merging hit {} of {}'.format(str(i), str(len(self.other_cnc))))
            hit = self.match_hit(other_hit, i)
            if not hit:
                if self.add_hits:
                    self.cnc.append(other_hit)
                continue
            if self.update_tags:
                hit.tags.update(other_hit.tags)
            else:
                # i.e. only add new tags, so take a copy and perform 2 updates.
                d = hit.tags.copy()
                hit.tags.update(other_hit.tags)
                hit.tags.update(d)
            # Call the token_merger, if one is given.
            if self.token_merger:
                hit = self.token_merger.merge(hit, other_hit)
        # MUST check use_uuid because if the cncs use different UUIDs it will
        # delete every hit in the first cnc.
        if self.del_hits and self.match_by == 'uuid':
            # Debug code
            #s1 = set(self.cnc.get_uuids())
            #s2 = set(self.other_cnc.get_uuids())
            #print('Deleting UUIDS...')
            #print(list(s1 - s2))
            l = self.other_cnc.get_uuids()
            self.cnc = Concordance(list(
                filter(lambda x: x.uuid in l, self.cnc)
            ))
        if self.del_hits and self.match_by == 'ref':
            l = self.other_cnc.get_refs()
            self.cnc = Concordance(list(
                filter(lambda x: x.ref in l, self.cnc)
            ))
        return self.cnc
        
class TokenMerger():
    """
    Class used to align the tokens and merge the attributes in corresponding
    Hits.
    
    Attributes:
    -----------
    core_cx (bool):
        other_hit contains only tokens from the core context of hit.
        Default is False.
    id_tag (str):
        Tag containing ID for the token. Must be unique within the hit.
        Default is ''.
    update_tags (bool):
        Update values already present in tok.tags with new values from the
        merging hit. Default is False.
    
    Methods:
    --------
    match_token(self, hit, other_tok):
        Finds the tok in hit which corresponds to other_tok. Returns
        None if nothing can be found.
    merge(self, hit, other_hit):
        Modifies the Hit hit by adding data from Hit other_hit.
    """
    
    def __init__(self, core_cx=False):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.id_tag = ''
        self.update_tags = False
        self.core_cx = False
        
    def match_token(self, hit, other_tok, ix):
        """
        Finds the tok in hit which corresponds to other_tok. Returns
        None if nothing can be found.
        
        Parameters:
            hit (concordance.Hit):          The Hit to be modified.
            other_tok (concordance.Hit):    The token to be matched.
            ix (int):                       The index of other_tok.
        
        Returns:
            match_token(self, hit, other_tok, ix):
                The corresponding tok in hit, or None if not found.
        """
        # Extract the core context of hit if running in core context mode
        # otherwise use all the tokens.
        toks = hit.get_tokens(hit.CORE_CX if self.core_cx else hit.TOKENS)
        # Use id_tag if one is set, and return None if there's no matching ID.
        if self.id_tag and self.id_tag in other_tok.tags:
            other_id = other_tok.tags[self.id_tag]
            l = list(filter(lambda x: x.tags.get(self.id_tag) == other_id, toks))
            return l[0] if l else None
        # Otherwise, use the index
        return toks[ix] if ix < len(hit) else None

        
    def merge(self, hit, other_hit):
        """
        Modifies the Hit hit by adding data from Hit other_hit.
        
        Parameters:
        hit (concordance.Hit):          The hit to be modified.
        other_hit (concordance.Hit):    The hit containing the new data.
        
        Returns:
            merge(self, hit, other_hit):
                A concordance.Hit object combining data from hit and other_hit.
        """
        for i, other_tok in enumerate(other_hit):
            tok = self.match_token(hit, other_tok, i)
            if not tok:
                # Token can't be matched: ignore it (no modification of tokens
                # allowed).
                continue
            if self.update_tags:
                tok.tags.update(other_tok.tags)
            else:
                # i.e. only add new tags, so take a copy and perform 2 updates.
                d = tok.tags.copy()
                tok.tags.update(other_tok.tags)
                tok.tags.update(d)
        return hit
            
def match_by_kw(hits, other_hit):
    """
    Tries to disambiguate hits with an identical ref by using the
    KEYWORD. If one text has no keywords, it 
    
    Parameters:
        hits:                List of hits which could match other_hit
        other_hit:           Single hit
        
    Returns:
        match_by_kw(hits, other_hit):
            A list of possible matches.
    """
    l = []
    other_kw = other_hit.to_string(other_hit.KEYWORDS)
    for hit in hits:
        kw = hit.to_string(hit.KEYWORDS)
        if kw == other_kw or not kw or not other_kw:
            l.append(hit)
    return l
    
def match_by_text(hits, other_hit):
    """
    Tries to disambiguate hits with an identical ref by using the
    TOKEN string, trimming the context.
    
    Parameters:
        hits:                List of hits which could match other_hit
        other_hit:           Single hit
        
    Returns:
        match_by_text(hits, other_hit):
            A list of possible matches.
    """
    
    # 1. Get the text from the other_hit.
    other_text = other_hit.to_string(other_hit.TOKENS)
    # 2. Iterate over possible matches and check against text.
    l = []
    for hit in hits:
        hit_text = hit.to_string(hit.TOKENS)
        # 3. Calculate difference in length of text
        a, b = len(hit_text), len(other_text)
        diff = a - b
        # The amount of text to be *removed* from each side of the 
        # LONGEST hit is either
        #   - (i) the absolute value of the difference in length (so double what's necessary)
        #   - (ii) or half of the difference in length between the longest hit and one-third
        #          of the length of the shortest hit, so that at least one-third of the
        #          shortest hit remains
        # whichever value is SMALLER (delete as little as necessary)
        k = min(
            abs(diff),
            (max(a, b) - (min(a, b) // 3)) // 2,
        )
        # Positive diff means possible_hit_text is longer and must be trimmed,
        # and vice versa.
        if (diff >= 0 and other_text.find(hit_text[k:-k]) != -1) \
        or (diff < 0 and hit_text.find(other_text[k:-k]) != -1):
            l.append(hit)
    return l

