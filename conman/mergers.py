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
        self._cnc_map, self._other_cnc_map = [], []
        self._cnc_list, self._other_cnc_list = [], []
        # Now, turn the concordance into a list of tokens, sensitive to 
        # core_cx setting. Note that for other_cnc, core_cx is always False,
        # the idea being of course that it contains only toks in the core_cx.
        for cnc, l, mp, core_cx in [
            (cnc_chunk, self._cnc_list, self._cnc_map, self.core_cx),
            (other_cnc_chunk, self._other_cnc_list, self._other_cnc_map, False)
        ]:
            k = 0
            for j, hit in enumerate(cnc):
                toks = hit.get_tokens(hit.CORE_CX if core_cx else hit.TOKENS)
                # Set the offset if the core context doesn't start at
                # the first token by incrementing k
                if core_cx:
                    offset = hit.get_ix('start', hit.CORE_CX)
                else:
                    offset = 0
                l += [(i + k + offset, str(tok)) for i, tok in enumerate(toks)]
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
        self._build_maps(cnc_chunk, other_cnc_chunk)
        self._align()
        # The .aligned attribute of the aligner is a list of tuples:
        # - First item: token in main text
        # - Second item: list of matching tokens in second text
        # - Third item: comments on mismatches (which we're going to ignore here).
        for cnc_ix, other_cnc_ixs, x in self.aligner.aligned:
            if other_cnc_ixs: # matches some token in text b
                cnc_address = self._cnc_map[cnc_ix]
                other_cnc_address = self._other_cnc_map[other_cnc_ixs[0]]
                cnc_chunk[cnc_address[0]][cnc_address[1]].tags.update(
                    other_cnc_chunk[other_cnc_address[0]][other_cnc_address[1]].tags
                )
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
        A string telling the merger how to match hits. The only possible values
        are 'uuid' and 'ref'. If empty string (default), assumes list index.
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
        if self.del_hits and not self.match_by == 'uuid':
            print("WARNING: Merger not set to match by UUID. Hits will not be deleted.")
        
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
        if self.match_by == 'ref': 
            # Calculate refs only once and store.
            if not hasattr(self, '_cnc_refs'): self._cnc_refs = [hit.ref for hit in self.cnc]
            l = self._cnc_refs
            matches = list(filter(lambda x: x[0] == other_hit.ref, l))
            if len(matches) == 1:
                # One matching reference
                return self.cnc[matches[0][1]]
            else:
                # None or more than one matching reference; return None
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
            
