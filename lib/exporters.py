#!/usr/bin/python3

class Exporter():
    """
    Parent Class to export a concordance. Defines core methods for Child classes.
    
    Attributes:
    -----------
    concordance (concordance.Concordance): The concordance to be exported.
    
    Methods:
    --------
    """
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.concordance = None

class ConllExporter(Exporter):
    """
    Exports the concordance to a Conll file.
    
    Attributes:
    -----------
    
    lemma (str)    : key in tok.tags whose value should be mapped to the LEMMA column
    cpostag (str)  : key in tok.tags whose value should be mapped to the CPOSTAG column
    postag (str)   : key in tok.tags whose value should be mapped to the POSTAG column
    head (str)     : key in tok.tags whose value should be mapped to the HEAD column
    deprel (str)   : key in tok.tags whose value should be mapped to the DEPREL column
    phead (str)    : key in tok.tags whose value should be mapped to the PHEAD column
    pdeprel (str)  : key in tok.tags whose value should be mapped to the PDEPREL column
    
    Methods:
    --------
    export(self, cnc, path): Exports concordance cnc as a Conll file.
    
    hit_to_string(self, hit): 
       Returns a string representing the Conll table for the hit.   
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Exporter.__init__(self)
        self.lemma = 'conll_LEMMA'
        self.cpostag = 'conll_CPOSTAG'
        self.postag = 'conll_POSTAG'
        self.head = 'conll_HEAD'
        self.deprel = 'conll_DEPREL'
        self.phead = 'conll_PHEAD'
        self.pdeprel = 'conll_PDEPREL'
   
    
    def export(self, cnc, path):
        """
        Exports a concordance as a Conll file suitable for dependency parsing.
        
        Parameters:
            cnc (concordance.Concordance): A concordance.
            path (str)                   : Path for Conll file.
        """
        with open(path, 'w', encoding='utf-8') as f:
            for hit in cnc:
                f.write(self.hit_to_string(hit))
                f.write('\n')
    
    def hit_to_string(self, hit):
        """
        Converts each hit to Conll table.
        
        Parameters:
            hit (concordance.Hit)   : a Hit object
            
        Return:
            hit_to_string(self, hit):
                Returns a string representing the Conll table for the hit.
        """
        s = ''
        for ix, tok in enumerate(hit):
            s += '\t'.join(self.tok_to_list(tok, ix + 1))
            s += '\n'
        return s
        
    def tok_to_list(self, tok, ix):
        """
        Converts each token to a 10 item list compatible with the CoNLL-X
        format.
        
        Parameters:
            tok (concordance.Token) : a Token object
            ix : 
            
        Return:
            tok_to_list(self, tok):
                A ten item list representing the columns in a CoNLL-X table.
        """
        
        # The ten columns are:
        # 1. ID (from 1 to n, given by ix)
        # 2. form (str(tok))
        # 3. lemma (tok.tags[self.lemma] or '_')
        # 4. cpostag (tok.tags[self.cpostag] or '_')
        # 5. postag (tok.tags[self.postag] or '_')
        # 6. feats (self.get_feats(tok))
        # 7. head (tok.tags[self.head] or 0)
        # 8. deprel (tok.tags[self.deprel] or 'ROOT')
        # 9. phead (tok.tags[self.phead] or '_')
        # 10. pdeprel (tok.tags[self.pdeprel] or '_')
        
        pass
            
        
        

