#!/usr/bin/python3

import collections

class Concordance(collections.UserList):
    """
    Class to store a concordance.
    
    Core data: a List of instances of Hits.
    
    Attributes:
    -----------
    
    Methods:
    --------
    
    """
    
    pass

    
class Hit(collections.UserList):
    """
    Class to store a single hit in a Concordance.
    
    Core data: a List of instances of Tokens.
    
    Attributes:
    -----------
    
    kwix : int
        index of the token containing the keyword.
        
    Methods:
    --------
    
    """
    
    def __init__(self, l, ix = 0):
        """
        Constructs all attributes needed for an instance of the class (kwix).
        
            Parameters:
                l (list): A list of tokens.
                ix (int): The index of the hit token.
        """
        collections.UserList.__init__(self, l)
        self.ix = ix

    
class Token(collections.UserString):
    """
    Class to store a single Token.
    
    Core data: a String containing the form of the token.
    
    Attributes:
    -----------
    
    tags : dict
        Annotation attached to the token.
        
    Methods:
    --------
    
    """
    
    def __init__(self, s):
        """
        Constructs all attributes needed for an instance of the class (tags).
        
            Parameters:
                s (str): String representing the token.
        """
        collections.UserString.__init__(self, s)
        self.tags = {}
    
    