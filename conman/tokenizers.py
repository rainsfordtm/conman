#!/usr/bin/python3

import re

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
        split = [' '] # Split at these characters, no regex
        split_after_regex = [re.compile(r".*'$")]
        split_before_regex = [re.compile(x) for x in [r'\.\s+.*', r',\s+.*']]
        l, buff = [], ''
        while s:
            char = s.pop(0)
            if char in split and buff:
                # split at single character, ignore the character
                l.append(buff)
                buff, char = '', ''
            if buff:
                for regex in split_after_regex:
                    if regex.match(buff): # buffer is a token, store the char.
                        l.append(buff)
                        buff = char
                        char = ''
                        break # out of for loop
                for regex in split_before_regex:
                    if regex.match(s): # string to come matches regex
                        buff += char
                        l.append(buff)
                        buff, char = '', ''
            if char: # char not dealt with above
                buff += char
        if buff:
            l.append(buff)
        return l
                    
            
        
    
        
