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
    
    Constants:
    ----------
    Token constants (tok_constant): 
        TOKENS, LCX, RCX, TOKENS. 
            Used to specify which tokens should be return by methods in the class.
    
    Attributes:
    -----------
    
    kws (list) :
        List of the keyword tokens.
        
    tags (dict) :
        Dictionary containing further annotation (e.g. metadata).
        
    ref (str) :
        String representing the reference (original corpus format).
        
    Methods:
    --------
    
    format_token(self, [tok_fmt, [kw_fmt]]):
        Returns a string representation of tok formatted according to 
        the tok_fmt and kw_fmt format strings.
    
    get_tokens(tok_constant):
        Returns the specified tokens as a list.

    is_kw(tok) :
        Returns True or False depending on whether the Token instance is a
        keyword or not. Raises TypeError if tok is NOT a Token instance
        (The class uses exact object equivalence.)
        
    to_string(self, [tok_constant, [delimiter, [tok_fmt, [kw_fmt]]]]) 
        Return a list of some or all of the tokens in the hit as a string
        formatted according to the arguments passed.
        
    """
    
    TOKENS = 0
    LCX = 1
    RCX = 2
    KEYWORDS = 3
    
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
        self.tags, self.ref = {}, ''
        
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
    
    def get_tokens(self, tok_constant = 0):
        """
        Returns the specified tokens as a list.
        
        Parameters:
            tok_constant:   A tok_constant specifying which tokens to return.
            
        Returns:
            get_tokens(self, tok_constant):
                A list of tokens
        """
        if tok_constant == self.TOKENS:
            return [tok for tok in self.data]
        if tok_constant == self.KEYWORDS:
            return [tok for tok in self.kws]
        if not self.kws:
            # No context possible if there are no keywords
            return []
        if tok_constant == self.LCX:
            l = []
            toks = self.data[:]
            tok = toks.pop(0)
            while not self.is_kw(tok):
                l.append(tok)
                tok = toks.pop(0)
            return l
        if tok_constant == self.RCX:
            l = []
            toks = self.data[:]
            tok = toks.pop(-1)
            while not self.is_kw(tok):
                l.append(tok)
                tok = toks.pop(-1)
            l.reverse()
            return l
        return []
    
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
        
    def format_token(self, tok, tok_fmt = '{0}', kw_fmt = '{0}'):
        """
        Returns a string representation of tok formatted according to 
        the tok_fmt and kw_fmt format strings.
        
        Parameters:
            tok (concordance.Token):    a token
            tok_fmt (str):                  Format string giving arguments of token to print
            kw_fmt (str):                   Format string giving special formatting of keyword
            
        Returns:
            format_token(self, [tok_fmt, [kw_fmt]]):
                A string representing the token.
        """
        if self.is_kw(tok):
            return kw_fmt.format(tok)
        else:
            return tok_fmt.format(tok)
            
        
    def to_string(self, 
            tok_constant = 0,
            delimiter = ' ', 
            tok_fmt = '{0}',
            kw_fmt = '{0}'):
        """
        Return a string representing some or all of the tokens in the hit as a string
        formatted according to the arguments passed.
        
        Parameters:
            
        tok_constant (tok_constant):    Constant specifying which tokens to print
        delimiter (str):                String used to delimit the tokens
        tok_fmt (str):                  Format string giving arguments of token to print
        kw_fmt (str):                   Format string giving special formatting of keyword
        
        Returns:
            to_string(self, [tok_constant, pdelimiter, [tok_fmt, [kw_fmt]]]):
                A string representing the token.
        """
        toks = self.get_tokens(tok_constant)
        l = [self.format_token(tok, tok_fmt, kw_fmt) for tok in toks]
        return delimiter.join(l)
        
class Token(collections.UserString):
    """
    Class to store a single Token.
    
    Core data: a String containing the form of the token.
    
    Attributes:
    -----------
    
    tags : dict
        Annotation attached to the token.
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
   