#!/usr/bin/python3

import csv, os.path

class Error(Exception):
    """
    Parent class for errors defined in this module.
    """
    pass

class ExportError(Error):
    """
    Raised where some aspect of the export fails.
    """
    pass

class Exporter():
    """
    Most basic of all exporters that simply prints each hit in the concordance
    on each line. Token appearance can be controlled by kw_fmt, tok_fmt,
    and tok_delimiter.
    
    Attributes:
    -----------
    encoding (str):
        Name of codec to use to write the exported file. Default is utf-8.
        
    core_cx (bool):
        If True, exports only the keywords and the core context surrounding
        each Hit. Core context must first be identified by running a 
        CoreContextAnnotator, otherwise this will trigger an ExportError.
        Default is False.

    kw_fmt(str):
        Format string used to format each keyword. Takes a single positional
        argument, which is evaluated as a token instance. Default is '{0}'.
        
    split_hits (int):
        Splits the output into smaller files containing maximum split_hits
        hits.
        
    tok_delimiter (str):
        String used to delimit the tokens. Default is ' '.
        
    tok_fmt (str):
        Format string used to represent each token. Takes a single positional
        argument, which is evaluated as a token instance. Default is '{0}',
        i.e. just the token as a string.
        
    Methods:
    --------
    
    export(self, cnc, path):
        Base method for exporting a concordance by calling the 
        exporter-specific _export method, having first split the concordance
        if necessary.
        
    get_tokens(self, hit):
        Returns the tokens in the hit as a list while taking account of the 
        core context setting.
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.encoding = 'utf-8'
        self.kw_fmt = '{0}'
        self.core_cx = False
        self.split_hits = 0
        self.tok_fmt = '{0}'
        self.tok_delimiter = ' '
        self.exts = ['txt', 'csv', 'tsv']
        
    @classmethod
    def create(cls, exporter_type):
        """
        Creates an instance of exporter_type and returns it.
        """
        
        EXPORTER_TYPE_TO_CLASS_MAP = {
          'Exporter':  Exporter,
          'TokenListExporter': TokenListExporter,
          'LGermExporter': LGermExporter,
          'TableExporter': TableExporter,
          'ConllExporter': ConllExporter
        }
        if exporter_type not in EXPORTER_TYPE_TO_CLASS_MAP:
              raise ValueError('Bad exporter type {}'.format(exporter_type))
        return EXPORTER_TYPE_TO_CLASS_MAP[exporter_type]()
        
    def export(self, cnc, path):
        """
        Base method for exporting a concordance by calling the 
        exporter-specific _export method, having first split the concordance
        if necessary.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
            encoding (str):                 Character encoding
        """
        if self.split_hits:
            cncs = self._splitter(cnc)
            split_path = os.path.splitext(path)
            paths = [
                '{}_{}{}'.format(split_path[0], str(i), split_path[1])
                for i in range(len(cncs))
            ]
            for cnc, path in zip(cncs, paths):
                self._export(cnc, path)
        else:
            self._export(cnc, path)
            
    def fix_ext(self, path):
        """
        Ensures that the exporter only saves to a file with an appropriate
        extension as specified in self.exts. If a wrong extension is
        found, used the first entry in self.exts.
        
        Parameters:
            path (str):                     File name
            
        Returns:
            self.fix_ext(path)
                A file name with an appropriate extension.
        """
        name, ext = os.path.splitext(path)
        if not ext or not ext[1:] in self.exts:
            return name + '.' + self.exts[0]
        else:
            return path
            
    def get_tokens(self, hit):
        """
        Returns the tokens in the hit relevant for the export, taking account
        of core context setting. Raises ExportError if nothing found.
        
        Parameters:
            hit (concordance.Hit):  Hit to export
            
        Returns:
            List of tokens. 
        """
        l = hit.get_tokens(hit.CORE_CX if self.core_cx else hit.TOKENS)
        if not l:
            raise ExportError(
                'Nothing to export. Check core context settings\n.' + \
                'Hit: ' + hit.to_string(hit.TOKENS)
            )
        return l
            
    def _export(self, cnc, path):
        """
        Exports concordance cnc to path in a tabular format.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
            encoding (str):                 Character encoding
        """
        with open(path, 'w', encoding=self.encoding, errors='replace') as f:
            for hit in cnc:
                s = hit.to_string(
                    hit.CORE_CX if self.core_cx else hit.TOKENS,
                    delimiter=self.tok_delimiter,
                    tok_fmt=self.tok_fmt,
                    kw_fmt=self.kw_fmt
                )
                if not s:
                    raise ExportError(
                        'Nothing to export. Check core context settings\n.' + \
                        'Hit: ' + hit.to_string(hit.TOKENS)
                    )
                f.write(s + '\n')
                
    def _splitter(self, cnc):
        """
        Method to split the concordance into a list of a concordances containing
        max self.split_hits hits.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            
        Returns:
            _splitter(self, cnc):
                A list of concordance containing max self._split_hits hits.
        """
        if not self.split_hits: return [cnc]
        l = []
        for i in range((len(cnc) // self.split_hits) + 1):
            start_ix = i * self.split_hits
            end_ix = min((i + 1) * self.split_hits, len(cnc))
            l.append(cnc[start_ix:end_ix])
        return l

class TokenListExporter(Exporter):
    """
    Class to export the tokens in a one-token-per-line list format.
    
    Attributes:
    -----------
    hit_end_token (str):
        Character used as a dummy token to delimit the hits (essential).
        Default is '', i.e. an empty line.
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Exporter.__init__(self)
        self.hit_end_token = ''
        self.exts = ['txt', 'tsv']
        
    def _export(self, cnc, path):
        """
        Exports concordance cnc to path in a one-token-per-line format.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
        """
        with open(path, 'w', encoding=self.encoding, errors='replace') as f:
            for hit in cnc:
                s = hit.to_string(
                    hit.CORE_CX if self.core_cx else hit.TOKENS,
                    delimiter='\n',
                    tok_fmt=self.tok_fmt,
                    kw_fmt=self.kw_fmt
                )
                if not s:
                    raise ExportError(
                        'Nothing to export. Check core context settings\n.' + \
                        'Hit: ' + hit.to_string(hit.TOKENS)
                    )
                f.write(s + '\n' + self.hit_end_token + '\n')
                
