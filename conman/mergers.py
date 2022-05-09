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
            cnc (concordance.Concordance):      The concordance to be modified
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
                self.token_merger.merge(hit, other_hit)
        # MUST check use_uuid because if the cncs use different UUIDs it will
        # delete every hit in the first cnc.
        if self.del_hits and self.match_by == 'uuid':
            l = other_cnc.get_uuids()
            cnc = Concordance(list(
                filter(lambda x: x.uuid in l, cnc)
            ))
        return cnc
        