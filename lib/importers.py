#!/usr/bin/python3

from lib.concordance.Concordance import *

class Importer():
    """
    Parent Class to build a concordance. Defines core methods for Child classes  
    
    Attributes:
    -----------
    concordance (concordance.Concordance):
        Concordance object
    
    Methods:
    --------
    
    add_hit(l, ix):
        Adds a hit to the Concordance.
    
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.concordance = new Concordance([])
    
    def add_hit(self, l, ix = 0):
        """
        Adds a hit to the Concordance.
        
            Parameters:
                l (list) : A list of strings or Tokens.
                ix (index) : The index of the hit Token.
        """
        
        l = to_tokens(l)
        self.concordance.append(Hit(l, ix))
        
    def to_tokens(self, l):
        """
        Converts a list of strings to Tokens.
        
            Parameters:
                l (list) : A list of strings or Tokens.
                
            Returns:
                self.to_tokens(l): A list of Tokens.
        """
        for tok in l:
            
                
        
       
        
    
           

