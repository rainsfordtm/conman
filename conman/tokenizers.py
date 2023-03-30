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
          'BfmTokenizer': BfmTokenizer,
          'FrantextTokenizer': FrantextTokenizer
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
            r = '[^_]+_' * parts + "[^_\s'(]*[^_\s'(),.!´][(']?|[,.)!]|,!|,´"
        else:
            # Used if one token does not contain an underscore, i.e. 
            # underscores (probably) aren't special characters.
            # Necessary because there are occasional tokens containing
            # spaces in the BFM :-(
            r = "[^\s'(]*[^\s'(),.!]'?|[,.()!]|,!"
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
                # everything preceding next w/s considered to be 
                # a token
                toks.append(s.split(' ', maxsplit=1)[0])
                s = s[s.index(' ') + 1:] if ' ' in s else ''
            else:
                toks.append(m.group(0))
            s = s[len(toks[-1]):].lstrip() # remove whitespace
        return toks

class FrantextTokenizer(Tokenizer):
    """
    Tokenizes forms outputted from Frantext (slash divided form/pos pairs).
    
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
        # Tokenizing from FRANTEXT would be straightforward except that
        # tokens and lemmas can contain whitespace, which is really annoying.
        # The Tokenizer makes *all* w/s into token delimiters.
        
        # Step 0: sanity check: if s is an empty string or contains only
        # whitespace, return an empty list
        if not s or s.isspace(): return []
        # Step 1: Identify how many slashes each token contains. We assume,
        # with all due caution, that slash itself is always a special character
        l = re.split(r'\s+', s)
        l = remove_empty(l)
        parts_per_tok = [len(re.findall(r'/', x)) for x in l]
        parts_per_tok.sort()
        parts = parts_per_tok[len(parts_per_tok) // 2] # Median (more or less)
        regex = re.compile(r'[^\s/]+/' * parts + r'[^\s/]+')
        # Step 2: Iterate over the whitespace delimited tokens in s and try to
        # attach all slash-less tokens to an appropriate token with slashes,
        # assuming that (i) lemmas with spaces are more common than tokens with
        # spaces and (ii) tokens with spaces contain at most the same number of
        # spaces as their lemmas.
        toks = []
        strays_left, strays_right = [], []
        for grp in l:
            m = regex.match(grp)
            if m:
                # First, deal with strays
                if strays_right:
                    # we have a match but singletons preceded it
                    if strays_left:
                        # singletons preceded the *last* match. All strays added
                        # to both sides of the last match.
                        toks[-1] = '_'.join(strays_left) + '_' + toks[-1] + '_' + '_'.join(strays_right)
                        strays_left, strays_right = [], []
                    else:
                        # no singletons preceded the last match; strays are now
                        # tagged as preceding this match
                        strays_left = strays_right
                        strays_right = []
                elif strays_left:
                    # nothing preceded this match, but something preceded the
                    # *last* match. Logic: the strays did not belong to the
                    # last match, so add to end of second-to-last token.
                    if len(toks) > 1:
                        toks[-2] += '_' + '_'.join(strays_left)
                    else:
                        toks[-1] = '_'.join(strays_left) + '_' + toks[-1]
                    strays_left = []
                # Strays dealt with, now append matched token
                toks.append(grp)
            else: # no match, this is a stray
                strays_right.append(grp)
        # Any strays at the end of the string: attach to the last token
        if strays_right:
            toks[-1] += '_' + '_'.join(strays_right)
        return toks

        

                    
            
        
    
        
        

                    
            
        
    
        
