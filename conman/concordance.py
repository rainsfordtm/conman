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
    
    kws (list) :
        List of the keyword tokens.
        
    meta (dict) :
        Metadata extracted from self.ref.
        
    ref (str) :
        String representing the reference (original corpus format).
        
    Methods:
    --------
    
    is_kw(tok) :
        Returns True or False depending on whether the Token instance is a
        keyword or not. Raises TypeError if tok is NOT a Token instance
        (The class uses exact object equivalence.) 
    """
    
    def __init__(self, l = [], kws = []):
        """
        Constructs all attributes needed for an instance of the class.
        
            Parameters:
                l (list): A list of tokens.
                kws (list): List of the keyword tokens.
        """
        l = [make_token(s) for s in l]
        collections.UserList.__init__(self, l)
        self.kws = kws
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
        self.update_ids(i, 'insert', 1)
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
        
    # Other methods
    
    def is_kw(self, tok):
        """
        Returns True or False depending on whether the Token instance is a
        keyword or not. Raises TypeError if tok is NOT a Token instance
        (The class uses exact object equivalence.)
        
        Parameters:
            tok (concordance.Token) : A token instance
            
        Returns:
            is_kw(self, tok):
                True is tok is a keyword, False if tok is not a keyword.
                TypeError if tok is not a concordance.Token.
        """
        if not isinstance(tok, Token):
            raise TypeError('concordance.Token expect, {} received.',format(type(tok)))
        for kw in self.kws:
            if kw is tok: return True
        return False
        
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

def make_hit(l, kws = []):
    """
    Function to convert a list or list-like object into a valid Hit instance.
    
    Parameters:
        l (list): A list of tokens.
        kws (list): List of the keyword tokens.
        
    Returns:
        make_hit(l, kws):
            An instance of the Hit class.
    """
    if isinstance(l, Hit): return l
    hit = Hit(l, kws)
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
   