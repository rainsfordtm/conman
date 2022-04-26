#!/usr/bin/python3

from lib.concordance import *
from lib.tokenizers import *
import csv, re

class Error(Exception):
    """
    Parent class for errors defined in this module.
    """
    pass

class ParseError(Error):
    """
    Raised where a parse method fails.
    """
    pass

class Importer():
    """
    Parent Class to build a concordance. Defines core methods for Child classes.  
    
    Attributes:
    -----------
    concordance (concordance.Concordance):
        Concordance object
        
    lcx_fields (list):
        List of tag names exported in the left context of the concordance.
        "word" is used as the base form.
        
    keywds_fields (list):
        List of tag names exported in the keywords column of the concordance.
        "word" is used as the base form.
        
    rcx_fields (list):
        List of tag names exported in the right context of the concordance.
        "word" is used as the base form.
        
    ref_regex (str):
        Regex with named groups used to identify fields in the reference string.
        
    tokenizer (tokenizers.Tokenizer):
        Tokenizer use to parse multi-word fields (typically left- and
        right context).
    
    Methods:
    --------
    
    parse_ref(self, ref):
        Parses the reference field into a dictionary of metadata. Uses the
        regex in self.ref_regex.
        
    tokenize(self, s):
        Uses self.tokenizer to tokenize a multi-word field.
    
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.concordance = Concordance([])
        self.lcx_fields, self.keywds_fields, self.rcx_fields = [], [], []
        self.ref_regex = ''
        self.tokenizer = Tokenizer()
        
    def parse_ref(self, ref):
        """
        Parses a reference string into a dictionary of metadata using the 
        self.ref_regex.
        
        Parameters:
            ref (str):  String containing the reference to parse.
            
        Returns:
            parse_ref(self, ref):
                A dictionary of metadata.
        """
        if not self.ref_regex: return d
        m = re.match(self.ref_regex, ref)
        return m.groupdict()
        
    def tokenize(self, s):
        """
        Calls tokenize method of self.tokenizer to tokenize string s.
    
        Parameters:
            s (str) : String containing tokens
        
        Return:
            tokenize(self, s):
              A list of tokens
        """
        return self.tokenizer.tokenize(s)
        
        
class TXMImporter(Importer):
    """
    Imports a CSV file exported from TXM to build a concordance.  
    
    Additional attributes:
    ----------------------
    
    Methods:
    --------
    
    parse(self, path, encoding = 'utf-8'):
        Parses a CSV file (Four columns, tab separated) exported from TXM.
        
    parse_hit(self, row):
        Parses a row from a TXM CSV file. Returns a Hit object.
        
    parse_token(self, s):
        Parses the tokens in the TXM concordance file, using the underscore
        to split the fields. The tag names must be set by the lcx_fields,
        keywds_fields and rcx_fields attribute of the class.
    
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Importer.__init__(self)
        self.lcx_fields, self.keywds_fields, self.rcx_fields = [], [], []
        
    
    def parse(self, path, encoding = 'utf-8', header = True):
        """
        Parses a CSV file (Four columns, tab separated, header) exported from TXM.
        
        Parameters:
            path (str):     Path to the CSV or text file.
            encoding (str): Text encoding of the CSV or text file.
            header (bool):  True (default) if the first line of the file is
                            a header.
        
        Returns:
            parse(self, path, [encoding, [header]]):
                A concordance object.
        """
        with open(path, 'r', encoding=encoding, newline='') as f:
            # TXM generates a tab delimited file with no quote characters.
            # First line is the header.
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        # Skip the first row if header is True
            if header: x = reader.__next__()
            for row in reader:
                hit = self.parse_hit(row)
                self.concordance.append(hit)
        return self.concordance
        
    def parse_hit(self, row):
        """
        Parses a row from a TXM CSV file. Returns a Hit object.
        
        Parameters:
            row (list):     List with four items (ref, left context, kw, 
                            right context)
            
        Returns:
            parse_hit(self, row):
                A Hit object.
                
        """
        # Tokenization
        lcx_tokenized = self.tokenize(row[1])
        keywds_tokenized = self.tokenize(row[2])
        rcx_tokenized = self.tokenize(row[3])
        # Parse tokens
        lcx = [self.parse_token(item, self.lcx_fields) for item in lcx_tokenized]
        keywds = [self.parse_token(item, self.keywds_fields) for item in keywds_tokenized]
        rcx = [self.parse_token(item, self.rcx_fields) for item in rcx_tokenized]
        # Combine to a list
        l, kw = context_to_list(lcx, keywds, rcx)
        # Create Hit
        hit = Hit(l, kw)
        hit.ref = row[0]
        hit.meta = self.parse_ref(hit.ref)
        return hit
        
    def parse_token(self, s, tagnames):
        """
        Parses a token string from the TXM concordance file, using the underscore
        to split the fields. The tag names must be set by the lcx_fields,
        keywds_fields and rcx_fields attribute of the class.
        
        Parameters:
            s (str):    A string representing a token
            
        Returns:
            parse_token(self, s):
                A Token instance.
        """
        l = s.split('_')
        tok = tags_to_tok(l, tagnames)
        return tok
        
def context_to_list(lcx, keywds, rcx):
    """
    Merges three lists representing the left context, keywords, and
    right context respectively into a single list, returning the fromix
    and the toix of the keywords as a tuple, as required in Hit format.
    
    Parameters:
        lcx (list)      : List containing tokens/strings in the left context
        keywds (list)   : List containing the keywords
        rcx (list)      : List containing tokens/strings in the right context
        
    Returns:
        context_to_list(lcx, keywds, rcx):
            A list, kw tuple which can be used to initialize a Hit object.   
    """
    fromix = len(lcx)
    toix = len(lcx) + len(keywds)
    l = lcx + keywds + rcx
    kw = (fromix, toix)
    return l, kw
    
def tags_to_tok(tags, tagnames = [], word_tag='word'):
    """
    Converts a list of tags to a token using the names in tagnames.
    
    Parameters:
        tags (list)       : List of tags
        tagnames (list)   : List of tagnames to attach to the tags (optional).
                            If no tagnames are given or the length doesn't
                            match 'tag1', 'tag2' etc. will be generated.
        word_tag (str)    : Tag to use for the form of the word.
                            Default is 'word' or the first item, if no 
                            tagnames are given.
        
    Returns:
        tags_to_tok(tags, [tagnames, [word_tag]]):
            A token instance.
    """
    
    def get_tagname():
        nonlocal i
        s = 'tag' + str(i)
        i += 1
        return s
        
    i = 1
    form, tag_d = '', {}
    # If tagnames is NOT passed, use the first tag as the form.
    if not tagnames: form = tags.pop(0)
    # Iterate over tags
    for tag in tags:
        tagname = tagnames.pop(0) if tagnames else get_tagname()
        if tagname == word_tag:
            form = tag
        else:
            tag_d[tagname] = tag
    if not form:
        raise ParseError('Tag "{}" not found in tagnames'.format(word_tag))
    tok = Token(form)
    tok.tags = tag_d
    return tok
    

