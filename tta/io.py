#!/usr/bin/python3

import os.path, sys, os, csv

class Error(Exception):
    """Exceptions in this module"""
    def __init__(self, msg):
        self.msg = msg
        
class ReadError(Error):
    pass

class WriteError(Error):
    pass

class Reader():
    """Metaclass for text file readers"""
    
    def __init__(self, fname, enc='utf-8'):
        self.fname = fname
        self.enc = enc
        self._check()

    def _check(self):
        """On initialization, opens file and checks read permissions."""
        try:
            f = open(self.fname, 'r', encoding=self.enc)
        except OSError:
            raise ReadError(
                'Error opening {}, please check filename and '.format(self.fname) + \
                'read permissions.'
            )
        except LookupError:
            raise ReadError(
                'Encoding "{}" is unsupported.'.format(self.enc)
            )
            
    def _check_unique_ids(self, ids):
        dupls = list(set([x for x in ids if ids.count(x) > 1]))
        if dupls:
            raise ReadError('Non-unique ids in file {}: {}'.format(
                self.fname, ', '.join(dupls)
            )) 
            
class Writer():
    """Metaclass for text file writers."""
    
    def __init__(self, fname, enc='utf-8'):
        self.fname = fname
        self.enc = enc
        
    def _check(self):
        """Checks write permissions for self.fname."""
        try:
            f = open(self.fname, 'w', encoding=self.enc)
        except OSError:
            raise WriteError(
                'Error opening {}, please check filename and '.format(self.fname) + \
                'write permissions.'
            )
    
class CsvReader(Reader):
    
#        
#    def get_tags(self):
#        """Reads the third column of a CSV file if the "inject" option is
#        switched on."""
#        with open(self.fname, 'r', encoding=self.enc) as f:
#            reader=csv.reader(f)
#            tags = []
#            for x in reader:
#                try:
#                    tags.append((x[0], x[2]))
#                except IndexError:
#                    raise ReadError(
#                        '{} does not contain three columns. '.\
#                        format(self.fname) + 
#                        'Problem line: {}'.format(x),
#                    )
#        return tags

    def _read_csv(self):
        self.lines = []
        with open(self.fname, 'r', encoding=self.enc) as f:
            reader=csv.reader(f)
            for x in reader:
                self.lines.append(x)
        # Generic property "self.data" to be passed back to the writer
        self.data = self.lines
        # Check Unique IDs
        self.ids = [x[0] for x in self.data]
        self._check_unique_ids(self.ids)
        
        
    def get_attr(self, line, key):
        """Returns value by column ID. Key must be an integer or an error is
        returned."""
        try:
            key = int(key)
        except ValueError:
            raise ReadError(
                'Cannot interpret inject value "{}" for headerless CSV file {}.'.\
                format(key, self.fname)
            )
        return line[key]

    def get_tuples(self):
        """Reads CSV to token--tuple list."""
        # Load the CSV if not already in memory
        if not hasattr(self, 'lines'): self._read_csv()
        l = []
        for x in self.lines:
            try:
                l.append((ints(x[0]), x[1]))
            except IndexError:
                raise ReadError(
                    '{} does not contain two columns.'.format(self.fname) + \
                    'Problem line: {}'.format(x)
                )
        return l
        
    def get_line_by_id(self, an_id):
        """Returns the line with the given ID."""
        if not hasattr(self, 'ids_lines'): self.get_ids_lines()
        if not hasattr(self, 'lines_by_id'):
            self.lines_by_id = dict(self.ids_lines)
        try:
            return self.lines_by_id[an_id]
        except KeyError:
            raise ReadError('Line "{}" not found in file {}.'.format(an_id, self.fname))

    def get_ids_lines(self):
        """Returns a list of (id (col 0), list) tuples."""
        # Load the CSV if not already in memory
        if hasattr(self, 'ids_lines'): return self.ids_lines
        if not hasattr(self, 'lines'): self._read_csv()
        l = []
        for x in self.lines:
            l.append((ints(x[0]), x))
        self.ids_lines = l
        return l
        
    def injectables(self):
        """Returns range containing all column IXs in the file"""
        # Load the CSV if not already in memory
        if not hasattr(self, 'lines'): self._read_csv()
        return list(range(0, len(self.lines[0])))

