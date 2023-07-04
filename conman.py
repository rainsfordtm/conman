#!/usr/bin/python3
################################################################################
# Concordance Manager (ConMan)
# © Tom Rainsford, Institut für Linguistik/Romanistik, 2022-
################################################################################

import os.path, argparse
import importlib.machinery, importlib.util
from conman.importers import *
from conman.exporters import *
from conman.mergers import *
from conman.annotators import Annotator
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
    merger (mergers.Merger):                Merger for cnc and other_cnc.
    annotator (annotators.Annotator):       Annotator for cnc (used after merge).
    path_in (str):                          Path to the base concordance.
    path_out (str):                         Path to the output file.
    path_other (str):                       Path to the other concordance.
    path_save (str):                        Path to which concordance should be saved.
    gz_save (bool):                         Enable gzip compression of saved cnc file.
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
        self.gz_save = False
        self.cnc, self.other_cnc = None, None
        self.importer, self.other_importer = None, None
        self.exporter = None
        self.merger = None
        self.annotator = None
        self.workflow = None
        
    def _initialize_from_path(self):
        # Uses the path variables to set importers, exporters and mergers
        in_splitext = os.path.splitext(self.path_in)
        if in_splitext[1] in CONCORDANCE_EXTS or \
        (in_splitext[1] == '.gz' and os.path.splitext(in_splitext[0])[1] in CONCORDANCE_EXTS):
            self.cnc = load_concordance(self.path_in)
        else:
            self.importer = get_importer_from_path(self.path_in)
        if self.path_other:
            other_splitext = os.path.splitext(self.path_other)
            if other_splitext[1] in CONCORDANCE_EXTS or \
            (other_splitext[1] == '.gz' and os.path.splitext(other_splitext[0])[1] in CONCORDANCE_EXTS):
                self.other_cnc = load_concordance(self.path_other)
            else:
                self.other_importer = get_importer_from_path(self.path_other)
        if self.other_cnc or self.other_importer:
            self.merger = ConcordanceMerger()
        out_splitext = os.path.splitext(self.path_out)
        if out_splitext[1] not in CONCORDANCE_EXTS or \
        (out_splitext[1] == '.gz' and os.path.splitext(out_splitext[0])[1] not in CONCORDANCE_EXTS):
            self.exporter = get_exporter_from_path(self.path_out)
        else:
            self.path_save = self.path_out
            
    def _initialize_from_workflow(self):
        # 1. Read setup section
        for key in ['importer', 'other_importer', 'annotator', 'exporter', 'merger']:
            value = self.workflow.get('setup', key, fallback='')
            if value:
                if key == 'exporter':
                    obj = Exporter.create(value)
                elif key == 'annotator':
                    obj = Annotator.create(value)
                elif key == 'merger':
                    obj = Merger.create(value)
                else:
                    obj = Importer.create(value)
                setattr(self, key, obj)
        # 2. Read importer and other_importer sections
        for section, importer in [
            ('importer', self.importer), ('other_importer', self.other_importer)
        ]:
            # Only read if the importer has been set.
            if not importer: continue
            # Read the values
            for key in ['encoding', 'lcx_regex', 'keywds_regex', 'rcx_regex', 'ref_regex']:
                value = self.workflow.get(section, key, fallback='')
                if value:
                    setattr(importer, key, value)
            value = self.workflow.get(section, 'tokenizer', fallback='')
            if value:
                importer.tokenizer = Tokenizer.create(value)
            if isinstance(importer, TokenListImporter):
                value = self.workflow.get(section, 'TL_hit_end_token', fallback='')
                if value:
                    importer.hit_end_token = value
                value = self.workflow.get(section, 'TL_comment_string', fallback='')
                if value:
                    importer.comment_string = value
            if isinstance(importer, ConllImporter):
                value = self.workflow.get(section, 'CI_head_as_kw', fallback='')
                if value:
                    importer.head_is_kw = True if value.lower() == 'true' else False
            if isinstance(importer, TableImporter):
                value = self.workflow.get(section, 'TI_dialect', fallback='')
                if value:
                    importer.dialect = value
                value = self.workflow.get(section, 'TI_has_header', fallback='')
                if value:
                    importer.has_header = True if value.lower() == 'true' else False
                value = self.workflow.get(section, 'TI_fields', fallback='')
                if value:
                    importer.fields = [x.strip() for x in value.split(',')]
                    importer.ignore_header = True
            if isinstance(importer, BaseTreeImporter):
                value = self.workflow.get(section, 'BT_keyword_attr', fallback='')
                if value:
                    importer.keyword_attr = value
            if isinstance(importer, PennOutImporter):
                value = self.workflow.get(section, 'PO_keyword_node_regex', fallback='')
                if value:
                    importer.keyword_node_regex = value
                    print(importer.keyword_node_regex)
                # Read advanced values for PennOutImporter
                value = self.workflow.get('advanced', 'PO_dump_xml', fallback='')
                if value:
                    importer.dump_xml = value
                value = self.workflow.get('advanced', 'PO_script_file', fallback='')
                if value:
                    name = os.path.splitext(os.path.basename(value))[0]
                    script_module = load_module(name, value)
                    importer.script = script_module.script
        # 3. Read exporter section
        if self.exporter:
            for key in ['encoding', 'tok_fmt', 'kw_fmt', 'tok_delimiter']:
                value = self.workflow.get('exporter', key, fallback='')
                if value:
                    # convert to normal string to allow \n, \s, etc.
                    value = fix_escape_characters(value)
                    setattr(self.exporter, key, value)
            value = self.workflow.getint('exporter', 'split_hits', fallback=0)
            if value:
                self.exporter.split_hits = value
            value = self.workflow.get('exporter', 'core_cx', fallback='')
            self.exporter.core_cx = True if value.lower() == 'true' else False
            if isinstance(self.exporter, TokenListExporter):
                value = self.workflow.get('exporter', 'TL_hit_end_token', fallback='')
                if value:
                    self.exporter.hit_end_token = value
            if isinstance(self.exporter, TableExporter):
                value = self.workflow.get('exporter', 'TE_dialect', fallback='')
                if value:
                    self.exporter.dialect = value
                value = self.workflow.get('exporter', 'TE_header', fallback='')
                if value:
                    self.exporter.header = True if value.lower() == 'true' else False
                value = self.workflow.get('exporter', 'TE_fields', fallback='')
                if value:
                    self.exporter.fields = [x.strip() for x in value.split(',')]
            if isinstance(self.exporter, ConllExporter):
                for key in [
                    'CE_lemma', 'CE_cpostag', 'CE_postag', 'CE_head',
                    'CE_deprel', 'CE_phead', 'CE_pdeprel', 'CE_hit_end_token'
                ]:
                    value = self.workflow.get('exporter', key, fallback='')
                    if value:
                        setattr(self.exporter, key[3:], value)
                value = self.workflow.get('exporter', 'CE_feats', fallback='')
                if value:
                    self.exporter.feats = [x.strip() for x in value.split(',')]
                value = self.workflow.get('exporter', 'CE_split_hit', fallback='')
                if value:
                    self.exporter.split_hit = True if value.lower() == 'true' else False
        # 4. Read merger section
        if self.path_other:
            if isinstance(self.merger, ConcordanceMerger):
                for key in ['CM_add_hits', 'CM_del_hits']:
                    value = self.workflow.get('merger', key, fallback='')
                    if value.lower() == 'true':
                        setattr(self.merger, key[3:], True)
                value = self.workflow.get('merger', 'CM_match_by', fallback='')
                if value in ['uuid', 'ref']: self.merger.match_by = value
                value = self.workflow.get('merger', 'CM_update_hit_tags', fallback='')
                if value.lower() == 'true': self.merger.update_tags = True
                value = self.workflow.get('merger', 'CM_merge_tokens', fallback='')
                if value.lower() == 'true':
                    self.merger.token_merger = TokenMerger()
                    value = self.workflow.get('merger', 'CM_update_token_tags', fallback='')
                    if value.lower() == 'true':
                        self.merger.token_merger.update_tags = True
                    value = self.workflow.get('merger', 'CM_core_cx', fallback='')
                    if value.lower() == 'true':
                        self.merger.token_merger.core_cx = True
                    value = self.workflow.get('merger', 'CM_tok_id_tag', fallback='')
                    if value:
                        self.merger.token_merger.id_tag = value
            if isinstance(self.merger, TextMerger):
                for key in ['TM_threshold', 'TM_ratio']:
                    value = self.workflow.get('merger', key, fallback='')
                    if value:
                        num_value = float(value)
                        setattr(self.merger, key[3:], value)
                value = self.workflow.get('merger', 'TM_hit_end_token', fallback='')
                if value:
                    self.merger.hit_end_token = value
                value = self.workflow.get('merger', 'TM_core_cx', fallback='')
                self.merger.core_cx = True if value.lower() == 'true' else False
        # 5. Manage annotator settings (i.e. changing the script)
        if self.annotator:
            for key in self.workflow.options('annotator'):
                value = self.workflow.get('annotator', key)
                if value:
                    try:
                        self.annotator.kwargs[key] = eval(value)
                    except:
                        raise ConfigError('Error in annotator option "{}={}"'.format(key, value))
            value = self.workflow.get('advanced', 'annotator_script_file', fallback='')
            if value:
                # Load the module
                name = os.path.splitext(os.path.basename(value))[0]
                script_module = load_module(name, value)
                # Update the class method
                Annotator.script = script_module.script
        # 6. Load the concordances if there are no importers or exporters
        # specified in the workflow file.
        if not self.importer:
            try:
                self.cnc = load_concordance(self.path_in)
            except LoadError:
                raise ConfigError('No importer set and cannot load concordance from {}'.format(self.path_in))
        if self.path_other and not self.other_importer:
            try:
                self.other_cnc = load_concordance(self.path_other)
            except LoadError:
                raise ConfigError('No other importer set and cannot load concordance from {}'.format(self.path_other))
        if not self.exporter:
            out_splitext = os.path.splitext(self.path_out)
            if out_splitext[1] in CONCORDANCE_EXTS or \
            (out_splitext[1] == '.gz' and os.path.splitext(out_splitext[0])[1] in CONCORDANCE_EXTS):
                # save don't export
                self.path_save = self.path_out
            else:
                raise ConfigError('No exporter set and out file is not a concordance file.')
            
    def launch(self):
        """
        Runs the conversion.
        """
        # 1. Initalization, including loading.
        if self.workflow:
            self._initialize_from_workflow()
        else:
            self._initialize_from_path()
        # 2. Importing
        print('Loading/importing concordance...')
        if not self.cnc:
            if self.importer:
                self.cnc = self.importer.parse(self.path_in)
            else:
                raise ConfigError('Cannot load or import an input concordance.')
        if not self.other_cnc and self.other_importer and self.path_other:
            self.other_cnc = self.other_importer.parse(self.path_other)
        if self.path_other and not self.other_cnc:
            raise ConfigError('Cannot load or import the concordance to merge or concordance is empty.')
        # 3. Merging
        if self.other_cnc:
            print('Merging concordances...')
            if not self.merger:
                self.merger = ConcordanceMerger()  
            self.merger.cnc = self.cnc
            self.merger.other_cnc = self.other_cnc
            self.cnc = self.merger.merge()
        # 4. Annotating
        if self.annotator:
            print('Annotating concordance...')
            self.cnc = self.annotator.annotate(self.cnc)
        # 5. Exporting and saving
        print('Saving/exporting results.')
        if self.path_save:
            self.cnc.save(self.path_save)
        if self.exporter and self.path_out:
            # Fix output path using the exporters fix_ext method.
            # Prevents idiot errors like typing .cnc as an extension
            # with an exporter specified in the workflow file.
            #print(self.exporter.kw_fmt)
            self.path_out = self.exporter.fix_ext(self.path_out)
            self.exporter.export(self.cnc, self.path_out)
        if not self.path_save and not self.exporter:
            raise ConfigError('Cannot save or export the result.')
        print('Done!')

