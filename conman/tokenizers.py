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
    
        
