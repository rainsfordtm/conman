#!/usr/bin/python3

from conman.concordance import *
from conman.tokenizers import *
from uuid import uuid4
import treetools.basetree, treetools.syn_importer, treetools.transformers
import conman.scripts.pennout2cnc
import copy, csv, glob, json, re, os.path

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
    Parent Class to build a concordance. Reads any simple text file where
    hits are delimited by a fixed sequence of characters (typically \n).
    Also defines core methods for Child classes.
    
    Attributes:
    -----------
    concordance (concordance.Concordance):
        Concordance object
        
    encoding (str):
        Text encoding to use for reading the file. Default is 'utf-8'.
        
    lcx_regex (str):
        Regular expression string used to interpret fields in each token
        string in the left context. Default is r'(?P<word>.*)', i.e. the 
        whole string is a word. Also used if there are NO keywords.
        
    keywds_regex (str):
        Regular expression string used to interpret fields in each token
        string in the keywords. Default is r'(?P<word>.*)', i.e. the 
        whole string is a word.
        
    rcx_regex (str):
        Regular expression string used to interpret fields in each token
        string in the right context. Default is r'(?P<word>.*)', i.e. the 
        whole string is a word.
        
    ref_regex (str):
        Regex with named groups used to identify fields in the reference string.
        
    tokenizer (tokenizers.Tokenizer):
        Tokenizer use to parse multi-word fields (typically left- and
        right context).
        
    _on_token_parse_error (str):
        Internal attribute set by descendent class to instruct parser how
        to deal with token strings that it cannot parse with the regex.
        Possible values are:
            - 'drop':   the token is given as an empty string and a warning is printed. 
            - 'keep':   the whole string becomes a word and a warning is printed.
            - 'raise':  raises a ParseError.
        Default is 'drop'.
    
    Methods:
    --------
    get_tokens(self, s, special_field):
        Converts a string into a list of tokens, using the tokenizer and 
        the regex.
        
    parse(self, path, [encoding, [delimiter]]):
        Parses a text file and splits hits using the regex passed in
        delimiter. Default is '\n', i.e. one line per hit.
        
    parse_hit(self, s):
        Parses a string into a hit.
    
    parse_ref(self, ref):
        Parses the reference field into a dictionary of metadata. Uses the
        regex in self.ref_regex.
        
    parse_token(self, s, regex):
        Parses a token string into fields using the regex. The key "word" is
        reserved for the form of the token.
        
    tokenize(self, s):
        Uses self.tokenizer to tokenize a multi-word field.
    
    """
    
    SPECIAL_FIELDS = ['KEYWORDS', 'LCX', 'RCX', 'TOKENS', 'REF', 'UUID']
    
    @classmethod
    def create(cls, importer_type):
        """
        Creates an instance of importer_type and returns it.
        """
        
        IMPORTER_TYPE_TO_CLASS_MAP = {
          'Importer':  Importer,
          'TokenListImporter': TokenListImporter,
          'ConllImporter': ConllImporter,
          'TableImporter': TableImporter,
          'PennOutImporter': PennOutImporter,
          'BaseTreeImporter': BaseTreeImporter,
          'GrewMatchImporter': GrewMatchImporter
        }
        if importer_type not in IMPORTER_TYPE_TO_CLASS_MAP:
              raise ValueError('Bad importer type {}'.format(importer_type))
        return IMPORTER_TYPE_TO_CLASS_MAP[importer_type]()
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        self.concordance = Concordance([])
        self.encoding = 'utf-8'
        self.lcx_regex, self.keywds_regex, self.rcx_regex = \
            r'(?P<word>.*)', r'(?P<word>.*)', r'(?P<word>.*)' 
        self.ref_regex = ''
        self.tokenizer = Tokenizer()
        self._on_token_parse_error = 'drop'
        
    def _handle_token_parse_error(self, s, regex):
        # What to do when a string is encountered that the regex can't
        # process
        msg = "Can't identify the token in '{}', regex '{}'".format(s, regex)
        if self._on_token_parse_error == 'raise':
            raise ParseError(msg)
        else:
            print(msg)
        if self._on_token_parse_error == 'keep':
            tok = Token(s)
        else:
            tok = Token('')
        return tok
            
    def get_tokens(self, s, special_field):
        """
        Converts a string into a list of tokens, using the tokenizer and 
        the regex.
        
        Parameters:
            s (str) :           A string containing tokens
            special_field (str):One of the special fields in SPECIAL_FIELDS
                                which selects the right regex.
                                
        Returns:
            get_tokens(self, s, special_field):
                A list of concordance.Tokens.
        """
        l = self.tokenize(s)
        if special_field in ['LCX', 'TOKENS']:
            result = [self.parse_token(item, self.lcx_regex) for item in l]
        if special_field.startswith('KEYWORDS'):
            result = [self.parse_token(item, self.keywds_regex) for item in l]
        if special_field == 'RCX':
            result = [self.parse_token(item, self.rcx_regex) for item in l]
        while Token('') in result:
            result.remove(Token(''))
        return result
            
    def parse(self, path, delimiter = '\n'):
        """
        Parses a text file and splits hits using the value passed in
        delimiter. Default is '\n', i.e. one line per hit.
        
        Parameters:
        -----------
            path (str):         Path to text file.
            encoding (str):     Text encoding of the CSV or text file.
            delimiter (str):    Regex representing the characters used as 
                                a delimiter.
        
        Returns:
        --------
            parse(self, path, [encoding, [delimiter]]):
                A concordance object.
        """
        with open(path, 'r', encoding=self.encoding, errors='replace') as f:
            s = ''
            for line in f:
                s += line
                if not re.search(delimiter, s): continue
                l = re.split(delimiter, s)
                for group in l[:-1]:
                    hit = self.parse_hit(group)
                    self.concordance.append(hit)
                s = l[-1]
            # At EOF strip all trailing whitespace
            s = s.rstrip()
            if s:
                hit = self.parse_hit(s)
                if hit:
                    self.concordance.append(hit)
        return self.concordance
        
    def parse_hit(self, s):
        """
        Parses a string into a hit.
        
        Parameters:
            s (str):        A string containing the hit
            
        Returns:
            parse_hit(self, s):
                A concordance.Hit object.
        """
        l = self.get_tokens(s, 'TOKENS')
        return Hit(l) if l else None
            
    def parse_token(self, s, regex):
        """
        Parses a token string into fields using the regex. The key "word" is
        reserved for the form of the token.
        
        Parameters:
            s (str):        A string representing a token
            regex (str):    A regex mapping the token string to fields, one
                            of which must be 'word'.
        
        Returns:
            parse_token(self, s, regex):
                A concordance.Token instance.
        """
        m = re.match(regex, s)
        if not m or m and not 'word' in m.groupdict():
            tok = self._handle_token_parse_error(s, regex)
            tok.tags = {}
        else: # Successful parse
            tok = Token(m.groupdict()['word'])
            tok.tags = dict([(key, value) for key, value in m.groupdict().items()])
            tok.tags.pop('word')
        return tok
        
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
        if m:
            return m.groupdict()
        else:
            return {}
        
        
    def tokenize(self, s):
        """
        Calls tokenize method of self.tokenizer to tokenize string s.
    
        Parameters:
            s (str) : String containing tokens
        
        Return:
            tokenize(self, s):
              A list of tokens
        """
        try:
            return self.tokenizer.tokenize(s)
        except:
            print(s)
            raise

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
        
    separate_by_keyword_true_value (bool):
        If True, different keyword_true_values will be treated as separate
        matches within the same tree.
        
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
        
    stree_to_hits(self, stree):
        Converts a treetools.basetree.StringTree object to a list of
        concordance.Hit objects.
        
    """
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Importer.__init__(self)
        self.keyword_attr = 'KEYWORDS'
        self.keyword_true_values = ['yes', 'y', 't', 'true']
        self.separate_by_keyword_true_value = False
        
    def is_keyword(self, elem):
        """
        Returns True if the passed leaf node from a BaseTree is marked as a
        keyword. Uses attribute given in self.keyword_attr and looks for
        the value in self.keyword_true_values.
        
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
        else:
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
            hits = self.stree_to_hits(stree)
            self.concordance.extend(hits)
        return self.concordance
        
    def stree_to_hits(self, stree):
        """
        Converts a treetools.basetree.StringTree object to a list of
        concordance.Hit objects.
        
        Parameters:
            stree (treetools.basetree.StringTree):
                A StringTree containing the hit.
            
        Returns:
            stree_to_hits(self, stree):
                A list of Hit objects.
        """
        l, kws = [], []
        bst = stree.to_base_tree()
        bst.restructure(knots = False) # Convert all knots to leaves.
        bst.sort() # Ensures that leaves in the BaseTree are in text order.
        for leaf in bst.leaves:
            l.append(self.leaf_to_token(bst, leaf))
            if self.is_keyword(leaf): kws.append(l[-1])
        tree_id = stree.get_id()
        if self.separate_by_keyword_true_value and kws:
            # 1. Get possible true values of keyword_attr 
            values = list(
                set([kw.tags[self.keyword_attr] for kw in kws]) & set(self.keyword_true_values)
            )
            # 2. Make a list of separate kws lists.
            l_kws = []
            for value in values:
                l_kws.append((value,
                    list(filter(lambda x: x.tags[self.keyword_attr] == value, kws))
                ))
        else:
            l_kws = [('', kws)]
        # Iterate over l_kws to generate a list of hits from the tree.
        hits = []
        for true_val, kws in l_kws:
            hit = Hit(l, kws)
            # Use tree_id for the ref whatever -- this format is needed for the
            # pennout2cnc script.
            hit.ref = tree_id.split('|')[0]
            hit.tags = self.parse_ref(hit.ref)
            hits.append(hit)
        if not hits:
            print(l)
            print(l_kws)
            print(self.keyword_node_regex)
            raise ParseError
        return hits

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
        Default is r':\s*[0-9]+\s', i.e. the first node after the dominating
        node.
        
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
    
    update_regex_from_remark(self, path):
        Reads keyword_node_regex from a remark in the out file and updates
        self.keyword_node_regex.
    
    parse(self, path):
        Parses a Penn .out file.
   
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        BaseTreeImporter.__init__(self)
        self.dump_xml = ''
        self.keyword_node_regex = r':\s*(?P<keyword_node>[0-9]+)\s'
        self.script = conman.scripts.pennout2cnc.script
        # Reset self.keyword_true_values to match integers from 1 to 100
        # and self.separate_by_keyword_true_value
        self.keyword_true_values = [str(i) for i in range(100)]
        self.separate_by_keyword_true_value = True
        
    def update_regex_from_remark(self, path):
        """
        Updates self.keyword_node_regex from the remark at the beginning of
        the file.
        
        Parameters:
            path (str) :        Path to the .out file.
            
        """
        with open(path, 'r', encoding=self.encoding) as f:
            s, in_remark = '', False
            for line in f:
                if in_remark:
                    # Remark is over with next string ending :
                    if re.match('^[A-z].*: .*', line):
                        break
                    else:
                        # replace CR with space
                        s += line[:-1] + ' '
                elif re.match('^remark: .*', line):
                    s += line[7:-1] + ' '
                    in_remark = True
        m = re.search(r'PO_keyword_node_regex=(.*\(?P<keyword_node>[^s]+\)[^\s]*)', s)
        if m:
            self.keyword_node_regex = m.group(1)
        
        
    def parse(self, path):
        """
        Parses a Penn .out file.
        
        Parameters:
            path (str) :        Path to the .out file.
            
        Returns:
            parse(self, path):
                A concordance object.
        """
        # 0. Update self.keyword_node_regex from the remark
        self.update_regex_from_remark(path)
        # 1. Call syn_importer on the .out file. to create a BaseForest.
        forest = treetools.syn_importer.build_forest(
            path, 'penn-psd-out', encoding=self.encoding, errors='replace'
        )
        # 2. Initialize a transformer
        transformer = treetools.transformers.Transformer()
        # 3. Set the script method from self.script
        transformer.script = self.script
        # 4. Transform the forest
        forest = transformer.transform(
            forest,
            keyword_attr = self.keyword_attr,
            keyword_node_regex = self.keyword_node_regex,
            word_lemma_regex = self.lcx_regex
            )
        # 5. Add each tree in the forest to the concordance
        for stree in forest:
            hits = self.stree_to_hits(stree)
            self.concordance.extend(hits)
        # 6. Dump the XML if a path is set
        if self.dump_xml:
            with open(self.dump_xml, 'w') as f:
                f.write(forest.toxml())
        # 7. Return concordance.s 
        return self.concordance
        
class GrewMatchImporter(Importer):
    """
    Imports a concordance derived from the .json output of a 
    Grew Match search.
    
    Additional Attributes:
    ----------------------
    
    add_ref_prefix (bool):
        If True, adds a "corpus/file/" prefix to the sent_id in
        MULTI mode. Default is True.
    
    corpus_path (str):
        Path to the corpus file, which is either a .conllu file
        (if running in MONO mode) or another .json file (MULTI mode)
        
    keyword_node (str):
        Name of the node from the query to use as a keyword. Default
        is "X" (Grew match's default label)
        
        
    Methods:
    --------
    parse(self, path):
        Parses the .json file containing the hits, reading the
        original corpus to create a concordance.
        
    parse_conllu(self, path, results):
        Parses a conllu file, reading the hits from "results".
    
    """
    
    def __init__(self):
        Importer.__init__(self)
        self.add_ref_prefix = True
        self.corpus_path = ''
        self.keyword_node = 'X'
        self._importer = ConllImporter()
        self._importer.head_is_kw = False
        self._multi = False # Hidden attribute, set from corpus_path extension
        
    def _set_mode(self):
        ext = os.path.splitext(self.corpus_path)[1]
        self._multi = True if ext == '.json' else False
        
    def parse_conllu(self, path, results, ref_prefix=''):
        """
        Adds hits to self.concordance useing a conllu file and a list
        of results.
        
        Parameters:
            path (str):
                Path to the original conllu file.
            results (list):
                A list of dictionaries read from the .json outputted
                by Grew Match.
        """
        # Reset the .concordance attribute of the importer.
        self._importer.concordance = Concordance([])
        # Parse the .conllu file
        raw_cnc = self._importer.parse(path)
        # Get the .ref attributes as a list
        refs = [x.ref for x in raw_cnc]
        # Iterate over the results
        for result in results:
            try:
                hit_src = raw_cnc[refs.index(result['sent_id'])]
            except ValueError:
                # The result is not in this concordance
                # Continue the loop
                # KeyError should never be raised
                continue
            try:
                kw_ix = int(result['matching']['nodes'][self.keyword_node]) - 1
            except KeyError:
                # Can't find the node in this result; could have bee
                # a weird or badly formed query
                continue
            # Rebuild the hit
            hit = Hit([copy.copy(x) for x in hit_src])
            hit.tags = hit_src.tags.copy()
            hit.ref = ref_prefix + hit_src.ref if self.add_ref_prefix else hit_src.ref
            # Parse the ref
            for key, value in self.parse_ref(hit.ref).items():
                hit.tags[key] = value
            try:
                hit.kws = [hit.data[kw_ix]]
            except:
                print(hit)
                print(hit_src)
                print(result)
                raise
            # Append hit to self.concordance
            self.concordance.append(hit)
        
    def parse(self, path):
        """
        Parses the Grew Match results from a .json file.
        
        Parameters:
            path (str):
                Path to the .json results file.
        
        Returns:
            parse(self, path):
                A concordance object.
        """
        # An initial check: corpus_path must be set
        if not self.corpus_path:
            raise ParserError('No path to original corpus (GM_corpus_path).')
        
        # We begin by working out if we're in "multi" mode or not.
        self._set_mode()
        # If we're in multi mode:
        #   (i)   the results file is a dictionary keyed by corpus.
        #   (ii)  self.corpus_path is a .json file containing a list of
        #         corpora with "id" and "directory" attributes
        #   (iii) the Concordance is obtained by iterating over corpora
        #         and files in the corpora.
        # Otherwise:
        #   (i)   the results file is a list of hits
        #   (ii)  self.corpus_path is the .conllu file containing the
        #         data
        if self._multi:
            results_by_corpus = parse_json(path)
            corpus_json = parse_json(self.corpus_path)
            corpora = [x['id'] for x in corpus_json]
            directories = [x['directory'] for x in corpus_json]
            # If no ref_regex is set, 
            if not self.ref_regex and self.add_ref_prefix:
                self.ref_regex = r'(?P<corpus>[^/]+)/(?P<file>[^/]+)/.*'
            for corpus, directory in zip(corpora, directories):
                try:
                    results = results_by_corpus[corpus]
                except KeyError:
                    # No results
                    continue
                if not os.path.isabs(directory):
                    # calculate relative to 
                    directory = os.path.join(os.path.dirname(self.corpus_path), directory)
                conllus = [
                    os.path.join(directory, x)
                    for x in glob.glob(
                        '*.conll*',
                        root_dir=directory
                    )
                ]
                for conllu in conllus:
                    print('Parsing ' + conllu)
                    ref_prefix = corpus + '/' + os.path.basename(conllu) + '/'
                    self.parse_conllu(conllu, results, ref_prefix = ref_prefix)
        else:
            results = parse_json(path)
            self.parse_conllu(self.corpus_path, results)
        return self.concordance
        
class TableImporter(Importer):
    """
    Imports a concordance in some kind of tabular form.
    Defines core methods for child classes.
    
    Additional Attributes:
    ----------------------
    dialect (str):
        Dialect to use for the CSV reader. Options are:
            'excel':    Comma-separated, quote with " only when necessary.
            'tab'  :    Tab-separated, no quoting or escaping.
            
    has_header (bool):
        File has a header row if set to True. Default is True.
        
    ignore_header (bool):
        Ignore the header in the CSV file and use values in self.fields.
        Default is False.
        
    fields (list):
        List of fields to import in the order in which the columns should be
        represented in the file, overrides data read from the file header. 
        Fields are stored by default in the .tags dictionary of the hit, but
        the TableImporter.SPECIAL_FIELDS are reserved values:
        Default values read a four-column concordance exported from TXM.
        
        Hits:
        -----
        KEYWORDS:   Keyword tokens only
        LCX:        Tokens preceding keywords only
        RCX:        Tokens following keywords only
        REF:        hit.ref
        UUID:       unique ID
        TOKENS:     Tokens
        
    Methods:
    --------
    
    parse(self, path, encoding = 'utf-8'):
        Parses a CSV file.
        
    parse_hit(self, row):
        Parses a row from the CSV file. Returns a Hit object.
        
    parse_token(self, s):
        Parses the tokens in the concordance file, using the underscore
        to split the fields. The tag names must be set by the lcx_fields,
        keywds_fields and rcx_fields attribute of the class.
    """
    
    def __init__(self):
        Importer.__init__(self)
        self.has_header = True
        self.ignore_header = False
        self.dialect = 'excel'
        self.fields = ['REF', 'LCX', 'KEYWORDS', 'RCX']
        csv.register_dialect(
            'tab',
            delimiter='\t',
            quoting=csv.QUOTE_NONE
            )
            
    def parse(self, path):
        """
        Parses a CSV file.
        
        Parameters:
            path (str):     Path to the CSV or text file.
            encoding (str): Text encoding of the CSV or text file.
        
        Returns:
            parse(self, path, [encoding, [header]]):
                A concordance object.
        """
        with open(path, 'r', encoding=self.encoding, errors='replace', newline='') as f:
            reader = csv.reader(f, self.dialect)
        # Skip the first row if header is True
            if self.has_header:
                header_row = reader.__next__()
                if not self.ignore_header: 
                    self.fields = header_row
                elif not self.fields:
                    raise ParseError("No column names given. Set importer.fields or importer.header = True.")
            for row in reader:
                hit = self.parse_hit(row)
                self.concordance.append(hit)
        return self.concordance
        
    def parse_hit(self, row):
        """
        Parses a row from a CSV file. Returns a Hit object.
        
        Parameters:
            row (list):     List of fields. 
            
        Returns:
            parse_hit(self, row):
                A Hit object.
                
        """
        uuid, ref, d = None, '', dict()
        # Parse the fields
        for key, value in zip(self.fields, row):
            if key in self.SPECIAL_FIELDS or key.startswith('KEYWORDS'):
                if key == 'UUID':
                    uuid = get_uuid(value) # Get UUID will always return a UUID.
                elif key == 'REF':
                    ref = value
                else:
                    d[key] = self.get_tokens(value, key)
            else:
                d[key] = value
        # Create list of all tokens
        #print(d)
        # Check for KEYWORDS split over several columns and rewrite
        # them as a single column
        l = []
        for field in self.fields:
            if field.startswith('KEYWORDS'): l.append(field)
        if l:
            d['KEYWORDS'] = [tok for field in l for tok in d.pop(field)]
        if 'KEYWORDS' in d:
            l, kws = context_to_list(d.pop('LCX'), d.pop('KEYWORDS'), d.pop('RCX'))
        else:
            try:
                l, kws = d.pop('TOKENS'), []
            except KeyError:
                raise ParseError('Cannot find TOKEN or KEYWORDS field in file. ' + \
                    'Use automatically recognized names in the header or set fieldnames ' + \
                    'manually in the workflow file.')
        # Create Hit, passing uuid
        hit = Hit(l, kws, uuid)
        hit.ref = ref
        # Parse the reference to add metadata
        for key, value in self.parse_ref(hit.ref).items():
            d[key] = value
        # Set as hit.tags
        hit.tags = d
        return hit
        
    def sniff_dialect(self, path):
        """
        Resets self.dialect and self.has_header based on the results of
        csv.sniffer.
        
        Parameters:
            path (str):     Path to the CSV file.
        """
        with open(path, 'r', newline='') as f:
            sniffer = csv.Sniffer()
            self.dialect = sniffer.sniff(f.read(1024))
            f.seek(0)
            self.has_header = sniffer.has_header(f.readline())
            
class TokenListImporter(Importer):
    """
    Class to import the tokens in a one-token-per-line list format.
    
    Attributes:
    -----------
    hit_end_token (str):
        Character used as a dummy token to delimit the hits (essential).
        Default is '', which is interpreted as an empty line. Otherwise,
        empty lines are ignored until hit_end_token is encountered.
    comment_string (str):
        String used at the start of a line to indicate a comment. Default is
        '', i.e. no comments
    
    Methods:
    --------
    parse(self, path):
        Imports concordance from path, one token per line.
        
    parse_comment(self, s):
        Parses a line starting with self.comment_string. Default
        behaviour is to ignore comments. Returns a dictionary.
        
    """
    
    def __init__(self):
        """
        Constructs all attributes needed for an instance of the class.
        """
        Importer.__init__(self)
        self.hit_end_token = ''
        self.comment_string = '#'
        
    def parse(self, path):
        """
        Imports concordance from path, one token per line.
        
        Parameters
        ----------
        path (str):
            Path to the file to import.
            
        Returns:
        --------
        parse(self, path):
            A concordance object
        """     
        with open(path, 'r', encoding=self.encoding, errors='replace') as f:
            d, l = {}, []
            for line in f:
                if self.comment_string and line.startswith(self.comment_string):
                    # send to comment parser
                    d.update(self.parse_comment(line))
                    # next line
                    continue
                if line[:-1]:
                    tok = self.parse_token(line[:-1], self.lcx_regex)
                else:
                    tok = Token('')
                if tok and tok != self.hit_end_token: 
                    # not an empty line, not the hit_end_token
                    l.append(tok)
                elif tok == self.hit_end_token:
                    # could be an empty line if it's also the hit_end_token
                    hit = Hit(l)
                    hit.tags = d.copy()
                    self.concordance.append(hit)
                    d, l = {}, []
            # If there are no hit end tokens, we basically get a concordance
            # with a single hit. So we need to store whatever's left in l.
            if l:
                hit = Hit(l)
                hit.tags = d.copy()
                self.concordance.append(hit)
                d, l = {}, []
        #print(len(self.concordance))
        #print(self.concordance[0][:100])
        return self.concordance
        
    def parse_comment(self, s):
        """
        Parses a line starting with self.comment_string. Default
        behaviour is to ignore comments. Returns a dictionary.
        
        Parameters
        ----------
        s (str):
            A line from the input file containing a comment.
            
        Returns:
        --------
        parse_comment(self, s):
            A dictionary.
        """
        return {}

class ConllImporter(TokenListImporter):
    """
    Class to import Conll files. Uses TokenListImporter but resets 
    self.lcx_regex when parse is called to ensure it's correct for a 
    ten-column .conllu file.
    
    Attributes:
    -----------
    head_is_kw (boolean):
        If set to True, it turns the first sentence root element in a 
        parsed structure into the keyword. If False, no keywords are
        identified. Default is True.
        
    Methods:
    --------
    head_to_kw(self):
        Promotes the first token for which conll_HEAD is 0 to a keyword,
        allowing the hit to be treated as a concordance with left and
        right context.
        
    parse(self, path):
        Parses a conllu file, returns a Concordance
        
    parse_comment(self, s):
        Parses a comment line. If the line has the form "# key = value",
        it's stored in the dictionary, otherwise it's ignored.
    """
    
    def __init__(self):
        TokenListImporter.__init__(self)
        self.head_is_kw = True
        # Raise Parse Error if a token can't be dealt with.
        self._on_token_parse_error = 'raise'
        
    def head_to_kw(self):
        """
        Promotes the first token for which conll_HEAD is 0 to a keyword,
        allowing the hit to be treated as a concordance with left and
        right context.
        """
        for hit in self.concordance:
            for tok in hit:
                try: 
                    if str(tok.tags['conll_HEAD']) == '0':
                        hit.kws = [tok]
                        continue
                except:
                    print(tok, tok.tags)
                    raise
        
    def parse(self, path):
        """
        Mostly a wrapper for TokenListImporter.parse using a complex self.lcx_regex.
        But also has handles Conllu's coding of agglutinations.
        """
        
        def get_ref():
            nonlocal hit, path, i
            try:
                return hit.tags['sent_id']
            except KeyError:
                pass
            return '{}_{:0>5}'.format( 
                os.path.basename(path),
                i + 1 # Grew Match is 1-indexed.
            )
        
        def parse_agglutination(hit):
            # Pass 2 to remove agglutination
            l, span, form = [], 0, ''
            for tok in hit:
                if form:
                    # Reset tok.form
                    tok.form = form
                    # Eliminate form
                    form = ''
                    # Decrease span
                    span += -1
                elif span:
                    # Reset tok.form
                    tok.form = ''
                    # Decrease span
                    span += -1
                else:
                    ixs = tok.tags['conll_ID'].split('-')
                    if len(ixs) > 1:
                        # append the token to the deletion list
                        l.append(tok)
                        # calculate span
                        span = int(ixs[1]) - int(ixs[0]) + 1
                        # store full form
                        form = tok.form
            # Delete agglutinated tokens
            for tok in l:
                hit.remove(tok)
        
        self.lcx_regex = ''.join([
            r'(?P<conll_ID>[0-9\-]+)\t',
            r'(?P<word>[^\t]+)\t',
            r'(?P<conll_LEMMA>[^\t]+)\t',
            r'(?P<conll_CPOSTAG>[^\t]+)\t',
            r'(?P<conll_POSTAG>[^\t]+)\t',
            r'(?P<conll_FEATS>[^\t]+)\t',
            r'(?P<conll_HEAD>[^\t]+)\t',
            r'(?P<conll_DEPREL>[^\t]+)\t',
            r'(?P<conll_PHEAD>[^\t]+)\t',
            r'(?P<conll_PDEPREL>[^\t]+).*'
        ])
        # Run parse from the parent class
        TokenListImporter.parse(self, path)
        # Re-parse agglutinated tokens
        for i, hit in enumerate(self.concordance):
            parse_agglutination(hit)
            # Generate a .ref from sent_id OR using Grew Match style
            hit.ref = get_ref()
        # Turn heads into kws if necessary
        if self.head_is_kw: self.head_to_kw()
        # Return concordance
        return self.concordance
        
    def parse_comment(self, s):
        """
        Parses a comment line. If the line has the form "# key = value",
        it's stored in the dictionary, otherwise it's ignored.
        
        Parameters
        ----------
        s (str):
            A line from the input file containing a comment.
            
        Returns:
        --------
        parse_comment(self, s):
            A dictionary.
        
        """
        m = re.match(r'#+\s*([^\s=]+)\s*=\s*([^\n]+)', s)
        if m:
            return {m.group(1): m.group(2)}
        else:
            return {}
      
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
    
def get_importer_from_path(path):
    """
    Function to pick a default importer from the filename extension.
    Currently implements the following:
    
    .csv : TableImporter
    .out : PennOutImporter
    .txt : Importer
    .xml : BaseTreeImporter
    .conll(u) : ConllImporter
    
    All other extensions trigger ParseError.
    
    Parameters:
    path (str) : Path to the input file
    
    Returns:
        get_importer_from_path(path)
            An Importer object.
    """
    ext = os.path.splitext(path)[1]
    if ext == '.csv':
        importer = TableImporter()
        # CSV files being what they are, call the sniffer.
        importer.sniff_dialect(path)
        return importer
    if ext == '.out': return PennOutImporter()
    if ext == '.txt': return Importer()
    if ext == '.xml': return BaseTreeImporter()
    if ext in ['.conll', '.conllu']: return ConllImporter()
    raise ParseError('No default importer for file extension "{}".'.format(ext))
    
def get_uuid(s):
    """
    Returns a UUID generated from the string or a new UUID, if s isn't a
    valid UUID. TODO: log something here.
    
    Parameters:
        s (str):    A string representing a UUID
        
    Returns:
        get_uuid(s):
            A uuid.UUID object.
    """
    try:
        uuid = make_uuid(s)
    except:
        uuid = uuid4()
    return uuid
    
def parse_json(path):
    """
    Loads a JSON file into a Python object.

    Parameters:
        path (str):    Path to the JSON file
        
    Returns:
        parse_json(path):
            A Python object.
    """
    with open(path) as f:
        return json.load(f)
    
    
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
    
