Concordance Manager (ConMan)
============================

Concordance management and generation tools for SILPAC H1 WP2.
© Tom Rainsford, Institut für Linguistik/Romanistik, University of Stuttgart 2022-

[https://sites.google.com/site/rainsfordtm/home]{https://sites.google.com/site/rainsfordtm/home}


## 1. Introduction

The Concordance Manager (ConMan) is a command-line Python tool designed to 
post-process data extracted from linguistic corpora in the form of a KWIC
(Keyword in Context) concordance of some form.

It is designed to read this data from a variety of different input formats,
process it in a flexible and user-configurable way, and output the result in
different formats for further study.

### 1.1 Data

The ConMan manages data in the form of a **Concordance**. A concordance is
defined as a list of **Hits**, i.e. short sections of text corresponding to 
a particular search criterion. Each Hit consists of a list of **Tokens**.

Within each Hit, the ConMan stores and processes the following information:
	* the tokens in the hit;
	* the keyword or keywords within the hit, as distinct from the context;
	* any number of user-defined annotations attached to the hit as a whole;
	* tokens in the "core context" of the hit (see TODO).

For each Token within a hit, the ConMan can store any number of annotations
(part of speech, lemma, dependency parse data in Conll format, etc.)

Please note that the ConMan cannot store constituency data from
corpora parsed in the Penn-Treebank format. Although it can input hits
identified in in CorpusSearch .out files, the syntactic constituency data is
(mostly) lost during the conversion into a concordance.

### 1.2 Modules

The ConMan has four core modules which are called in the following order 
each time it is run.
	1. Importer: imports the primary concordance from an input file. If the
	Importer module isn't run, the primary concordance must be loaded from a
	.cnc file saved by ConMan.
	2. Merger: Imports a secondary concordance and merges it with the 
	primary concordance. This can be used to add or remove hits from the
	primary concordance or to add annotations to existing hits.
	3. Annotator: Adds user-defined annotations to the primary concordance.
	4. Exporter: exports the primary concordance to an output file. If the
	'-s' file is passed on the command line, it also saves a .cnc file
	containing the primary concordance.
	
	
	

### 1.3 Workflow files


Using ConMan to convert Penn .out file to a PSD file
----------------------------------------------------

ConMan can convert the output of a CorpusSearch .out file to a concordance-style .csv table
with the following command:

./conman.py -w workflows/wf_pennout2csv.cfg myfile.out myfile.csv

The out file MUST include node numbers!

Two parameters must be correctly set in order for this to work:

1. You need to give ConMan a regular expression to identify the node number of the keyword(s) node
from the comment preceding the tree. For example, if you are interested in non-finite verb forms
and your out file contains comments such as the following:
```
11 IP-INF:  11 IP-INF, 16 VX, 12 NP-SBJ
```
your regex should identify the string "16". It must also *name* the group containing number 
16 as "keyword_node" using the symbolic group name syntax from the [Python 3 re library](https://docs.python.org/3/library/re.html).
The correct regex in this case is:
```
\s(?P<keyword_node>[0-9]+)\sVX,
```
The regex can either be set using the PO\_keyword\_node\_regex setting in the importer section of the
workflow file or by including "PO\_keyword\_node\_regex=\<regex\>" (no whitespace!) in the remark section of the
.out file (tip: this is copied directly from the remark section of the .q file).

2. You need to instruct ConMan how to interpret the token strings, since CorpusSearch tokens often include
lemmas. This is done by modifying the lcx_regex setting in the importer section of the workflow file.
The regex must as a minimum identify the symbolic group "word".


