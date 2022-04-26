#!/usr/bin/python3

import collections, pickle

class Error(Exception):
    """
    Parent class for errors defined in this module.
    """
    pass

class LoadError(Error):
    """
    Error raised when loading a pickled concordance fails.
    """
    pass

class Concordance(collections.UserList):
    """
    Class to store a concordance.
    
    Core data: a List of instances of Hits.
    
    Attributes:
    -----------
    
    Methods:
    --------
    
    save(self, path):
        Saves the concordance to path using pickle (binary).
    
    """
    
    def __init__(self, l = []):
        """
        Constructs all attributes needed for an instance of the class.
        
                l (list): A list of hits
        """
        l = [make_hit(item) for item in l]
        collections.UserList.__init__(self, l)
    
    # UserList methods modified to ensure that make_hit is run on
    # all modifications to the concordance.
    
    def __setitem__(self, i, item):
        item = make_hit(item)
        collections.UserList.__setitem__(self, i, item)
        
    def append(self, item):
        item = make_hit(item)
        collections.UserList.append(self, item)
    
    def insert(self, i, item):
        item = make_hit(item)
        collections.UserList.insert(self, i, item)
        
    # UserList methods modified to ensure that make_concordance is run on
    # all additions to the concordance
    
    def __add__(self, other):
        other = make_concordance(other)
        collections.UserList.__add__(self, other)
        
    def __radd__(self, other):
        other = make_concordance(other)
        collections.UserList.__radd__(self, other)
        
    def __iadd__(self, other):
        other = make_concordance(other)
        collections.UserList.__iadd__(self, other)
        
    def extend(self, other):
        other = make_concordance(other)
        collections.UserList.extend(self, other)
        
    # Other methods
    def save(self, path):
        """
        Saves the concordance to path using pickle (binary).
        
        Parameters:
            path (str): Path to file where object should be saved.
        """
        with open(path, 'wb') as f:
            pickle.dump(self, f)
    
class Hit(collections.UserList):
    """
    Class to store a single hit in a Concordance.
    
    Core data: a List of instances of Tokens.
    
    Attributes:
    -----------
    
    kw : (fromix, toix)
        Tuple containing the fromix and toix of the keyword tokens.
        
    meta (dict) :
        Metadata extracted from self.ref.
        
    ref (str) :
        String representing the reference (original corpus format).
        
    Methods:
    --------
    
    """
    
    def __init__(self, l = [], kw = (0, 0)):
        """
        Constructs all attributes needed for an instance of the class (kwix).
        
            Parameters:
                l (list): A list of tokens.
                ix (int): The index of the hit token.
        """
        l = [make_token(s) for s in l]
        collections.UserList.__init__(self, l)
        self.kw = kw
        self.meta, self.ref = {}, ''
        
    # UserList methods modified to ensure that make_token is run on
    # all modifications to the hit.
    
    def __setitem__(self, i, item):
        item = make_token(item)
        collections.UserList.__setitem__(self, i, item)
        
    def append(self, item):
        item = make_token(item)
        collections.UserList.append(self, item)
    
    def insert(self, i, item):
        item = make_token(item)
        collections.UserList.insert(self, i, item)
        
    # UserList methods modified to ensure that make_hit is run on
    # all addition to the hit
    
    def __add__(self, other):
        other = make_hit(other)
        collections.UserList.__add__(self, other)
        
    def __radd__(self, other):
        other = make_hit(other)
        collections.UserList.__radd__(self, other)
        
    def __iadd__(self, other):
        other = make_hit(other)
        collections.UserList.__iadd__(self, other)
        
    def extend(self, other):
        other = make_hit(other)
        collections.UserList.extend(self, other)

        
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
    
def load_concordance(path):
    """
    Function to load a concordance from a file. Uses pickle.
    
    Parameters:
        path (str): Path to object containing the concordance.
        
    Returns:
        load_concordance(path): A concordance object.
    """
    with open(path, 'rb') as f:
        cnc = pickle.load(f)
    if not isinstance(cnc, Concordance):
        raise LoadError('File does not contain a concordance.')
    return cnc

def make_concordance(l):
    """
    Function to convert a list or list-like object into a valid Concordance
    instance.
    
    Parameters:
        l (list): A list of hits.
        
    Returns:
        make_concordance(l):
            An instance of the Concordance class.
    """
    if isinstance(l, Concordance): return l
    cnc = Concordance(l)
    return cnc

def make_hit(l, kw = (0, 0)):
    """
    Function to convert a list or list-like object into a valid Hit instance.
    
    Parameters:
        l (list): A list of tokens.
        kw (fromix, toix): A tuple containing the fromix and the toix of the 
            keyword tokens.
        
    Returns:
        make_hit(l, kw):
            An instance of the Hit class.
    """
    if isinstance(l, Hit): return l
    hit = Hit(l, kw)
    return hit
    
def make_token(s):
    """
    Function to convert a list or list-like object into a valid Hit instance.
    
    Parameters:
        s (str): A string
        
    Returns:
        make_token(s):
            An instance of the Token class.
    """
    if isinstance(s, Token): return s
    tok = Token(s)
    return tok