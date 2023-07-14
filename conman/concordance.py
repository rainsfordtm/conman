#!/usr/bin/python3

import collections, pickle, os.path, gzip
from uuid import UUID, uuid4

# This global variable is available in the whole of conman for identifying
# valid path extensions for a concordance.
CONCORDANCE_EXTS = ['.cnc']

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

class UUIDError(Error):
    """
    Error raised when converting to a UUID fails.
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
    
    get_uuids(self):
        Returns a list of UUIDs for all the Hits in the concordance in the
        order in which they are currently stored.

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
    # all modifications to the concordance and that the .concordance attribute
    # is set.
    
    def __setitem__(self, i, item):
        item = make_hit(item)
        item.concordance = self
        collections.UserList.__setitem__(self, i, item)
        
    def append(self, item):
        item = make_hit(item)
        item.concordance = self
        collections.UserList.append(self, item)
    
    def insert(self, i, item):
        item = make_hit(item)
        item.concordance = self
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
    def get_uuids(self):
        """
        Returns a list of UUIDs for all the Hits in the concordance in the
        order in which they are currently stored.
        
        Returns:
            get_uuids(self):
                List of UUIDs in the order that they currently appear.
        """
        return [hit.uuid for hit in self.data]

    
    def save(self, path):
        """
        Saves the concordance to path using pickle (binary).
        
        Parameters:
            path (str): Path to file where object should be saved.
        """
        path_splitext = os.path.splitext(path)
        if path_splitext[1] in CONCORDANCE_EXTS or \
        (path_splitext[1] == '.gz' and os.path.splitext(path_splitext[0])[1] in CONCORDANCE_EXTS):
            # Path is OK
            pass
        else:
            path += CONCORDANCE_EXTS[0]
        open_fnc = gzip.open if os.path.splitext(path)[1] == '.gz' else open
        with open_fnc(path, 'wb') as f:
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
    
    concordance (concordance.Concordance):
        Pointer to the concordance in which the hit is contained. Default is
        None.
        
    core_cx (list) :
        List of tokens forming part of the core context of the keyword.
        The core context includes the keywords and immediately surrounding
        context; its precise extent is determined by the script used in the
        CoreContextAnnotator which creates it.
        
    kws (list) :
        List of the keyword tokens.
        
    tags (dict) :
        Dictionary containing further annotation (e.g. metadata).
        
    ref (str) :
        String representing the reference (original corpus format).
        
    Properties:
    -----------
    
    uuid (uuid.UUID):
        Unique ID.
        
    Methods:
    --------
    
    format_token(self, [tok_fmt, [kw_fmt]]):
        Returns a string representation of tok formatted according to 
        the tok_fmt and kw_fmt format strings.
        
    get_ix(sf, tok_constant):
        Returns the start and end indices of the subset of tokens
        specified by tok_constant within the hit.
        
    get_following_tokens(tok, [tok_constant]):
        Returns a list of all tokens following tok. tok_constant
        specifies the context (core_cx, all tokens, etc.).
        
    get_preceding_tokens(tok, [tok_constant]):
        Returns a list of all preceding tokens. tok_constant
        specifies the context (core_cx, all tokens, etc.).
    
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
    CORE_CX = 4
    
    def __init__(self, l = [], kws = [], uuid = None):
        """
        Constructs all attributes needed for an instance of the class.
        
            Parameters:
                l (list):           A list of tokens.
                kws (list):         List of the keyword tokens.
                uuid :              A UUID object or something than can be
                                    used to initialize one.
        """
        l = [make_token(s) for s in l]
        collections.UserList.__init__(self, l)
        self.kws = kws
        self.core_cx = []
        self.concordance, self.tags, self.ref = None, {}, ''
        self._uuid = make_uuid(uuid) if uuid else uuid4()
        
    # Properties
    @property
    def uuid(self):
        return self._uuid
        
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
    
    def get_following_tokens(self, tok, tok_constant = 0):
        """
        Returns a list of all tokens following tok.
        
        Parameters:
            tok:    A token in the hit
            
        Returns:
            get_following(tok):
                A list of tokens.
        """
        return self._get_sublist(tok, tok_constant, backwards=False)
        
    def get_preceding_tokens(self, tok, tok_constant = 0):
        """
        Returns a list of all tokens preceding tok.
        
        Parameters:
            tok:    A token in the hit
            
        Returns:
            get_preceding(tok):
                A list of tokens.
        """
        return self._get_sublist(tok, tok_constant, backwards=True)
        
    def _get_sublist(self, the_tok, tok_constant, backwards=False):
        # Called by get_following_tokens or get_preceding_tokens
        # 1. Get the tokens
        toks = self.get_tokens(tok_constant)
        # 2. Reverse list if finding preceding tokens
        if backwards: toks.reverse()
        # 3. Pop first token
        tok = toks.pop(0)
        # 4. Scan the list until the_tok is found.
        while toks and not tok is the_tok: tok = toks.pop(0)
        # 5. If no toks (because tok is not found, or was the first or the last)
        # return an empty list
        if not toks: return []
        # 6. Otherwise reverse toks if we've been searching backwards
        if backwards: toks.reverse()
        # 7. Return toks
        return toks
    
    def get_ix(self, sf, tok_constant=0):
        """
        Returns the start and end indices of the subset of tokens
        specified by tok_constant within the hit.
        
        Parameters:
            tok_constant:   A tok_constant specifying which token list to return.
            sf (str):       Either 'start' or 'end'
            
        Returns:
            get_ix(sf, tok_constant)
                The index of the give context within the hit.
        """
        toks = self.get_tokens(tok_constant)
        if sf == 'start':
            tok_a = toks[0]
        elif sf == 'end':
            tok_a = toks[-1]
        else:
            raise Error('sf must be "start" or "end"')
        for i, tok_b in enumerate(self.data):
            if tok_a is tok_b: return i
    
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
        if tok_constant == self.CORE_CX:
            return [tok for tok in self.core_cx]
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
            try:
                return kw_fmt.format(tok)
            except:
                #print(tok.tags)
                return str(tok)
        else:
            try:
                return tok_fmt.format(tok)
            except:
                return str(tok)
                
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
    open_fnc = gzip.open if os.path.splitext(path)[1] == '.gz' else open
    with open_fnc(path, 'rb') as f:
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
    
def make_uuid(uuid):
    """
    Function to convert the passed argument to a uuid.UUID object if possible.
    Otherwise returns TypeError.
    
    Parameters:
        uuid (uuid.UUID or str or bytes or 6-tuple or int) :
            A object which can initialize a UUID.
    
    Returns:
        make_uuid(uuid):
            A uuid.UUID object
    """
    # Case 1: it's a uuid.UUID already
    if isinstance(uuid, UUID): return uuid
    # Case 2: it's a string
    if isinstance(uuid, str):
        try:
            return UUID(uuid)
        except:
            raise UUIDError('Cannot convert str "{}" to UUID'.format(uuid))
    # Case 3: it's an integer
    if isinstance(uuid, int):
        try:
            return UUID(int=uuid)
        except:
            raise UUIDError('Cannot convert int "{}" to UUID'.format(str(uuid)))
    # Case 4: it's a six-tuple (i.e. the fields argument)
    if isinstance(uuid, tuple):
        try:
            return UUID(fields=uuid)
        except:
            raise UUIDError('Cannot convert tuple "{}" to UUID'.format(str(uuid)))
    # Case 5: it's a bytes object
    if isinstance(uuid, bytes):
        try:
            return UUID(bytes=uuid)
        except:
            raise UUIDError('Cannot convert bytes "{}" to UUID'.format(str(uuid)))
    # Case 6: it's not a recognized type, raise TypeError
    raise TypeError('Type {} not supported by concordance.make_uuid'.format(type(uuid)))

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
   