class LGermExporter(TokenListExporter):
    """
    Subclass of TokenListExporter designed to fix the vagaries of LGerM,
    in particular (i) splitting the export file by default and (ii) 
    removing punctuation which causes it to crash (e.g. "/")
    
    Ignores some global defaults. In particular, 
    """
    
    def __init__(self):
        TokenListExporter.__init__(self)
        self.encoding = 'latin1'
        self.split_hits = 5500
    
    def _export(self, cnc, path):
        """
        Exports concordance cnc to path in a one-token-per-line format,
        ignoring tok_fmt and 
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
        """
        with open(path, 'w', encoding=self.encoding, errors='replace') as f:
            for hit in cnc:
                toks = self.get_tokens(hit)
                for tok in toks:
                    f.write(str(lgermsafe(tok)) + '\n')
                f.write(self.hit_end_token + '\n')

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
        .tags dictionary of the hit, but the TableExporter.SPECIAL_FIELDS are
        reserved values:
        
        Hits:
        -----
        KEYWORDS:   Keyword tokens only
        LCX:        Tokens preceding keywords only
        RCX:        Tokens following keywords only
        REF:        hit.ref
        TOKENS:     All tokens
        UUID:       hit.uuid

        
    Methods:
    --------
    
    hit_to_list(self, hit):
        Converts a hit to a list ready for export.
    
    """
    
    SPECIAL_FIELDS = ['KEYWORDS', 'LCX', 'RCX', 'TOKENS', 'REF', 'UUID']
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Exporter.__init__(self)
        self.concordance = None
        self.header = True
        self.dialect = 'excel'
        self.fields = []
        csv.register_dialect(
            'tab',
            delimiter='\t',
            quoting=csv.QUOTE_NONE
            )
        self.exts = ['csv', 'tsv']
        
    def _set_default_fields(self, cnc):
        # Set the default fields if none have been given at the moment of
        # export.
        # Default name plus all tags in self.tags
        self.fields = ['UUID', 'REF', 'LCX', 'KEYWORDS', 'RCX']
        if not cnc: return # don't look for cnc[0] if the concordance is empty
        for key in cnc[0].tags:
            self.fields.append(key)
        
    def _export(self, cnc, path):
        """
        Exports concordance cnc to path in a tabular format.
        
        Parameters:
            cnc (concordance.Concordance):  Concordance to export
            path (str):                     File name
            encoding (str):                 Character encoding
        """
        if not self.fields: self._set_default_fields(cnc)
        with open(path, 'w', encoding=self.encoding, errors='replace', newline='') as f:
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
                    ('TOKENS', hit.TOKENS),
                    ('CORE_CX', hit.CORE_CX) # not ideal, doesn't split R and L.
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
                # 3. Check for the UUID field
                if field == 'UUID':
                    l.append(hit.uuid)
            # 3. Otherwise, use self.tags
            else:
                l.append(hit.tags[field] if field in hit.tags else '')
        return l
        
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
    hit_end_token (str): Character used as a dummy token to delimit the hits (essential).
                    Default is 'ENDHIT'.
    
    Methods:
    --------
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
        self.hit_end_token = 'ENDHIT'
        self.exts = ['conllu', 'conll', 'txt', 'tsv']
    def _export(self, cnc, path, add_refs = True):
        """
        Exports a concordance as a Conll file suitable for dependency parsing.
        If add_refs is True, adds hit.uuid and hit.ref as comments.
        
        Parameters:
            cnc (concordance.Concordance): A concordance.
            path (str)                   : Path for Conll file.
            add_refs (bool)              : Boolean
        """
        with open(path, 'w', encoding=self.encoding, errors='replace') as f:
            for hit in cnc:
                if add_refs:
                    f.write('# ' + str(hit.uuid) + '\n')
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
        toks = self.get_tokens(hit)
        for ix, tok in enumerate(toks):
            s += '\t'.join(self.tok_to_list(tok, ix + 1))
            s += '\n'
        if self.hit_end_token:
            s += '\t'.join([
                str(ix + 2), #1
                self.hit_end_token, #2
                '_', '_', '_', '_', '0', 'root', '_', '_' 
            ])
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
        # 8. deprel (tok.tags[self.deprel] or 'root')
        # 9. phead (tok.tags[self.phead] or '_')
        # 10. pdeprel (tok.tags[self.pdeprel] or '_')
        
        return [
            str(ix),                                                  # 1. ID
            str(tok),                                                 # 2. form
            tok.tags[self.lemma] if self.lemma in tok.tags else '_',  # 3. lemma
            tok.tags[self.cpostag] if self.cpostag in tok.tags else '_',  # 4. cpostag
            tok.tags[self.postag] if self.postag in tok.tags else '_',  # 5. postag
            self.get_feats(tok) or '_',                                  # 6. feats
            str(tok.tags[self.head]) if self.head in tok.tags else '0',    # 7. head
            tok.tags[self.deprel] if self.deprel in tok.tags else 'root', # 8. deprel
            tok.tags[self.phead] if self.phead in tok.tags else '_',  # 9. phead
            tok.tags[self.pdeprel] if self.pdeprel in tok.tags else '_',  # 10. pdeprel
        ]
       
def get_exporter_from_path(path):
    """
    Function to pick a default exporter from the filename extension.
    Currently implements the following:
    
    .csv    : TableExporter
    .txt    : Exporter
    .conll  : ConllExporter
    .conllu : ConllExporter
    
    All other extensions trigger ParseError.
    
    Parameters:
    path (str) : Path to the output file
    
    Returns:
        get_exporter_from_path(path)
            An Exporter object.
    """
    ext = os.path.splitext(path)[1]
    if ext == '.csv': return TableExporter()
    if ext == '.txt': return Exporter()
    if ext in ['.conll', '.conllu']: return ConllExporter()
    raise ParseError('No default exporter for file extension "{}".'.format(ext))
    
def lgermsafe(s):
    """
    Removes anything from a string which is likely to upset the LGerm lemmatizer.
    """
    s = s.replace('/', '.')
    return s
