#!/usr/bin/python3

from conman.concordance import Concordance
import tta.aligner

class TokenListMerger():
    """
    Class used to merge two concordance.Concordance objects at the level of
    the Token rather than at the level of the Hit, i.e. it ignores the Hits
    in other_cnc. The two concordances must contain (more or less) the same
    tokens in the same order.
    
    Attributes:
    -----------
    aligner (tta.aligner.Aligner):
        The aligner object
    cnc (concordance.Concordance):
        Concordance to merge into
    other_cnc (concordance.Concordance):
        Concordance to merge from.
        
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
        self.aligner = None
        self.cnc, self.other_cnc = None, None
        self._cnc_map, self._other_cnc_map = [], []
        self._cnc_list, self._other_cnc_list = [], []
        
    def _build_maps(self):
        # Builds (other_)cnc_map and (other_)cnc_list objects
        # First, turn the concordance into a list of tokens.
        for cnc, l, mp in [
            (self.cnc, self._cnc_list, self._cnc_map),
            (self.other_cnc, self._other_cnc_list, self._other_cnc_map)
        ]:
            k = 0
            for j, hit in enumerate(cnc):
                l += [(i + k, str(tok)) for i, tok in enumerate(hit)]
                mp += [(j, i) for i in range(len(hit))]
                k += len(hit)
                
    def _align(self):
        # Sets up and runs the aligner. cnc_list and other_cnc_list must be set.
        self.aligner = tta.aligner.Aligner(self._cnc_list, self._other_cnc_list)
        self.aligner.align()
        
    def merge(self):
        """
        Modifies the concordance self.cnc by adding token-level data only from
        concordance self.other_cnc.
        
        Parameters:
        
        Returns:
            merge(self):
                A modified cnc concordance.
        """
        self._build_maps()
        self._align()
        # The .aligned attribute of the aligner is a list of tuples:
        # - First item: token in main text
        # - Second item: list of matching tokens in second text
        # - Third item: comments on mismatches (which we're going to ignore here).
        for cnc_ix, other_cnc_ixs, x in self.aligner.aligned:
            if other_cnc_ixs: # matches some token in text b
                cnc_address = self._cnc_map[cnc_ix]
                other_cnc_address = self._other_cnc_map[other_cnc_ixs[0]]
                self.cnc[cnc_address[0]][cnc_address[1]].tags.update(
                    self.other_cnc[other_cnc_address[0]][other_cnc_address[1]].tags
                )
        return self.cnc

class ConcordanceMerger():
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
        is False.
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
        self.add_hits, self.del_hits = False, False
        self.update_tags = False
        self.match_by = ''
        self.token_merger = None
        self.cnc, self.other_cnc = None, None
        
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
            l = self.cnc.get_uuids()
            return self.cnc[l.index(other_hit.uuid)] if other_hit.uuid in l else None
        if self.match_by == 'ref':
            l = [hit.ref for hit in self.cnc]
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
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        # self.aligner = None # DISABLED
        self.id_tag = ''
        self.update_tags = False
        
    #########################################################################
    # Private methods needed to implement the aligner
    #########################################################################
        
    def _initialize_aligner(self, hit, other_hit):
        # Re-run the aligner ensuring that the ID is the index of each
        # token in the hit. Otherwise match_token doesn't work.
        self.aligner.a_list = [(i, tok) for i, tok in enumerate(hit)]
        self.aligner.b_list = [(i, tok) for i, tok in enumerate(other_hit)]
        self.aligner.threshold = 3 # Short matches, lower threshold for pass1
        try:
            self.aligner.align()
        except:
            print(self.aligner.a_list)
            print(self.aligner.b_list)
            print(self.aligner.aligned)
        
    def _match_token_aligner(self, hit, other_tok, ix):
        # Uses the aligner to find the token.
        if not self.aligner.aligned:
            self.aligner.align()
        for alignment in self.aligner.aligned:
            if ix in alignment[1]:
                return hit[alignment[0]]
        return None
        
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
        # Use id_tag if one is set, and return None if there's no matching ID.
        if self.id_tag and self.id_tag in other_tok.tags:
            other_id = other_tok.tags[self.id_tag]
            l = list(filter(lambda x: x.tags.get(self.id_tag) == other_id, hit))
            return l[0] if l else None
        # Otherwise, use aligner if one is set. DISABLED
        # if self.aligner:
        #    return self._match_token_aligner(hit, other_tok, ix)
        # Otherwise, use the index
        return hit[ix] if ix < len(hit) else None
        
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
        # if self.aligner:
        #     self._initialize_aligner(hit, other_hit) DISABLED
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
            
        
    


        