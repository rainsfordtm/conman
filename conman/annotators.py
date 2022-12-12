#!/usr/bin/python3

class Annotator():
    """
    Base class used to add annotation to a hit. The class method "script",
    which does nothing by default, can be updated to provide custom 
    annotation.
    
    Class method:
    -------------
    create(cls, annotator_type):  
        Creates an instance of annotator_type and returns it.
    
    Attributes:
    -----------
    kwargs (dict):
        Dictionary of keyword arguments to be passed to script.

    Methods:
    --------
    
    annotate(self, cnc, **kwargs):
        Adds annotation to the concordance using the script function.
        
    annotate_hit(self, hit):
        Run before script on each hit in the concordance.
        
    script(self, hit, **kwargs):
        Returns updated hit.
    """
    
    @classmethod
    def create(cls, annotator_type):
        """
        Creates an instance of annotator_type and returns it.
        """
        
        ANNOTATOR_TYPE_TO_CLASS_MAP = {
          'Annotator':  Annotator,
          'KeywordTagAnnotator': KeywordTagAnnotator
        }
        if annotator_type not in ANNOTATOR_TYPE_TO_CLASS_MAP:
              raise ValueError('Bad annotator type {}'.format(annotator_type))
        return ANNOTATOR_TYPE_TO_CLASS_MAP[annotator_type]()
        
    def __init__(self):
        self.kwargs = {}
    
    def annotate(self, cnc):
        """
        Calls self.annotate_hit on each hit in the concordance.
            
        Parameters:
            cnc (conman.concordance.Concordance):
                The concordance to be annotated.
            **kwargs:
                **kwargs to be passed to self.annotate_hit.
                
        Returns:
            annotate(self, cnc, **kwargs) :
                An updated concordance.
        """
        for i, hit in enumerate(cnc):
            # counter for very large cncs
            if len(cnc) > 10000 and i // 10000 == i / 10000 and i > 0:
                print('Annotating hit {} of {}'.format(str(i), str(len(cnc))))
            hit = self.annotate_hit(hit)
        return cnc
        
    def annotate_hit(self, hit):
        """
        Calls self.script on each hit in the concordance. The default 
        method does nothing else.
        
        Parameters:
            hit (conman.concordance.Hit):
                The Hit to be annotated.
        """
        return self.script(hit, **self.kwargs)
        
    def script(self, hit, **kwargs):
        """
        Default function for Annotator class applies to hit: returns the hit
        unchanged.
        
        Parameters:
            hit (conman.concordance.Hit):
                The hit to be annotated
            **kwargs:
                All further arguments must be keyword arguments.
        """
        return hit
        
class CoreContextAnnotator(Annotator):
    """
    Annotator which populates the CORE_CX list of a hit from the list of 
    tokens returned by the script.
    """
    
    def annotate_hit(self, hit):
        l = self.script(hit, **self.kwargs)
        l = list(l) # in case script has returned a hit object
        hit.core_cx = l
        return hit
        
    def script(self, hit, **kwargs):
        # If no kws, return empty list.
        if not hit.kws: return []
        # Set flag
            core = False
        # Iterate forwards, then backwards over the tokens
        passes = []
        for seq in [hit, reversed(hit)]:
            l = []
            for tok in seq:
                # If tok is a delimiter, set core to False (end of seq)
                if tok in delimiters:
                    # not in core...
                    core = False
                # ...provided it's not a kw, for which core is always True.
                for kw in hit.kws:
                    if kw is tok:
                        core = True
                l.append(core)
            passes.append(l)
        # Reverse the second pass in place
        passes[1].reverse()
        # Merge into a single list of boolean values
        bools = []
        for pass1, pass2 in zip(passes[0], passes[1]):
            bools.append(True) if pass1 or pass2 else l.append(False)
        # Make token list
        l = []
        for tok, val in zip(list(hit), l):
            if val: l.append(tok)
        return l

class KeywordTagAnnotator(Annotator):
    """
    Annotator providing a script method to project tags from the keywords up
    to the level of the hit. 
    """
    
    def script(self, hit, tags=[]):
        # Tags should be a list of (kw_tag, hit_tag) pairs
        for kw_tag, hit_tag in tags:
            l = []
            for kw in hit.kws:
                if kw_tag in kw.tags:
                    l.append(kw.tags[kw_tag])
                else:
                    l.append('')
            try:
                hit.tags[hit_tag] = '_'.join(l)
            except:
                print(hit)
                print(hit.tags)
                print(l)
                print(hit.kws)
                raise
        return hit
        