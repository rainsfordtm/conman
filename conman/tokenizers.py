#!/usr/bin/python3

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
          'Tokenizer':  Tokenizer
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
    
        
