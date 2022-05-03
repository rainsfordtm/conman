#!/usr/bin/python3

import csv

class Exporter():
    """
    Most basic of all exporters that simply prints each hit in the concordance
    on each line. Token appearance can be controlled by kw_fmt, tok_fmt,
    and tok_delimiter.
    
    Attributes:
    -----------

    kw_fmt(str):
        Format string used to format each keyword. Takes a single positional
        argument, which is evaluated as a token instance. Default is '',
        which is evaluated as 'use tok_fmt'.
        
    tok_delimiter (str):
        String used to delimit the tokens. Default is ' '.
        
    tok_fmt (str):
        Format string used to represent each token. Takes a single positional
        argument, which is evaluated as a token instance. Default is '{0}',
        i.e. just the token as a string.
        
    Methods:
    --------
    
    export(self, cnc, path, [encoding]):
        Exports concordance cnc to path, one token per line.
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.kw_fmt = ''
        self.tok_fmt = '{0}'
        self.tok_delimiter = ' '
        
    def export(self, cnc, path, encoding = 'utf-8'):
        """
        Exports concordance cnc to path in a tabular format.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
            encoding (str):                 Character encoding
        """
        with open(path, 'w' encoding=encoding) as f:
            for hit in cnc:
                f.write(hit.to_string(
                    hit.TOKENS,
                    delimiter='\n',
                    tok_fmt=self.tok_fmt,
                    kw_fmt=self.kw_fmt))
                f.write('\n')

class TableExporter(Exporter):
    """
    Class to export a concordance in some kind of tabular form as 
    a text file. Defines core methods for Child classes. 
    Default methods produce an Excel-style CSV file with one hit per line
    as a KWIC concordance.
    
    Constants:
    ----------
    SPECIAL_FIELDS (list):
        List of fieldnames reserved for fields not stored
        in the tags dictionary of the hit.
    
    Attributes:
    -----------
    dialect (str):
        Dialect to use for the CSV writer. Options are:
            'excel':    Comma-separated, quote with " only when necessary.
            'tab'  :    Tab-separated, no quoting or escaping.
            
    header (bool):
        Write a header row if set to True. Default is True.
        
    fields (list):
        List of fields to export in the order in which the columns should be
        represented in the file. Fields are looked up by default in the
        .tags dictionary of the hit, but the HitExporter.SPECIAL_FIELDS are
        reserved values:
        
        Hits:
        -----
        KEYWORDS:   Keyword tokens only
        LCX:        Tokens preceding keywords only
        RCX:        Tokens following keywords only
        REF:        hit.ref
        TOKENS:     All tokens

        
    Methods:
    --------
    
    hit_to_list(self, hit):
        Converts a hit to a list ready for export.
    
    export(self, path, [encoding]):
        Exports concordance cnc to path in a tabular format.
    
    """
    
    SPECIAL_FIELDS = ['KEYWORDS', 'LCX', 'RCX', 'TOKENS', 'REF']
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Exporter.__init__(self)
        self.concordance = None
        self.header = True
        self.dialect = 'excel'
        self.fields = ['REF', 'LCX', 'KEYWORDS', 'RCX']
        csv.register_dialect(
            'tab',
            delimiter='\t',
            quoting=csv.QUOTE_NONE
            )
        
    def export(self, cnc, path, encoding = 'utf-8'):
        """
        Exports concordance cnc to path in a tabular format.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
            encoding (str):                 Character encoding
        """
        with open(path, 'w', encoding=encoding, newline='') as f:
            writer = csv.writer(f, dialect=self.dialect)
            if self.header:
                writer.writerow(self.fields)
            for hit in cnc:
                writer.writerow(self.hit_to_list(hit))
                
    def hit_to_list(self, hit):
        """
        Converts a hit to a list ready for export.
        
        Parameters:
            hit (concordance.Hit):  The hit to be exported
            
        Returns:
            hit_to_list(self, hit):
                A list of the fields in the hit.
        """
        l = []
        for field in self.fields:
            if field in self.SPECIAL_FIELDS:
                # 1. Token printing fields.
                for special_field, tok_constant in [
                    ('KEYWORDS', hit.KEYWORDS),
                    ('LCX', hit.LCX),
                    ('RCX', hit.RCX),
                    ('TOKENS', hit.TOKENS)
                ]:
                    if field == special_field:
                        l.append(hit.to_string(
                            delimiter = self.tok_delimiter,
                            tok_constant = tok_constant,
                            tok_fmt = self.tok_fmt,
                            kw_fmt = self.kw_fmt or self.tok_fmt
                        ))
                # 2. Check for the REF field
                if field == 'REF':
                    l.append(hit.ref)
            # 3. Otherwise, use self.tags
            else:
                l.append(hit.tags[field] if field in hit.tags else '')
        return l
        
class ConllExporter():
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
            tok.tags[self.deprel] if self.deprel in tok.tags else 'ROOT', # 8. deprel
            tok.tags[self.phead] if self.phead in tok.tags else '_',  # 9. phead
            tok.tags[self.pdeprel] if self.pdeprel in tok.tags else '_',  # 10. pdeprel
        ]
       