def main(path_in, path_out, path_other='', path_workflow='', 
    save=False, gz=False):
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
        if gz: launcher.path_save += '.gz'
    if path_other:
        launcher.path_other = path_other
    if path_workflow:
        cfg = ConfigParser()
        with open(path_workflow, 'r') as f:
            cfg.read_file(f)
        launcher.workflow = cfg
    launcher.launch()
    
def load_module(module_name, path):
    """Load arbitrary Python source file"""
    loader = importlib.machinery.SourceFileLoader(module_name, path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
   
def fix_escape_characters(s):
    """
    Interprets escape characters mangled by the config parser.
    """
    s = s.replace('\\n', '\n')
    s = s.replace('\\t', '\t')
    s = s.replace('\\r', '\r')
    return s

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Runs a concordance transformation operation using the command line ' + \
        'arguments and the workflow configuration file.'
        )
    parser.add_argument('infile', help='Input file to load or import.')
    parser.add_argument('outfile', help='Output file to save or export.')
    parser.add_argument('-m', '--merge', nargs=1, default=[''],
        help='Concordance to merge with input file.')
    parser.add_argument('-w', '--workflow', nargs=1, default=[''],
        help='Workflow configuration file.')
    
    parser.add_argument('-s', '--save', action='store_true', 
        help='Saves the concordance to the same path as the exported file even ' + \
        'if an exporter is given in the workflow file or if outfile is not of ' + \
        'type .cnc.'
    )
    parser.add_argument('-z', '--zip', action='store_true',
        help='Gzip compress the .cnc file while saving.'
    )
    # Convert Namespace to dict.
    args = vars(parser.parse_args())
    merge = args.pop('merge')[0] if 'merge' in args else ''
    workflow = args.pop('workflow')[0] if 'workflow' in args else ''
    main(args.pop('infile'), args.pop('outfile'), merge,
        workflow, args.pop('save'), args.pop('zip'))
    

