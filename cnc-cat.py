#!/usr/bin/python3
################################################################################
# Concordance concatenator for ConMan
# © Tom Rainsford, Institut für Linguistik/Romanistik, 2022-
################################################################################

import argparse, os.path
from conman.concordance import load_concordance, Concordance

def main(infiles, outfile, gz=False):
    """
    Concatenates all the concordances in infiles to a single concordance.
    
    Parameters:
    -----------
    infiles (list):         List of input file paths.
    outfile (str):          Path to output file.
    gz (bool):              Enable/disable gzip compression on
                            output file.
    """
    
    # Step 1. Initialize a new Concordance object
    cnc = Concordance()
    
    # Step 2. Iterate over infiles
    for infile in infiles:
        
        # Step 3. Generate an absolute path
        infile = os.path.abspath(infile)
        
        # Step 4. Load
        in_cnc = load_concordance(infile)
        
        # Step 5. Concatenate. No need to use a merger, this is a 
        # performance-oriented script.
        cnc.extend(in_cnc)
        
    # Step 6. Check outfile path name, splitting off any user ending
    outfile = os.path.splitext(outfile)[0]
    if not outfile.endswith('.cnc'): outfile += '.cnc'
    if gz: outfile += '.gz'
    
    # Step 7. Save concordance
    cnc.save(outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Concatenates .cnc files into one large .cnc file.'
        )
    parser.add_argument('infiles', nargs='*', help='Input files to concatenate.')
    parser.add_argument('-o', '--output', nargs=1, default=['out.cnc'],
        help='Output file.')
    parser.add_argument('-z', '--zip', action='store_true',
        help='Gzip compress the .cnc file while saving.'
    )
    # Convert Namespace to dict.
    args = vars(parser.parse_args())
    outfile = args.pop('output')[0] if 'output' in args else 'out.cnc'
    main(args.pop('infiles'), outfile, args.pop('zip'))
