#!/usr/bin/python3

import argparse, os, os.path, sys

def run(cmd):
    """Runs a command and checks exit status"""
    status = os.waitstatus_to_exitcode(os.system(cmd))
    if status != 0:
        sys.exit(status)

def main(infile, outfile, workflow):
    conman_path = os.path.join(os.path.dirname(__file__), os.pardir)
    conman_call = os.path.join(conman_path, 'conman.py')
    if workflow:
        wf_path = os.path.join(os.getcwd(), workflow)
    else:
        wf_path = os.path.join(conman_path, 'workflows', 'wf_pennout2csv.cfg')
    s = ' '.join([conman_call, '-w', wf_path, infile, outfile])
    print('Calling conman')
    print(s)
    run(s)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Uses ConMan to convert a Penn .out file to a .csv table.'
        )
    parser.add_argument('infile', help='Input .out file.')
    parser.add_argument('outfile', help='Output .csv file.')
    parser.add_argument('-w', '--workflow', nargs=1, default=[''],
        help='Workflow configuration file.')
    
    # Convert Namespace to dict.
    args = vars(parser.parse_args())
    workflow = args.pop('workflow')[0] if 'workflow' in args else ''
    main(args.pop('infile'), args.pop('outfile'), workflow)
