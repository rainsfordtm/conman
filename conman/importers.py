#!/usr/bin/python3

from conman.concordance import *
from conman.tokenizers import *
import treetools.basetree, treetools.syn_importer, treetools.transformers
import conman.scripts.pennout2cnc
import csv, re

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

class Importer():
    """
    Parent Class to build a concordance. Defines core methods for Child classes.  
    
    Attributes:
    -----------
    concordance (concordance.Concordance):
        Concordance object
        
    lcx_fields (list):
        List of tag names exported in the left context of the concordance.
        "word" is used as the base form.
        
    keywds_fields (list):
        List of tag names exported in the keywords column of the concordance.
        "word" is used as the base form.
        
    rcx_fields (list):
        List of tag names exported in the right context of the concordance.
        "word" is used as the base form.
        
    ref_regex (str):
        Regex with named groups used to identify fields in the reference string.
        
    tokenizer (tokenizers.Tokenizer):
        Tokenizer use to parse multi-word fields (typically left- and
        right context).
    
    Methods:
    --------
    
    parse_ref(self, ref):
        Parses the reference field into a dictionary of metadata. Uses the
        regex in self.ref_regex.
        
    tokenize(self, s):
        Uses self.tokenizer to tokenize a multi-word field.
    
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.concordance = Concordance([])
        self.lcx_fields, self.keywds_fields, self.rcx_fields = [], [], []
        self.ref_regex = ''
        self.tokenizer = Tokenizer()
        
    def parse_ref(self, ref):
        """
        Parses a reference string into a dictionary of metadata using the 
        self.ref_regex.
        
        Parameters:
            ref (str):  String containing the reference to parse.
            
        Returns:
            parse_ref(self, ref):
                A dictionary of metadata.
        """
        if not self.ref_regex: return {}
        m = re.match(self.ref_regex, ref)
        return m.groupdict()
        
    def tokenize(self, s):
        """
        Calls tokenize method of self.tokenizer to tokenize string s.
    
        Parameters:
            s (str) : String containing tokens
        
        Return:
            tokenize(self, s):
              A list of tokens
        """
        return self.tokenizer.tokenize(s)
        
class BaseTreeImporter(Importer):
    """
    Imports a Basetree XML file into a concordance.
    
    Additional attributes:
    ----------------------
    keyword_attr (str):
        Name of attribute on leaf node which specifies whether the node is 
        a keyword or not.
        
    keyword_true_values (list):
        List of values for the node.getAttribute(self.keyword_attr) which should
        be evaluated as "True". Defaults ['yes', 'y', 't', 'true'], not 
        case-sensitive.
    
    Methods:
    --------
    is_keyword(self, elem):
        Returns True if the passed leaf node from a BaseTree is marked as a
        keyword. Uses attribute given in self.keyword_attr and values 
        in self.keyword_true_values. If keyword_attr is not found, returns
        False.
    
    leaf_to_token(self, elem):
        Converts a leaf node from a BaseTree to a concordance.Token object.
    
    parse(self, path):
        Parses a Basetree XML file using treetools.
        
    stree_to_hit(self, stree):
        Converts a treetools.basetree.StringTree object to a concordance.Hit
        object.
        
    """
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Importer.__init__(self)
        self.keyword_attr = ''
        self.keyword_true_values = ['yes', 'y', 't', 'true']
        
    def is_keyword(self, elem):
        """
        Returns True if the passed leaf node from a BaseTree is marked as a
        keyword. Uses attribute given in self.keyword_attr and values 
        in self.keyword_true_values. If keyword_attr is not found, returns
        False.
        
        Parameters:
            elem (xml.dom.minidom.Element) :
                Element node representing a leaf in a BaseTree.
        
        Returns:
            is_keyword(self, elem): True or False
        """
        try:
            s = elem.getAttribute(self.keyword_attr)
        except:
            return False
        if s.lower() in self.keyword_true_values:
            return True
        return False
        
    def leaf_to_token(self, bst, elem):
        """
        Converts a leaf node from a BaseTree to concordance.Token object.
        
        Parameters:
            bst (treetools.basetree.BaseTree) :
                BaseTree containing the leaf node.
            elem (xml.dom.minidom.Element) :
                Element node representing a leaf in a BaseTree.
        
        Returns:
            leaf_to_token(self, elem):
               A concordance.Token node.
        """
        # 1. Get leaf attributes from bst object
        attrs = bst.leaf_attrs[:]
        # 2. Read the form
        tok = Token(elem.getAttribute('value'))
        attrs.remove('value')
        # 3. Store all other attributes as tok.tags
        tok.tags = dict(zip(attrs, [elem.getAttribute(attr) for attr in attrs]))
        # 4. Return Token
        return tok
        
    def parse(self, path):
        """
        Parses a Basetree XML file file using treetools.
        
        Parameters:
            path (str) :        Path to the XML file.
            
        Returns:
            parse(self, path):
                A concordance object.
        """
        forest = treetools.basetree.parse_file(path)
        for stree in forest:
            hit = self.stree_to_hit(stree)
            self.concordance.append(hit)
        return self.concordance
        
    def stree_to_hit(self, stree):
        """
        Converts a treetools.basetree.StringTree object to a concordance.Hit
        object.
        
        Parameters:
            stree (treetools.basetree.StringTree):
                A StringTree containing the hit
            
        Returns:
            stree_to_hit(self, stree):
                A Hit object.
        """
        l, kws = [], []
        bst = stree.to_base_tree()
        bst.restructure(knots = False) # Convert all knots to leaves.
        bst.sort() # Ensures that leaves in the BaseTree are in text order.
        for leaf in bst.leaves:
            l.append(self.leaf_to_token(bst, leaf))
            if self.is_keyword(leaf): kws.append(l[-1])
        hit = Hit(l, kws)
        hit.ref = stree.get_id()
        hit.meta = self.parse_ref(hit.ref)
        return hit
        
class PennOutImporter(BaseTreeImporter):
    """
    Imports a .out file from CorpusSearch containing hits marked in the
    text. Inherits from BaseTreeImporter as it first converts the .out
    file to a BaseTree.
    
    Additional attributes:
    ----------------------
    
    dump_xml (str):
        Path to which the post-transformation XML should be saved (useful
        for checking if the .psd transformer is doing what it's expected to do.)
        If not set, defaults to '' and XML is not saved.

    keyword_node_regex (str):
        Regex used to identify the node number of the keyword node from
        the comment above the tree. The matching node must be identified
        by the named group 'keyword_node'.
        Default is r'[^0-9]*(?P<keyword_node>[0-9]+)[^0-9]+.*', i.e. the first
        number in the comment (typically the dominating IP).
        
    word_lemma_regex (str):
        Regex used to split words from lemmas in the PSD file.
        The regex must include the named groups 'word' and 'lemma'.
        Default is a hyphen, e.g. r'(?P<word>[^\-]*)-(?P<lemma>.*)'
   
    script(transformer, keyword_node_regex=self.keyword_node_regex):
        Function containing instructions used to transform each BaseTree
        from the .out file into the desired format for the BaseTreeImporter,
        i.e. where all relevant information is stored as leaf attributes.
        Should add the attribute in self.keyword_attr to all nodes, with a 
        value matching self.keyword_true_values if the node number matches
        self.keyword_node_regex.
        Default is the 'script' function in conman/scripts/pennout2cnc.py.
        
    Methods:
    --------
    
    parse(self, path, encoding = 'utf-8'):
        Parses a Penn .out file.
   
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        BaseTreeImporter.__init__(self)
        self.dump_xml = ''
        self.keyword_node_regex = r'[^0-9]*(?P<keyword_node>[0-9]+)[^0-9]+.*'
        self.word_lemma_regex = r'(?P<word>[^\-]*)-(?P<lemma>.*)'
        self.script = conman.scripts.pennout2cnc.script
        
    def parse(self, path, encoding = 'utf-8'):
        """
        Parses a Penn .out file.
        
        Parameters:
            path (str) :        Path to the .out file.
            
        Returns:
            parse(self, path):
                A concordance object.
        """
        # 1. Call syn_importer on the .out file. to create a BaseForest.
        forest = treetools.syn_importer.build_forest(path, 'penn-psd-out')
        # 2. Initialize a transformer
        transformer = treetools.transformers.Transformer()
        # 3. Set the script method from self.script
        transformer.script = self.script
        # 4. Transform the forest
        forest = transformer.transform(
            forest,
            keyword_attr = self.keyword_attr,
            keyword_node_regex = self.keyword_node_regex,
            word_lemma_regex = self.word_lemma_regex
            )
        # 5. Add each tree in the forest to the concordance
        for stree in forest:
            hit = self.stree_to_hit(stree)
            self.concordance.append(hit)
        # 6. Dump the XML if a path is set
        if self.dump_xml:
            with open(self.dump_xml, 'w') as f:
                f.write(forest.toxml())
        # 7. Return concordance.s 
        return self.concordance
      
class TXMImporter(Importer):
    """
    Imports a CSV file exported from TXM to build a concordance.  
    
    Additional attributes:
    ----------------------
    
    Methods:
    --------
    
    parse(self, path, encoding = 'utf-8'):
        Parses a CSV file (Four columns, tab separated) exported from TXM.
        
    parse_hit(self, row):
        Parses a row from a TXM CSV file. Returns a Hit object.
        
    parse_token(self, s):
        Parses the tokens in the TXM concordance file, using the underscore
        to split the fields. The tag names must be set by the lcx_fields,
        keywds_fields and rcx_fields attribute of the class.
    
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Importer.__init__(self)
        self.lcx_fields, self.keywds_fields, self.rcx_fields = [], [], []
        
    
    def parse(self, path, encoding = 'utf-8', header = True):
        """
        Parses a CSV file (Four columns, tab separated, header) exported from TXM.
        
        Parameters:
            path (str):     Path to the CSV or text file.
            encoding (str): Text encoding of the CSV or text file.
            header (bool):  True (default) if the first line of the file is
                            a header.
        
        Returns:
            parse(self, path, [encoding, [header]]):
                A concordance object.
        """
        with open(path, 'r', encoding=encoding, newline='') as f:
            # TXM generates a tab delimited file with no quote characters.
            # First line is the header.
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        # Skip the first row if header is True
            if header: x = reader.__next__()
            for row in reader:
                hit = self.parse_hit(row)
                self.concordance.append(hit)
        return self.concordance
        
    def parse_hit(self, row):
        """
        Parses a row from a TXM CSV file. Returns a Hit object.
        
        Parameters:
            row (list):     List with four items (ref, left context, keywords, 
                            right context)
            
        Returns:
            parse_hit(self, row):
                A Hit object.
                
        """
        # Tokenization
        lcx_tokenized = self.tokenize(row[1])
        keywds_tokenized = self.tokenize(row[2])
        rcx_tokenized = self.tokenize(row[3])
        # Parse tokens
        lcx = [self.parse_token(item, self.lcx_fields) for item in lcx_tokenized]
        keywds = [self.parse_token(item, self.keywds_fields) for item in keywds_tokenized]
        rcx = [self.parse_token(item, self.rcx_fields) for item in rcx_tokenized]
        # Combine to a list
        l, kws = context_to_list(lcx, keywds, rcx)
        # Create Hit
        hit = Hit(l, kws)
        hit.ref = row[0]
        hit.meta = self.parse_ref(hit.ref)
        return hit
        
    def parse_token(self, s, tagnames):
        """
        Parses a token string from the TXM concordance file, using the underscore
        to split the fields. The tag names must be set by the lcx_fields,
        keywds_fields and rcx_fields attribute of the class.
        
        Parameters:
            s (str):    A string representing a token
            
        Returns:
            parse_token(self, s):
                A Token instance.
        """
        l = s.split('_')
        tok = tags_to_tok(l, tagnames)
        return tok
        
def context_to_list(lcx, keywds, rcx):
    """
    Merges three lists representing the left context, keywords, and
    right context respectively into a single list containing the whole 
    sentence and a second list containing only the keywords.
    
    Parameters:
        lcx (list)      : List containing Tokens in the left context
        keywds (list)   : List containing the keywords Tokens
        rcx (list)      : List containing Tokens in the right context
        
    Returns:
        context_to_list(lcx, keywds, rcx):
            A list, kws tuple which can be used to initialize a Hit object.   
    """
    # Check that keywds contains Tokens rather than strings, since the
    # Hit object will check object identity.
    keywds = [make_token(item) for item in keywds]
    l = lcx + keywds + rcx
    kws = [keywd for keywd in keywds]
    return l, kws
    
def tags_to_tok(tags, tagnames = [], word_tag='word'):
    """
    Converts a list of tags to a token using the names in tagnames.
    
    Parameters:
        tags (list)       : List of tags
        tagnames (list)   : List of tagnames to attach to the tags (optional).
                            If no tagnames are given or the length doesn't
                            match 'tag1', 'tag2' etc. will be generated.
        word_tag (str)    : Tag to use for the form of the word.
                            Default is 'word' or the first item, if no 
                            tagnames are given.
        
    Returns:
        tags_to_tok(tags, [tagnames, [word_tag]]):
            A token instance.
    """
    def get_tagname():
        nonlocal i
        s = 'tag' + str(i)
        i += 1
        return s
        
    i = 1
    tagnames = tagnames[:] # COPY tagnames since the pop method is used.
    form, tag_d = '', {}
    # If tagnames is NOT passed, use the first tag as the form.
    if not tagnames: form = tags.pop(0)
    # Iterate over tags
    for tag in tags:
        tagname = tagnames.pop(0) if tagnames else get_tagname()
        if tagname == word_tag:
            form = tag
        else:
            tag_d[tagname] = tag
    if not form:
        raise ParseError('Tag "{}" not found in tagnames'.format(word_tag))
    tok = Token(form)
    tok.tags = tag_d
    return tok
    

