#!/usr/bin/python3

class ConcordanceMerger():
    """
    Class used to merge two concordance.Concordance objects. Matching
    hits are identified using hit.uuid > hit.ref > order of hits in this 
    order of priority; one or more of these may be enabled or disabled by
    setting the use_uuid, use_ref and use_order parameters of the concordance.
    The default settings modify the concordance minimally by updating the
    hit.tags dictionary only.
    
    Attributes:
    -----------
    add_hits (bool):
        Adds hits to the concordance from the merging concordance. Default
        is False.
    del_hits (bool):
        Delete hits from the concordance which aren't found in the merging
        concordance. Default is False.
    update_tags (bool):
        Update values already present in hit.tags with new values from the
        merging concordance. Default is True.
    use_uuid (bool):
        Use hit.uuid to identify identical hits. Default is True.
    use_ref (bool):
        Use hit.ref to identify identical hits. Default is True.
    use_order (bool):
        Use the order of the hits in the concordance to identify identical
        rows. Default is True.
    token_merger (mergers.TokenMerger) :
        Provides a TokenMerger to add token-level data from other_cnc to cnc.
        If None provided, tokens are left unchanged. Default is None.
    
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
        self.add_hits, self.del_hits = False, False
        self.update_tags = True
        self.use_uuid, self.use_ref, self.use_order = True, True, True
        self.token_merger = None
        
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
        return cnc
        