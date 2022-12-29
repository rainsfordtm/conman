Concordance Manager (ConMan)
============================

Concordance management and generation tools for SILPAC H1 WP2.
© Tom Rainsford, Institut für Linguistik/Romanistik, University of Stuttgart 2022-

[https://sites.google.com/site/rainsfordtm/home]{https://sites.google.com/site/rainsfordtm/home}


# 1. Introduction

The Concordance Manager (ConMan) is a command-line Python tool designed to 
post-process data extracted from linguistic corpora in the form of a KWIC
(Keyword in Context) concordance of some form.

It is designed to read this data from a variety of different input formats,
process it in a flexible and user-configurable way, and output the result in
different formats for further study.

# 2. What the ConMan does

## 2.1 Data

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

## 2.2 Modules

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
	
## 2.3 Workflow files

Workflow files are configuration files which tell the ConMan what to do:
	+ which modules should be run;
	+ which importers and exporters should be used (see TODO) and what parameters
	should be passed to the importer and exporter;
	+ how hits from two concordances should be merged;
	+ which script should be used to annotate the concordance.
	
The workflow file is passed using the '-w' argument on the command line, e.g.
```
./conman.py -w my_workflow.cfg in_file.csv out_file.csv
```
See `conman/workflows/workflow.cfg` for full documentation of the structure
of a workflow file.

It is optional but *highly* recommended to use a workflow file. If the ConMan
is run without a workflow file, it will use the file extensions
to guess what the user wants it to do. All importers, exporters, and mergers will
use default parameters. The result is unlikely to be what you want, unless the
task is a very simple one.

# 3. Some sample workflows

# 3.1 The unannotated corpus

You've extracted a concordance using a regex from an unannotated corpus but
would like to tag and lemmatize the keywords to check whether or not the data
you've extracted is what you really want.

+ ConMan, workflow 1:
	+ Import the data, probably with a TableImporter
	+ Export the data in a one-token-per-line format to feed to the tagger,
	using the TokenListExporter
	+ Save the concordance by setting the '-s' flag on the command line:
	you'll need to load it again in Pass 2!
+ Next, run the tagger/lemmatizer on the one-token-per-line data.
+ ConMan, workflow 2:
	+ Reload your original concordance from the .cnc file, i.e. no Importer necessary
	+ Use the TokenListImporter as the `other_importer` to import the tagged and
	lemmatized data as a second concordance.
	+ Merge the two concordances using the TextMerger to inject the new 
	tags into the old concordance.
	+ Annotate the concordance using the KeywordTagAnnotator to project the
	Token-level pos and lemma tags on the keyword to a Hit-level tag.
	+ Export the concordance using the TableExporter.
	
# 3.2. The quick parse

You've found all the tokens of the verbs you're looking for in a well-lemmatized
but unparsed corpus, but now you want to know which of the approximately 
20000 hits have a direct object. Luckily, you have a good dependency parser.

+ ConMan, workflow 1:
	+ Import the data, probably with a TableImporter
	+ Export the data using the ConllExporter. You may want to limit yourself
	to the "core context" to speed up the parsing process (see TODO). Use
	CE_hit_end_token to add a special symbol or punctuation mark at the end
	of each hit so this can be recovered after parsing.
	+ Also save your concordance by passing the '-s' flag on the command line.
+ Next, run the parser on the Conll data.
+ Prepare a short Python script to identify whether or not a direct object
is present from the Conll annotation.
+ ConMan, workflow 2:
	+ Reload your original concordance from the .cnc file, i.e. no Importer necessary
	+ Use the ConllImporter as the `other_importer` to import the tagged and
	lemmatized data as a second concordance.
	+ Merge the two concordances using the ConcordanceMerger to inject the Conll 
	tags into the old concordance. Set TI_hit_end_token to recognize the
	special symbol used to mark the end of the hit.
	+ Annotate the concordance using your Python script to add a tag to each
	hit for the presence/absence of a direct object 
	+ Export the concordance using the TableExporter.
	
# 3.3 The Penn .out headache

You've got CorpusSearch to find the structure you're looking for in a 
parsed corpus but you've ended up with a massive .out file which is basically
unreadable, especially if the CorpusSearch "tokens" have had lemmas added to
them.

+ Setting up the .out file
	+ Make sure CorpusSearch is set to print node numbers (see TODO).
+ ConMan workflow
	+ Import the data using the PennOutImporter. Set the PO_keyword_node_regex to
	identify the keyword node. Set the lcx_regex to split off the lemmas from
	the form of the token.
	+ Export the data using the TableExporter.

# 4. Importers and Exporters

## 4.1 Types of Importers and Exporters

The ConMan implements the following importers and exporters:

Importer          Exporter           Extension   Description
----------------- ------------------ ----------- ------------------------------------------------------------------------
Importer          Exporter           .txt        Generic: lines are hits, tokens are separated by whitespace. 
TableImporter     TableExporter      .csv        Generic for concordances in tabular format, one line per hit
TokenListImporter TokenListExporter  .txt        Generic one token per line format.
                  LGermExporter      .txt        Specific one token per line export for the LGeRM lemmatizer
ConllImporter     ConllExporter      .conllu     CoNLL format for dependency parsing
BaseTreeImporter                     .xml        Generic importer for treebank corpora, must be converted to BaseTree XML
PennOutImporter                      .out        Importer for Penn format .out files (constituency parsing)

For every importer and exporter, the `encoding` parameter sets the correct text 
encoding. Default is `utf-8`.

## 4.2 Importing and exporting Tokens

Every Importer and Exporter has methods for solving the two fundamental
problems when importing Tokens from a source:
	1. tokenization, i.e. how are Tokens separated from each other?
	2. token-level annotation, i.e. what is the Token itself and what is annotation?
	
In the ConMan, problem 1 is generally solved using built-in methods and classes
while problem 2 is fully user-customizable using a regular expression.

### 4.2.1 Token annotation

When exporting data from a corpus, it's common for annotation such as 
part-of-speech annotation or lemmas to be printed alongside the token in the
output. Here are some formats that I came across while writing the ConMan
+ BFM via TXM web: customizable, tags separated by underscores, e.g. `de_PRE_|de|`
+ FRANTEXT: customizable, tags separated by slashes, e.g. `de/PRE/de`
+ Lemmatized Penn corpora: encoded in the .PSD file as part of the token 
	itself, various formats, e.g. `de@t=PRE@l=de`.
	
The importer should be instructed to parse these forms so that the annotation is
split off from the form of the token itself. This is done using a Python 3
regular expression containing symbolic group names, passed as the parameter
`lcx_regex` in the parameter file. Here's an example of some possible regexes:
```
lcx_regex=(?P<word>[^_]+)_(?P<pos_bfm>[^_]+)_(?P<lemma_bfm>.*) # de_PRE_|de|
lcx_regex=(?P<word>[^/]+)/(?P<pos_ft>[^/]+)/(?P<lemma_ft>.*) # de/PRE/de
lcx_regex=(?P<word>[^@]+)@t=(?P<pos>[^@]+)@l=(?P<lemma>.*) # de@t=PRE@l=de
```
Note that the name `word` is reserved for the form of the Token. Everything
else will be stored as a tag.

The same regex-based technique for splitting tokens is used with the
`TokenListImporter` to import tab-separated lists of tokens and pos tags and/or
lemmas such as those exported by the TreeTagger, or the RNNTagger:
```
lcx_regex=(?P<word>[^\t]+)\t(?P<pos>[^\t]+)\t(?P<lemma>[^\t]) # de	PRE	de
```

When exporting from the BFM, it's possible for the form of the tokens in the
left context, right context and in the keywords to be individually set. If
you need a separate regex for keywords and right context, use `kw_regex`
and `rcx_regex` parameters respectively.

When exporting from ConMan, you can use the `tok_fmt` parameter in the `exporter`
section of the workflow file to add
tags to the surface form of each Token, if you wish. `tok_fmt` takes a
Python format string with a single position argument, which is the token.
So, for example, to print `de_PRE_de` instead of just `de`, set `tok_fmt`
as follows (assuming that your concordance contains imported `pos` and `lemma`
tags):
```
tok_fmt={0}_{0.tags[pos]}_{0.tags[lemma]}
```

Note that setting the `kw_fmt` parameter allows keywords to have a different
format to context tokens.

### 4.2.2 Tokenization

By default, the `Importer` and `TableImporter` interpret tokens as being delimited
by whitespace. More source-specific behaviour can be achieved by specifying
a tokenizer in the workflow file.

+ `tokenizer=BfmTokenizer`: For concordances exported from the BFM (TXM web),
	where tokens are not systematically separated by whitespace. It can
	also tokenize output containing annotation, which is marked in the
	output using underscores e.g. `de_PRE_|de|`.
+ `tokenizer=FrantextTokenizer`: For concordances exported from FRANTEXT,
	where tokens may **contain** whitespace. It is essential to use this
	tokenizer when parsing output containing annotation, which is separated
	from the token by a foreslash, e.g. `de/P/de`.
	
The `Exporter` and `TokenExporter` allow the user to specify how tokens
should be separated using the `tok_delimiter` parameter. Default is a single
space.

All other Importers and Exporters deal with pre-tokenized data.

## 4.3 Using the tabular importers and exporters

The TableImporter and TableExporter are the primary ways of importing and
exporting data from the ConMan, since they best represent the underlying
Concordance format that the software is designed to manage.  

By default, the TableImporter requires .csv files to be comma-delimited, UTF-8
encoded, and with a header row containing the following field names IN 
CAPITALS:
	+ KEYWORDS: Keyword tokens only
	+ LCX:      Tokens preceding keywords only
	+ RCX:      Tokens following keywords only
	+ REF:      Reference
Alternatively, if there are no keywords, a single `TOKENS` field may be passed.

If your .csv file is not set up like this, you need to set the correct
parameters in the workflow file:
	+ TI_dialect:   excel (default) or tab for tab-delimited files without quotes.
	+ TI_has_header: set to 'false' if no header
	+ TI_fields:	if there's no header, or if your header doesn't contain
					the fieldnames in the right format, tell ConMan what's in
					each column with a comma delimited list of fields.

For example, to import a tab-delimited concordance exported from the BFM, 
we need to the importer up as follows:
```
[importer]
TI_dialect=tab
TI_fields=REF,LCX,KEYWORDS,RCX
```

When exporting a table, the same three parameters can be set in the export
section of the workflow file, i.e. `TE_dialect`, `TE_header`, `TE_fields`.
`TE_fields` tells the exporter which fields to export and in which order.
By default, all fields, including the fields annotated in the `tags` dictionary
of the hit, are exported, with UUID, REF, LCX, KEYWORDS, and RCX preceding all
tags, which are in alphabetical order.

## 4.4 Using the one-token-per-line exporter and importers

In a typical workflow, one-token-per-line formats should only be used if
you need to call an external tool like a lemmatizer, tagger or parser, because
they are **not** designed for storing concordance data. In particular, there
is no consistent way of representing either Hits or Keywords.




## 4. Merging

## 5. Annotating

## 6. 


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


