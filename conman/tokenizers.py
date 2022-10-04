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
        # Step 0: sanity check: if s is an empty string or contains only
        # whitespace, return an empty list
        if not s or s.isspace(): return []
        # Step 1: Identify how many underscores each token contains
        l = re.split(r'\s+', s)
        l = remove_empty(l)
        parts_per_tok = [len(re.findall(r'_', x)) for x in l]
        parts = min(parts_per_tok) # The minimum number of underscores in a token
        # Step 2: Generate regex to identify a token from the number of
        # parts before the underscore plus a sophisticated regex to identify
        # the end of the token.
        if parts > 0:
            # Used if every token contains at least one underscore, i.e.
            # underscores are special characters.
            r = '[^_]+_' * parts + "[^_\s'(]*[^_\s'(),.!][(']?|[,.)!]|,!"
        else:
            # Used if one token does not contain an underscore, i.e. 
            # underscores (probably) aren't special characters.
            # Necessary because there are occasional tokens containing
            # spaces in the BFM :-(
            r = "[^\s'(]*[^\s'(),.!][(']?|[,.)!]|,!"
        regex = re.compile(r)
        # Step 3: Tokenize using re.match on the string.
        toks = []
        s = s.lstrip().rstrip() # Strip trailing and preceding whitespace.
        while s:
            m = regex.match(s)
            if not m: 
                print("Warning: Can't tokenize {}".format(s, r))
                print("Last token: {}".format(toks[-1] if toks else ''))
                # start again from next whitespace or end, if it's the last
                # token.
                s = s[s.index(' ') + 1:] if ' ' in s else ''
            else:
                toks.append(m.group(0))
            s = s[len(toks[-1]):].lstrip() # remove whitespace
        return toks

        

                    
            
        
    
        
