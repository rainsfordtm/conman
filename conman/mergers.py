#!/usr/bin/python3

from conman.concordance import Concordance

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
        merging concordance. Default is True.
    token_merger (mergers.TokenMerger) :
        Provides a TokenMerger to add token-level data from other_cnc to cnc.
        If None provided, tokens are left unchanged. Default is None.
    
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
        self.update_tags = True
        self.match_by = ''
        self.token_merger = None
        
    def check_settings(self):
        """
        Performs a sanity check on the merger parameters and prints a 
        warning if something is not compatible.
        """
        if self.del_hits and not self.match_by == 'uuid':
            print("WARNING: Merger not set to match by UUID. Hits will not be deleted.")
        
    def match_hit(self, cnc, other_hit, ix):
        """
        Finds the hit in cnc which corresponds to other_hit. Returns
        None if nothing can be found.
        
        Parameters:
            cnc (concordance.Concordance):      The concordance to be modified.
            other_hit (concordance.Hit):        The hit to be matched.
            ix (int):                           The index of other_hit.
            
        Returns:
            match_hit(self, cnc, other_hit):
                The corresponding hit in self.cnc, or None if not found.
        """
        if self.match_by == 'uuid':
            l = cnc.get_uuids()
            return cnc[l.index(other_hit.uuid)] if other_hit.uuid in l else None
        l = [(hit.ref, i) for i, hit in enumerate(cnc)]
        if self.match_by == 'ref':
            matches = list(filter(lambda x: x[0] == other_hit.ref, l))
            if len(matches) == 0:
                # No matching reference
                return None
            if len(matches) == 1:
                # One matching reference
                return cnc[matches[0][1]]
            if len(matches) > 1:
                # More than one matching reference; reset l so it only contains 
                # matching references
                l = matches
        # Assume match by list index
        matches = list(filter(lambda x: x[1] == ix, l))
        return cnc[matches[0][1]] if matches else None

    def merge(self, cnc, other_cnc):
        """
        Modifies the concordance cnc by adding data from concordance
        other_cnc.
        
        Parameters:
        cnc (concordance.Concordance):          The concordance to be modified.
        other_cnc (concordance.Concordance):    The concord containing the new data.
        
        Returns:
            merge(self, cnc, other_cnc):
                A modified cnc concordance.
        """
        self.check_settings()
        for i, other_hit in enumerate(other_cnc):
            hit = self.match_hit(cnc, other_hit, i)
            if not hit:
                if self.add_hits:
                    cnc.append(other_hit)
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
            l = other_cnc.get_uuids()
            cnc = Concordance(list(
                filter(lambda x: x.uuid in l, cnc)
            ))
        return cnc
        
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
        merging hit. Default is True.
    
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
        self.update_tags = True
        
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
            
        
    


        