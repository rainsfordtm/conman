#!/usr/bin/python3

#######################################################################
# LGeRM lemma disambiguation tool                                     #
# Based on workflow/script developed by Alexei Lavrentiev             #
# © Tom Rainsford, ILR, Universität Stuttgart, 2022-                  #
#######################################################################

import re, csv, sys, argparse

class LgermFilterer():
    """
    Class containing all the functions necessary for filtering
    of LGeRM lemma output.
    """

    # Mappings from Alexei's Perl script. The order is important.
    MAPPING_LGERM = [
        (r'(\(\?\|loc|préf|suff)$', ['OUT']),
        (r'adj\., adv\. et subst\. masc', ['APD', 'ADV', 'NOMcom']),
        (r'adj\. et adv\.', ['APD', 'ADV']), # CORRECTED
        (r'adj\. et subst\.', ['APD', 'NOMcom']),
        (r'adv\., prép\. et subst', ['ADV','PRE','NOMcom']),
        (r"adv\. (d'intensité)? et conj", ['ADV','CON']),
        (r'adv\. et prép', ['ADV', 'PRE']),
        (r'adv\. et subst', ['ADV', 'NOMcom']),
        (r'art', ['DET']),
        (r'pron\. pers\.', ['PRO']),
        (r'(adj|dém|indéf|interr|num|poss|pron|rel\. interr)', ['APD']),
        (r'adv', ['ADV']),
        (r'conj', ['CON']),
        (r'interj', ['INJ']),
        (r'mot lat', ['ETR']),
        (r'(nom de lieu|nom propre)', ['NOMpro']),
        (r'(part|verbe)', ['VER']),
        (r'ponctuation', ['PON']),
        (r'prép\. et adv\.', ['PRE', 'ADV']),
        (r'prép\.', 'PRE'),
        (r'quantif', ['ADV', 'APD']),
        (r'subst\. et adj\.', ['NOMcom', 'APD']),
        (r'subst\. et adv\.', ['NOMcom', 'ADV']),
        (r'subst', ['NOMcom', 'NOMpro'])
    ]
    
    # Mappings from Alexei's Perl script. The order is important.
    MAPPING_CATTEX = [
        (r'ABR|OUT|RED|RES', 'OUT'),
        (r'DETdef|DETndf', 'DET'),
        (r'PROper', 'PRO'),
        (r'ADJ|DET|PRO', 'APD'),
        (r'ADV', 'ADV'),
        (r'CON', 'CON'),
        (r'ETR', 'ETR'),
        (r'INJ', 'INJ'),
        (r'NOMcom', 'NOMcom'),
        (r'NOMpro', 'NOMpro'),
        (r'PON', 'PON'),
        (r'PRE', 'PRE'),
        (r'VER', 'VER')
    ]
    
    # Frequent lemmas from Alexei's Perl script.
    FREQUENT_LEMMAS = set([
        'AVOIR1', 'ÊTRE1', 'DEVOIR2', 'TOUT2', 'PART1', 'SEIGNEUR', 
        'PRENDRE', 'FEMME', 'ROI1', 'SI3', 'AMI', 'VOULOIR', 'DIEU'
    ])
    
    def _get_stn(self, pos, mapping):
        # runs regex, converts pos to standardized tag, returning it.
        for pattern, stn in mapping:
             m = re.match(pattern, pos)
             if m: return stn
        # if this procedure fails, return the tag unchanged
        return pos
           
    def filter_lemmas(self, form, pos, lgerm_out, mapping_pos, mapping_lgerm):
        """
        Disambiguates the output from the LGeRM lemmatizer using a pos
        tag. Returns the matching lemma (or lemmas) as a list of strings.
        
        Parameters:
        
        form (str):
            The token as a string.
        pos (str):
            The gold or tagger-approved part-of-speech tag
        lgerm_out (str):
            The output string from the LGeRM lemmatizer.
        mapping_pos (list):
            A list of (regex, str) tuples to be applied to the pos tag.
            The str gives an internal, standard pos tags which
            will be used to compare the pos tag with the LGeRM tag.
        mapping_lgerm (list):
            A list of (regex, list) tuples to be applied to the LGeRM tags.
            The list specifies a list of internal, standard pos tags which
            will be matched against the standard pos tag.
            
        Returns:
        
        filter_lemmas(form, pos, lgerm_out, mapping_pos, mapping_lgerm)
            Returns a list of possible lemmas as a string.
        """
       
     
        lgerm_tups = self.parse_lgerm(lgerm_out)
        #print(lgerm_tups)
        pos_stn = self._get_stn(pos, mapping_pos)
        lgerm_stns = [self._get_stn(x[1], mapping_lgerm) for x in lgerm_tups]
        # Iterate over the LGeRM lemmas and their standardized POS tags
        lemmas = []
        #print(lgerm_stns)
        if form == 'on':
            print(lgerm_tups, lgerm_stns, pos_stn)
        for lgerm_tup, lgerm_stn in zip(lgerm_tups, lgerm_stns):
            # lgerm_stn is still a list of possible tags for this one
            # lemma. So if one matches, it's a possible lemma. Add to 
            # list.
            if pos_stn in lgerm_stn:
                lemmas.append(lgerm_tup[0])
        # If no appropriate lemma found: copy all lemmas without reference to pos;
        # if no lemma suggestions, simply recopy the form with an asterisk
        if not lemmas:
            lemmas = [x[0] for x in lgerm_tups] if lgerm_tups else [form.upper() + '*']
        return lemmas        
            
    def parse_lgerm(self, lgerm_out):
        """
        Parses the long string outputted by LGeRM into a list of 
        (lemma, lgerm_pos, [lgerm_rules]) tuples.
        
        Parameters:
        
        lgerm_out (str):
            The output string from the LGeRM lemmatizer.
            
        Returns:
        
        parse_lgerm(lgerm_out):
            A list of (lemma, lgerm_pos, [lgerm_rules]) tuples.
        """
        tups = []
        for pairs in lgerm_out.split('|'):
            l = pairs.split('@')
            if len(l) == 2: 
                tups.append((l[0], l[1], []))
            elif len(l) > 2: # extra fields are (presumably) LGeRM rules
                tups.append((l[0], l[1], l[2:]))
            else:
                print("Warning: Can't parse {}".format(pairs))
        return tups
    
    def process_csv(self, infile, outfile):
        """
        Runs the disambiguator on a CSV file, which must contain the
        following columns:
            - word (the form)
            - cattex_pos (the pos tag)
            - lgerm_out (unprocessed verb-pos pairings from LGeRM)
        """
        # Load
        with open(infile, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            for field in ['word', 'cattex_pos', 'lgerm_out']:
                if not field in header:
                    print("Field {} missing in csv, aborting".format(field))
                    sys.exit(2)
            table = [x for x in reader]
        # Process, filter + refine
        for d in table:
            l = self.filter_lemmas(
                d['word'], d['cattex_pos'], d['lgerm_out'],
                self.MAPPING_CATTEX, self.MAPPING_LGERM
            )
            d['lgerm_filtered'] = '|'.join(self.refine_lemmas(l))
        # Write the file
        with open(outfile, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames = header + ['lgerm_filtered'])
            writer.writeheader()
            writer.writerows(table)
                 
    def refine_lemmas(self, lemmas,
        lower_case=True,
        prioritize_frequent=True,
        strip_numbers=True
        ):
        """
        Post-processes the lemmas filtered by POS in order to further 
        reduce ambiguities.
        
        Parameters:
        
        lemmas (list):
            A list of LGeRM lemmas, as returned by filter_lemmas.
        lower_case (bool):
            If True (default), converts the lemma to lower case.
        prioritize_frequent (bool):
            If True (default), will prioritize the lemma given in the
            FREQUENT_LEMMAS list by placing all the others in parentheses.
        strip_numbers (bool):
            If True (default), removes the number from the end of the 
            LGeRM lemma and then eliminates duplicates.
            
        Returns
        refine_lemmas(lemmas):
            A list of lemmas following the refinement process.
        """
        
        def strip_numbers(l):
            # strips numbers from a list of lemmas if and when necessary
            nonlocal strip_numbers        
            if not strip_numbers: return l
            l2 = []
            while l:
                s = l.pop(0)
                l2.append(s[:-1] if s[-1].isnumeric() else s)
            l2 = list(set(l2))
            l2.sort()
            return l2
            
        if prioritize_frequent:
            # Get the union of the set of frequent lemmas and the set
            # of lemmas
            st = set(lemmas) & self.FREQUENT_LEMMAS
            if st:
                # add parentheses to infrequent lemmas            
                st2 = set(lemmas) - self.FREQUENT_LEMMAS
                lemmas = strip_numbers(list(st)) + ['(' + x + ')' for x in strip_numbers(list(st2))]
            else:
                lemmas = strip_numbers(lemmas)
        else:
            lemmas = strip_numbers(lemmas)
        if lower_case:
            # convert to lower case
            lemmas = [x.lower() for x in lemmas]
        return lemmas
            
# Test launch data
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Filters the LGeRM output based on results from a POS tagger. ' + \
        'Input is a CSV file with word, cattex_pos, and lgerm_out columns.'
        )
    parser.add_argument('infile', help='Input file to import.')
    parser.add_argument('outfile', help='Output file to export.',
        nargs='?', default='out.csv')
        
    # Convert Namespace to dict.    
    args = vars(parser.parse_args())
    filterer = LgermFilterer()
    filterer.process_csv(args.pop('infile'), args.pop('outfile'))
