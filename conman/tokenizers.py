#!/usr/bin/python3

import re

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

class Tokenizer():
    """
    Parent class used to tokenize strings in hits. Divides by whitespace.
    
    Attributes:
    -----------
    
    Methods:
    --------
    
    tokenize(self, s):
        Tokenizes s, returning a list of tokens.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def create(cls, tokenizer_type):
        """
        Creates an instance of tokenizer_type and returns it.
        """
        
        TOKENIZER_TYPE_TO_CLASS_MAP = {
          'Tokenizer':  Tokenizer,
          'BfmTokenizer': BfmTokenizer
        }
        if tokenizer_type not in TOKENIZER_TYPE_TO_CLASS_MAP:
              raise ValueError('Bad tokenizer type {}'.format(tokenizer_type))
        return TOKENIZER_TYPE_TO_CLASS_MAP[tokenizer_type]()
    
    def tokenize(self, s):
        """
        Tokenizes s, returning a list of tokens.
    
        Parameters:
            s (str) : String containing tokens
        
        Return:
            tokenize(self, s):
              A list of tokens
        """
        return s.split(' ')
        
class BfmTokenizer(Tokenizer):
    """
    Tokenizes forms outputted from the BFM.
    
    Attributes:
    -----------
    
    Methods:
    --------
    
    tokenize(self, s):
        Tokenizes s, returning a list of tokens.
    """
    
    def tokenize(self, s):
        """
        Tokenizes s, returning a list of tokens.
    
        Parameters:
            s (str) : String containing tokens
        
        Return:
            tokenize(self, s):
              A list of tokens
        """
        def remove_empty(l):
            while '' in l:
                l.remove('')
            return l
        # Tokenizing from the BFM is hard because whitespace is occasionally
        # suppressed, but tags can also be added.
        # Step 1: All whitespace is always a token boundary, so split here
        l = re.split(r'\s+', s)
        l = remove_empty(l)
        # Step 2: Work out how many underscores the token should contain
        parts_per_tok = [len(re.findall(r'_', x)) for x in l]
        parts = min(parts_per_tok) # The minimum number of underscores in a token
        # Step 3: Generate regex to identify a token
        r = '[^_\s]+_' * parts + "[^_\s']*[^_\s',\.]'?|[,\.]"
        regex = re.compile(r)
        # Step 4: Tokenize
        toks = []
        s = s.lstrip().rstrip() # Strip trailing and preceding whitespace.
        while s:
            m = regex.match(s)
            if not m:
                raise ParseError("Can't parse '{}' with '{}'".format(s, r))
            toks.append(m.group(0))
            s = s[len(toks[-1]):].lstrip() # remove whitespace
        return toks

        

                    
            
        
    
        