class CsvWriter(Writer):
    
    def set_ids_data(self, id_data):
        """Update the lines to write from the tuple data."""
        #self._check_ids_lines(data)
        if not self.data:
            # Set the lines to write as empty  
            self.data = [[]] * len(id_data) 
        self._update_lines(id_data)
        
    def set_data(self, data):
        """Sets the data for the file from a list."""
        if not isinstance(data, list):
            raise WriteError('Expected list of values.')
        self.data = data
        self.ids = [x[0] for x in self.data]
        
    def _update_lines(self, id_data):
        """Updates lines in self.data from (ids, lines) list."""
        # First convert id_data to a dictionary of lists
        d = dict(id_data)
        for i, line in enumerate(self.data):
            if ints(line[0]) in d:
                self.data[i] = d[ints(line[0])]

    def write(self):
        if not hasattr(self.data):
            raise WriteError('Please set lines to write using set_data or set_ids_data.')
        with open(self.fname, 'w', encoding='utf-8') as f:
            writer=csv.writer(f)
            for row in self.data:
                writer.writerow(row)
                
class DictCsvReader(CsvReader):
    
    def _read_csv(self):
        self.lines = []
        with open(self.fname, 'r', encoding=self.enc) as f:
            reader=csv.DictReader(f)
            self.fieldnames = reader.fieldnames
            if not 'id' in self.fieldnames or not 'word' in self.fieldnames:
                raise ReadError(
                    '{} does not contain required columns "word" and "id".'.format(self.fname)
                )
            for x in reader:
                self.lines.append(x)
        # Generic property "self.data" to be passed back to the writer
        self.data = self.lines
        self.ids = [x['id'] for x in self.data]
        self._check_unique_ids(self.ids)
        
    def get_attr(self, line, key):
        """Returns value by column ID. Key must be an integer or an error is
        returned."""
        try:
            return line[key]
        except KeyError:
            raise ReadError(
                'Column name "{}" not found in CSV file {}.'.\
                format(key, self.fname)
            )

    def get_tuples(self):
        """Reads CSV to token--tuple list."""
        # Load the CSV if not already in memory
        if not hasattr(self, 'lines'): self._read_csv()
        l = []
        for x in self.lines:
            l.append((ints(x['id']), x['word']))
        return l
        
    def get_ids_lines(self):
        """Returns a list of (id (col 0), list) tuples."""
        # Load the CSV if not already in memory
        if hasattr(self, 'ids_lines'): return self.ids_lines
        if not hasattr(self, 'lines'): self._read_csv()
        l = []
        for x in self.lines:
            l.append((ints(x['id']), x))
        self.ids_lines = l
        return l
        
    def injectables(self):
        """Returns list containing all fieldnames except 'id' and 'word' in the file."""
        # Load the CSV if not already in memory
        if not hasattr(self, 'lines'): self._read_csv()
        x = self.fieldnames[:]
        x.remove('id')
        x.remove('word')
        return x

class DictCsvWriter(CsvWriter):
    
    def set_data(self, data):
        """Sets the data for the file from a list."""
        if not isinstance(data, list):
            raise WriteError('Expected list of values.')
        self.data = data
        self.ids = [x['id'] for x in self.data]

    
    def set_ids_data(self, id_data):
        """Update the lines to write from the tuple data."""
        #self._check_ids_lines(data)
        if not self.data:
            # Set the lines to write as empty  
            self.data = [{}] * len(id_data) 
        self._update_lines(id_data)
        
    def _update_lines(self, id_data):
        """Updates lines in self.data from (ids, lines) list."""
        # First convert id_data to a dictionary of lists
        d = dict(id_data)
        for i, line in enumerate(self.data):
            if ints(line['id']) in d:
                self.data[i] = d[ints(line['id'])]
            
    def write(self):
        if not hasattr(self, 'data'):
            raise WriteError('Please set lines to write using set_data or set_ids_data.')
        if not hasattr(self, 'fieldnames'):
            self.fieldnames = list(self.data[0].keys())
        with open(self.fname, 'w', encoding='utf-8') as f:
            writer=csv.DictWriter(f, self.fieldnames)
            writer.writeheader()
            for row in self.data:
                writer.writerow(row)

