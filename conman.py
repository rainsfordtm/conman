#!/usr/bin/python3
################################################################################
# Concordance Manager (ConMan)
# © Tom Rainsford, Institut für Linguistik/Romanistik, 2022-
################################################################################

import os.path, argparse
from conman.importers import *
from conman.exporters import *
from conman.mergers import *
from conman.tokenizers import *
from conman.concordance import load_concordance
from configparser import ConfigParser

class Error(Exception):
    """
    Parent class for errors defined in this module.
    """
    pass

class ConfigError(Error):
    """
    Raised where some aspect of the configuration doesn't pass the sanity test.
    """
    pass

class Launcher():
    """
    Class to launch a concordance conversion.
    
    Attributes:
    -----------
    cnc (concordance.Concordance):          The base concordance.
    exporter (exporters.Exporter):          Exporter for the base concordance.
    importer (importers.Importer):          Importer for the base concordance.
    other_cnc (concordance.Concordance):    The other concordance to merge.
    other_importer (importers.Importer):    Importer for other_cnc.
    merger (mergers.ConcordanceMerger):     Merger for cnc and other_cnc.
    path_in (str):                          Path to the base concordance.
    path_out (str):                         Path to the output file.
    path_other (str):                       Path to the other concordance.
    path_save (str):                        Path to which concordance should be saved.
    workflow (configparser.ConfigParser)    ConfigParser containing data read for workflow.
    
    
    Methods
    -------
    launch(self):
        Runs the conversion.
    """
    
    def __init__(self, path_in, path_out):
        """
        Class to initialize attributes.
        """
        self.path_in = path_in
        self.path_out = path_out
        self.path_other, self.path_save = '', ''
        self.cnc, self.other_cnc = None, None
        self.importer, self.other_importer = None, None
        self.exporter = None
        self.merger = None
        self.workflow = None
        
    def _initialize_from_path(self):
        # Uses the path variables to set importers, exporters and mergers
        if os.path.splitext(self.path_in)[1] in CONCORDANCE_EXTS:
            self.cnc = load_concordance(self.path_in)
        else:
            self.importer = get_importer_from_path(self.path_in)
        if self.path_other:
            if os.path.splitext(self.path_other)[1] in CONCORDANCE_EXTS:
                self.other_cnc = load_concordance(self.path_other)
            else:
                self.other_importer = get_importer_from_path(self.path_other)
        if self.other_cnc or self.other_importer:
            self.merger = ConcordanceMerger()
        if os.path.splitext(self.path_out)[1] not in CONCORDANCE_EXTS:
            self.exporter = get_exporter_from_path(self.path_out)
        else:
            self.path_save = self.path_out
            
    def _initialize_from_workflow(self):
        # TODO
        # 1. Read default section
        for key in ['importer', 'other_importer', 'exporter']:
            value = self.workflow.get('DEFAULT', key, fallback='')
            if value:
                try:
                    eval('self.' + key + ' = ' + value + '()')
                except:
                    raise ConfigError('{} "{}" not recognized'.format(key, s))
        # 2. Read importer and other_importer sections
        for section, importer in [
            ('importer', self.importer), ('other_importer', self.other_importer)
        ]:
            # Only read if the importer has been set.
            if not importer: continue
            # Read the values
            for key in ['lcx_regex', 'keywds_regex', 'rcx_regex', 'ref_regex']:
                value = self.workflow.get(section, key, fallback='')
                if value:
                    eval('importer.' + key + "=r'''" + value + "'''")
            value = self.workflow.get(section, 'tokenizer', fallback='')
            if value:
                eval('importer.tokenizer=' + value + '()')
            if isinstance(importer, TableImporter):
                value = self.workflow.get(section, 'TI_dialect', fallback='')
                if value:
                    importer.dialect = value
                value = self.workflow.get(section, 'TI_has_header', fallback='')
                if value:
                    importer.has_header = True if value.lower() == 'true' else False
                value = self.workflow.get(section, 'TI_fields', fallback='')
                if value:
                    importer.fields = value.split(',')
                    importer.ignore_header = True
            if isinstance(importer, BaseTreeImporter):
                value = self.workflow.get(section, 'BT_keyword_attr', fallback='')
                if value:
                    importer.keyword_attr = value
            if isinstance(importer, PennOutImporter):
                value = self.workflow.get(section, 'Pn_keyword_node_regex', fallback='')
                if value:
                    eval("importer.keyword_node_regex=r'''" + value + "'''")
        # 3. Read exporter section (TODO)
                    
    def launch(self):
        """
        Runs the conversion.
        """
        # 1. Initalization
        if self.workflow:
            self._initialize_from_workflow()
        else:
            self._initialize_from_path()
        # 2. Loading and importing
        if not self.cnc:
            if self.importer:
                self.cnc = self.importer.parse(self.path_in)
            else:
                raise ConfigError('Cannot load or import an input concordance.')
        if not self.other_cnc and self.other_importer and self.path_other:
            self.other_cnc = self.other_importer.parse(self.path_other)
        if self.path_other and not self.other_cnc:
            raise ConfigError('Cannot load or import the concordance to merge.')
        # 3. Merging
        if self.other_cnc:
            if not self.merger: self.merger = ConcordanceMerger()
            self.cnc = merger.merge(self.cnc, self.other_cnc)
        # 4. Exporting and saving
        if self.path_save:
            cnc.save(self.path_save)
        if self.exporter and self.path_out:
            exporter.export(self.cnc, self.path_out)
        if not self.path_save and not self.exporter:
            raise ConfigError('Cannot save or export the result.')

def main(path_in, path_out, path_other='', path_workflow='', save=False):
    """
    Builds and runs a Launcher object.
    
    Parameters:
    -----------
    path_in (str):          Path to main input file.
    path_out (str):         Path to output file.
    path_merge (str):       Path to secondary input file.
    path_workflow (str):    Path to workflow configuration file.
    """
    launcher = Launcher(path_in, path_out)
    if save:
        launcher.path_save = os.path.splitext(path_out)[0] + CONCORDANCE_EXTS[0]
    if path_other:
        launcher.path_other = path_other
    if path_workflow:
        cfg = ConfigParser()
        cfg.read_file(path_workflow)
        launcher.workflow = cfg
    launcher.launch()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Runs a concordance transformation operation using the command line ' + \
        'arguments and the workflow configuration file.'
        )
    parser.add_argument('infile', help='Input file to load or import.')
    parser.add_argument('outfile', help='Output file to save or export.',
        nargs='?', 
        default='out.cnc'
    )
    parser.add_argument('-m', '--merge', nargs='?', default='',
        help='Concordance to merge with input file.')
    
    parser.add_argument('-w', '--workflow', nargs='?', default='',
        help='Workflow configuration file.')
    
    parser.add_argument('-s', '--save', action='store_true', 
        help='Saves the concordance to the same path as the exported file even ' + \
        'if an exporter is given in the workflow file or if outfile is not of ' + \
        'type .cnc.'
    )
    
    # Convert Namespace to dict.
    args = vars(parser.parse_args())
    
    launcher = Launcher()
    main(args.pop('infile'), args.pop('outfile'), args.pop('merge'),
        args.pop('workflow'), args.pop('save'))
