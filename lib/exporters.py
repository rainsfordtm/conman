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
    feats (list)   : list of keys in tok.tags whose values should be mapped to the FEATS column
    
    Methods:
    --------
    export(self, cnc, path, [add_ref]): 
        Exports concordance cnc as a Conll file.
        If add_ref = True (default) add the reference as a comment on the
        preceding line.
    
    get_feats(self, tok):
        Returns a string for the feats column of the Conll table.
        
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
        self.feats = []
    
    def export(self, cnc, path, add_ref = True):
        """
        Exports a concordance as a Conll file suitable for dependency parsing.
        
        Parameters:
            cnc (concordance.Concordance): A concordance.
            path (str)                   : Path for Conll file.
        """
        with open(path, 'w', encoding='utf-8') as f:
            for hit in cnc:
                if add_ref:
                    f.write('# ' + hit.ref + '\n')
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
        
    def get_feats(self, tok):
        """
        Calculates the feats column for the Conll table, using keys in 
        self.feats.
        
        Parameters:
            tok (concordance.Token) : a Token instance
            
        Returns:
            get_feats(self, tok):
                A string suitable for the FEATS column in Conll
        """
        l = []
        for feat in self.feats:
            if feat in tok.tags:
                l.append('{}={}'.format(feat, tok.tags[feat]))
        return '|'.join(l)
        
    def tok_to_list(self, tok, ix):
        """
        Converts each token to a 10 item list compatible with the CoNLL-X
        format.
        
        Parameters:
            tok (concordance.Token) : a Token object
            ix (int)                : value for the ID column
            
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
        
        return [
            str(ix),                                                  # 1. ID
            str(tok),                                                 # 2. form
            tok.tags[self.lemma] if self.lemma in tok.tags else '_',  # 3. lemma
            tok.tags[self.cpostag] if self.cpostag in tok.tags else '_',  # 4. cpostag
            tok.tags[self.postag] if self.postag in tok.tags else '_',  # 5. postag
            self.get_feats(tok),                                      # 6. feats
            tok.tags[self.head] if self.head in tok.tags else '_',    # 7. head
            tok.tags[self.deprel] if self.deprel in tok.tags else '_', # 8. deprel
            tok.tags[self.phead] if self.phead in tok.tags else '_',  # 9. phead
            tok.tags[self.pdeprel] if self.pdeprel in tok.tags else '_',  # 10. pdeprel
        ]
            
        
        