class ConllReader(Reader):
    
    ID = 1
    FORM = 2
    LEMMA = 3
    UPOS = 4
    XPOS = 5
    FEATS = 6
    HEAD = 7
    DEPREL = 8
    DEPS = 9
    MISC = 10
    
    def _read_conll(self):
        with open(self.fname, 'r', encoding='utf-8') as f:
            self.ids_lines = []
            self.lines = f.readlines()
            for i, line in enumerate(self.lines):
                cols = line[:-1].split('\t')
                # Only append lines containing tokens. 
                # Everything else (comments, whitespace, etc) is ignored.
                if len(cols) == 10: self.ids_lines.append((i, cols))
        # Generic property "self.data" to be passed back to the writer to
        # replicate the source file.
        # Here, it's "self.lines" (i.e. including the non-token lines)
        self.data = self.lines
        
    def get_attr(self, line, key):
        """Returns correct value either by name or by CONLL column number"""
        # Strings are used to match the IX of the CONLL file
        key = self.colname2int(key)
        ix = key - 1 # CONLL columns start at 1, not 0!
        # Return line[ix]
        try:
            return line[ix]
        except:
            raise ReadError(
                'Cannot interpret inject value "{}" for CONLL file {}.'.\
                format(key, self.fname)
            )

    def get_ids_lines(self):
        if not hasattr(self, 'ids_lines'): self._read_conll()
        return self.ids_lines[:]
        
    def get_line_by_id(self, an_id):
        """Returns the line with the given ID."""
        if not hasattr(self, 'ids_lines'): self._read_conll()
        if not hasattr(self, 'lines_by_id'): 
            self.lines_by_id = dict(self.ids_lines)
        try:
            return self.lines_by_id[an_id]
        except KeyError as e:
            raise ReadError('Line {} not found in file {}.'.format(an_id, self.fname))
            
    def get_tuples(self):
        """Reads CONLL-U to token--tuple list."""
        if not hasattr(self, 'ids_lines'): self._read_conll()
        return [(x[0], x[1][self.FORM - 1]) for x in self.ids_lines]
        
    def injectables(self):
        """Returns list of all CONLL-U column numbers EXCEPT 2 (ID, FORM)."""
        return list(range(2,11))
        
    def colname2int(self, key):
        """Converts a column name to an integer denoting the column number."""
        # Double check not an integer hiding here...
        key = ints(key)
        if isinstance(key, str):
            key = key.upper()
            x = 'self.' + key
            try:
                return eval(x)
            except:
                raise ReadError(
                    'Cannot interpret inject value "{}" for CONLL file {}.'.\
                    format(key, self.fname)
                )
        elif isinstance(key, int) and key in list(range(1,11)):
            return key
        else:
            raise ReadError(
                'Cannot interpret inject value "{}" for CONLL file {}.'.\
                format(key, self.fname)
            )
            
class ConllWriter(Writer):
    
    ID = 1
    FORM = 2
    LEMMA = 3
    UPOS = 4
    XPOS = 5
    FEATS = 6
    HEAD = 7
    DEPREL = 8
    DEPS = 9
    MISC = 10
    
    def set_ids_data(self, id_data):
        """Update the lines to write from the tuple data."""
        #self._check_ids_lines(data)
        if not self.data:
            # Set the lines to write as an empty list of length  
            self.data = ['\n'] * id_data[-1][0] + 1
        self._update_lines(id_data)
        
    def set_data(self, data):
        """Sets the raw lines in the file from a list."""
        if not isinstance(data, list):
            raise WriteError('Expected list of strings.')
        if data and not isinstance(data[0], str):
            raise WriteError('Expected list of strings.')
        self.data = []
        for item in data:
            # Append newline to each line if not present
            self.data.append(item if item[-1] == '\n' else item + '\n')
        
    def _check_ids_lines(self, data):
        """Checks that data is in correct format for a CONLL-U file, i.e.
        list of tuples, first element line no., second element list of 10 column
        values."""
        if not isinstance(data, list):
            raise WriteError('Expected list of (id, [line]) tuples.')
        if not data or not isinstance(data[0], tuple):
            raise WriteError('Expected list of (id, [line]) tuples.')
        for item in data:
            if not isinstance(item[0], int) or not isinstance(item[1], list):
                raise WriteError('Expected (int, list) tuple, got {}'.format(
                    repr(item)
                ))
            if not len(item[1]) == 10:
                raise WriteError('Line {}: expect 10 values, got {}'.format(
                    str(item[0]), repr(item[1])
                ))
                
    def _update_lines(self, id_data):
        """Updates lines in self._lines() from ids, lines tuple list."""
        self._check_ids_lines(id_data)
        for an_id, data in id_data:
            self.data[an_id] = '\t'.join(data) + '\n'
            
    def write(self):
        if not hasattr(self, 'data'):
            raise WriteError('Please set lines to write using set_data or set_ids_data.')
        with open(self.fname, 'w', encoding='utf-8') as f:
            f.writelines(self.data)
            
# TWO methods to resolve problems with integer keys in dictionaries.

def ints(s):
    """Converts strings containing integers to integers during the loading process.
    Applied to ALL IDs.
    If s does not contain an integer, returns s without modification."""
    try:
        return int(s)
    except:
        return s

def as_key(self, an_id):
    """Converts integer ID to a string key of the form _ + i"""
    if isinstance(an_id, int):
        return '_' + str(an_id)
    else:
        return an_id
        
def as_id(self, key):
    """Reverses as_key"""
    if key[0] == '_':
        try:
            return int(key[1:])
        except:
            return key
    return key