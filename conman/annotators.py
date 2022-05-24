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
        annotate(self, cnc, **kwargs):
            Applies the transformations given in self.script to each hit in
            the concordance.
            
        Parameters:
            cnc (conman.concordance.Concordance):
                The concordance to be annotated.
            **kwargs:
                **kwargs to be passed to self.script.
                
        Returns:
            annotate(self, cnc, **kwargs) :
                An updated concordance.
        """
        for i, hit in enumerate(cnc):
            # counter for very large cncs
            if len(cnc) > 10000 and i // 10000 == i / 10000 and i > 0:
                print('Annotating hit {} of {}'.format(str(i), str(len(cnc))))
            hit = self.script(hit, **self.kwargs)
        return cnc
        
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
        