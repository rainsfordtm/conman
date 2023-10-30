# Concordance Manager (ConMan)

Concordance management and generation tools for SILPAC H1 WP2.

© Tom Rainsford, Institut für Linguistik/Romanistik, University of Stuttgart, October 2023

[https://silpac.uni-mannheim.de/](https://silpac.uni-mannheim.de/)
[https://sites.google.com/site/rainsfordtm/home](https://sites.google.com/site/rainsfordtm/home)

## 1. Introduction

The Concordance Manager (ConMan) is a command-line Python tool designed to 
post-process data extracted from linguistic corpora in the form of a KWIC
(Keyword in Context) concordance of some form.

It is designed to read this data from a variety of different input formats,
process it in a flexible and user-configurable way, and output the result in
different formats for further study.

## 2. What the ConMan does

### 2.1 Data

The ConMan manages data in the form of a **Concordance**. A concordance is
defined as a list of **Hits**, i.e. short sections of text corresponding to 
a particular search criterion. Each Hit consists of a list of **Tokens**.

Within each **Hit**, the ConMan stores and processes the following information:
* the tokens in the **Hit**;
* the keyword or keywords within the **Hit**, as distinct from the context;
* any number of user-defined annotations attached to the **Hit** as a whole;

For each **Token** within a **Hit**, the ConMan can store any number of annotations
(part of speech, lemma, dependency parse data in Conll format, etc.)

### 2.2 Modules

The ConMan has four core modules which are called in the following order 
each time it is run.
1. **Importer**: imports the primary concordance from an input file. If the
Importer module isn't run, the primary concordance must be loaded from a
.cnc or .cnc.gz file saved by ConMan. See [section 4](#4-importers-and-exporters).
2. **Merger**: Imports a secondary concordance and merges it with the 
primary concordance. This can be used to add or remove hits from the
primary concordance or to add annotations to existing hits.
See [section 5](#5-merging).
3. **Annotator**: Adds user-defined annotations to the primary concordance.
See [section 6](#6-annotating).
4. **Exporter**: exports the primary concordance to an output file. If the
`-s` flag is passed on the command line, it also saves a .cnc file
containing the primary concordance. If a `-z` flag is also passed, it
compresses the .cnc file and saves it as a .cnc.gz file.
See [section 4](#4-importers-and-exporters).
	
### 2.3 Workflow files

Workflow files are configuration files which tell the ConMan what to do:
+ which modules should be run;
+ which importers and exporters should be used and which parameters
should be passed to the importer and exporter;
+ how **Hits** from two concordances should be merged;
+ which script should be used to annotate the concordance.
	
The workflow file is passed using the `-w` argument on the command line, e.g.:
```
./conman.py -w my_workflow.cfg in_file.csv out_file.csv
```
See [`workflows/workflow.cfg`](workflows/workflow.cfg) for full
documentation of the structure of a workflow file.

It is optional but *highly* recommended to use a workflow file. If the ConMan
is run without a workflow file, it will use the file extensions
to guess what the user wants it to do. All importers, exporters, and mergers will
use default parameters. The result is unlikely to be what you want, unless the
task is a very simple one.

## 3. Some sample tasks

### 3.1 The unannotated corpus

You've extracted a concordance using a regex from an unannotated corpus but
would like to tag and lemmatize the keywords to check whether or not the data
you've extracted is what you really want.

+ Pass 1:
	+ Import the data, probably with a `TableImporter`
	+ Export the data in a one-token-per-line format to feed to the tagger,
	using the `TokenListExporter`
	+ Save the concordance by setting the `-s` flag on the command line.
+ Next, run the tagger/lemmatizer on the one-token-per-line data.
+ Pass 2:
	+ Reload your original concordance from the .cnc file, i.e. no Importer necessary
	+ Use the `TokenListImporter` as the `other_importer` to import the tagged and
	lemmatized data as a second concordance.
	+ Merge the two concordances using the `TextMerger` to inject the new 
	tags into the old concordance.
	+ Annotate the concordance using the `KeywordTagAnnotator` to project the
	token-level `pos` and `lemma` tags on the keyword to a hit-level tag.
	+ Export the concordance using the `TableExporter`.
	
Try this out as a demo task!
```
# Pass 1
demo_tasks/bfm-rnn-pass-1.py demo_tasks/bfm-rnn-pass-1.csv out.txt
# Pass 2
demo_tasks/bfm-rnn-pass-2.py demo_tasks/bfm-rnn-pass-2.cnc demo_tasks/bfm-rnn-pass-2.txt out.csv
```
	
### 3.2. The quick parse

You've found all the tokens of the verbs you're looking for in a well-lemmatized
but unparsed corpus, but now you want to know which of the approximately 
20000 hits have a direct object. Luckily, you have a good dependency parser.

+ Pass 1:
	+ Import the data, probably with a `TableImporter`.
	+ Export the data using the `ConllExporter`.
	    + You may want to limit yourself to the "core context" to
	    speed up the parsing process (see [section 7](#7-core-context)).
	    + Use `CE_hit_end_token` to add a special symbol or punctuation
	    mark at the end of each hit so this can be recovered after parsing.
	+ Also save your concordance by passing the `-s` flag on the command line.
+ Next, run the parser on the Conll data.
+ Prepare a short Python script to identify whether or not a direct object
is present from the Conll annotation
    + Check out [demo_tasks/bfm-parse-pass-2-annotator-script.py](demo_tasks/bfm-parse-pass-2-annotator-script.py).
+ Pass  2:
	+ Reload your original concordance from the .cnc file, i.e. no Importer necessary
	+ Use the `ConllImporter` as the `other_importer` to import the tagged and
	lemmatized data as a second concordance.
	+ Merge the two concordances using the `ConcordanceMerger` to inject the Conll 
	tags into the old concordance. Set `CI_hit_end_token` to recognize the
	special symbol used to mark the end of the hit.
	+ Annotate the concordance using your Python script to add a tag to each
	hit for the presence/absence of a direct object.
	+ Export the concordance using the `TableExporter`.
	
Try this out as a demo task!
```
# Pass 1
demo_tasks/bfm-parse-pass-1.py demo_tasks/bfm-parse-pass-1.csv out.conllu
# Pass 2
demo_tasks/bfm-parse-pass-2.py demo_tasks/bfm-parse-pass-2.cnc demo_tasks/bfm-parse-pass-2.conllu out.csv
```
(Observant users will note that the results are rather unsatisfactory, but this
reflects wrong output from the parser with the sample data rather than an issue with ConMan.)
	
### 3.3 The Penn .out headache

You've got CorpusSearch to find the structure you're looking for in a 
parsed corpus but you've ended up with a massive unreadable .out file.

+ Setting up the .out file
	+ Make sure CorpusSearch is set to print node numbers (see [section 4.5](#4-5-the-pennoutexporter)).
+ ConMan workflow
	+ Import the data using the `PennOutImporter`.
	    + Set the `PO_keyword_node_regex` to identify the keyword and other keynodes.
	    + Set the `lcx_regex` to split off the lemmas from
	    the form of the token.
	+ Enable the `PennAnnotator` to add extra information about the
	keyword and other keynodes to the **Hit**.
	+ Export the data using the `TableExporter`.
	
Try this out as a demo task!
```
demo_tasks/penn-out-to-csv.py demo_tasks/penn-out-to-csv.out out.csv
```

## 4. Importers and Exporters

### 4.1 Types of Importers and Exporters

The ConMan implements the following importers and exporters:

| Importer            | Exporter            | Extension | Description                                                               |             
| ---                 | ---                 | ---       | ---                                                                       |
| `Importer`          | `Exporter`          | .txt      | Generic: lines are **Hits**, **Tokens** are separated by whitespace.      |
| `TableImporter`     | `TableExporter`     | .csv      | Generic for concordances in tabular format, one line per **Hit**.         |
| `TokenListImporter` | `TokenListExporter` | .txt      | Generic one **Token** per line format.                                    |
|                     | `LGermExporter`     | .txt      | Specific one **Token** per line export for the LGeRM lemmatizer.          |
| `ConllImporter`     | `ConllExporter`     | .conllu   | CoNLL format for dependency parsing.                                      |
| `BaseTreeImporter`  |                     | .xml      | Generic importer for treebank corpora, must be converted to BaseTree XML. |
| `PennOutImporter`   |                     | .out      | Importer for Penn format .out files (constituency parsing).               |

For every importer and exporter, the `encoding` parameter sets the correct text 
encoding. Default is `utf-8`.

### 4.2 Importing and exporting Tokens

Every Importer and Exporter has methods for solving the two fundamental
problems when importing tokens from a source:
1. tokenization, i.e. how are tokens separated from each other?
2. token-level annotation, i.e. what is the token itself and what is annotation?
	
In the ConMan, problem 1 is generally solved using built-in methods and classes
while problem 2 is fully user-customizable using a regular expression.

#### 4.2.1 Token annotation

When exporting data from a corpus, it's common for annotation such as 
part-of-speech annotation or lemmas to be printed alongside the token in the
output. Here are some formats that I came across while writing the ConMan:
+ **BFM via TXM web**: customizable, tags separated by underscores, e.g. `de_PRE_|de|`
+ **FRANTEXT**: customizable, tags separated by slashes, e.g. `de/PRE/de`
+ **Lemmatized Penn corpora**: encoded in the .psd file as part of the token 
	itself, various formats, e.g. `de@t=PRE@l=de`.
	
The importer should be instructed to parse these forms so that the annotation is
split off from the form of the token itself. This is done using a Python 3
regular expression containing symbolic group names, passed as the parameter
`lcx_regex` in the parameter file. Here's an example of some possible regexes:
```
# For the BFM, e.g. de_PRE_|de|
lcx_regex=(?P<word>[^_]+)_(?P<pos_bfm>[^_]+)_(?P<lemma_bfm>.*) 

# For FRANTEXT, e.g. de/PRE/de
lcx_regex=(?P<word>[^/]+)/(?P<pos_ft>[^/]+)/(?P<lemma_ft>.*) 

# For Penn corpora, e.g. de@t=PRE@l=de
lcx_regex=(?P<word>[^@]+)@t=(?P<pos>[^@]+)@l=(?P<lemma>.*)
```
Note that the name `word` is reserved for the form of the token. Everything
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
and `rcx_regex` parameters respectively. Otherwise the `lcx_regex` 
regex is used for everything.

When exporting from ConMan, you can use the `tok_fmt` parameter in the `exporter`
section of the workflow file to add
tags to the surface form of each **Token**, if you wish. `tok_fmt` takes a
Python format string with a single position argument, which is the **Token** object.
So, for example, to print `de_PRE_de` instead of just `de`, set `tok_fmt`
as follows (assuming that your concordance contains imported `pos` and `lemma`
tags):
```
tok_fmt={0}_{0.tags[pos]}_{0.tags[lemma]}
```

Note that setting the `kw_fmt` parameter allows keywords to have a different
format to context tokens.

#### 4.2.2 Tokenization

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

### 4.3 Using the tabular importers and exporters

The `TableImporter` and `TableExporter` are the primary ways of importing and
exporting data from the ConMan, since they best represent the underlying
Concordance format that the software is designed to manage.  

By default, the `TableImporter` requires .csv files to be comma-delimited, UTF-8
encoded, and with a header row containing the following field names IN 
CAPITALS:
+ `KEYWORDS`: Keyword tokens only
+ `LCX`:      Tokens preceding keywords only
+ `RCX`:      Tokens following keywords only
+ `REF`:      Reference
Alternatively, if there are no keywords, a single `TOKENS` field may be passed.

If your .csv file is not set up like this, you need to set the correct
parameters in the workflow file:
+ `TI_dialect`:   `excel` (default) or `tab` for tab-delimited files without quotes.
+ `TI_has_header`: set to `false` if no header
+ `TI_fields`:	if there's no header, or if your header doesn't contain
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
of the hit, are exported, with `UUID`, `REF`, `LCX`, `KEYWORDS`, and `RCX`
preceding all tags, which are in alphabetical order.

### 4.4 Using the one-token-per-line exporter and importers

In a typical workflow, one-token-per-line formats should only be used if
you need to call an external tool like a lemmatizer, tagger or parser, because
they are not designed for storing concordance data. In particular, there
is no consistent way of representing either **Hits** or keywords.

The one-token-per-line exporters are: `TokenListExporter` (generic), 
`LGermExporter` (for the LGerm lemmatizer), `ConllExporter`.
The one-token-per-line importers are: `TokenListImporter` (generic),
`ConllImporter`.

#### 4.4.1 Using `hit_end_token`

All one-token-per-line exporters and importers accept a `hit_end_token` 
parameter in the workflow file. If provided, the value of `hit_end_token`
is used as a dummy token to signal the end of a **Hit**. It is added to exported
data and deleted when data is imported. The `hit_end_token` should be unique
and not found elsewhere in the corpus.

For example, to ensure that the end of every **Hit** is marked by the token "?!"
in a CoNLL file, add the following to the workflow file:
```
[importer]
TL_hit_end_token=?!

[exporter]
CE_hit_end_token=?!
```

If no `hit_end_token` is given, the importers and exporters interpret empty
lines in the file to signal the beginning and end of Hits.

#### 4.4.2 Exporting and importing annotated tokens

Use the `lcx_regex` (Importer) and the `tok_fmt` (Exporter) parameters if
the one-token-per-line file contains annotation. For example, to parse
a tab-delimited file containing the token, part-of-speech tag, and the
lemma on each line (i.e. TreeTagger output), set the following in the
workflow file:
```
[importer]
lcx_regex=(?P<word>[^\t]+)\t(?P<pos>[^\t]+)\t(?P<lemma>[^\t]+)
```
To export a tab-delimited list of token-lemma pairs, set the following in 
the workflow file:
```
[exporter]
tok_fmt={0}\t{0.tags[lemma]}
```

#### 4.4.3 Further parameters

The behaviour of the `ConllExporter` is highly configurable, and it is possible
to set the name of the tag which should be exported in each column of the
Conll file with the parameters `CE_lemma`, `CE_cpostag`, etc.

The `split_hits` parameter specifies the maximum number of hits to include
in a single file, splitting the export across several files where necessary.
It's used by the LGermExporter to avoid exceeded the file size limit for
LGeRM.

### 4.5 The PennOutImporter

> **Tip**: For a tabular export, make a workflow using the 
> [`PennAnnotator`](#6-2-pennannotator) and the
> [`TableExporter`](#4-3-using-the-tabular-importers-and-exporters).

#### 4.5.1 Basic use
	
The PennOutImporter requires a CorpusSearch .out file **with node numbers**,
which are enabled by setting `print_indices: true` in the .q file of CorpusSearch.

Most users will only have to bother with one or perhaps two parameters:
+ `PO_keyword_node_regex`: identifies one node as the keyword.
+ `lcx_regex`: to parse the tokens if they contain further annotation (see [section 4.2.1](#4-2-1-token-annotation) above)

`PO_keyword_node_regex` is a Python regex which identifies a node number
in each hit and assigns it the symbolic group name `keyword_node`.
For example, let's say the structure you're searching for contains a non-finite 
verb and you want this to be the keyword in your concordance.
Your .out file will contains comments such as the following before each hit:
```
11 IP-INF:  11 IP-INF, 16 VX, 12 NP-SBJ
```
Your regex therefore needs identify the string "16", which is the node number
of the non-finite verb `VX`.
The correct regex in this case is:
```
\s(?P<keyword_node>[0-9]+)\sVX,
```
The regex can either be set using the `PO_keyword_node_regex` setting in the
importer section of the workflow file or by including
`PO_keyword_node_regex=<regex>` (no whitespace!) in the remark section of the
.out file (tip: this is copied directly from the remark section of the .q file).

**NEW 01/02/23**: You can name further nodes from your query using
the same technique and ConMan will tag all tokens dominated by that
node on import. For example, if you are also interested in the NP subject
node, you can set the following regex:
```
\s(?P<keyword_node>[0-9]+)\sVX,\s(?P<subject>[0-9]+)\sNP-SBJ
```
Use the [`PennAnnotator`](#6-2-pennannotator) to visualize these tokens in a table.

#### 4.5.2 Advanced use

The `PennOutImporter` is based on tools I developed before the ConMan and so
triggers a multi-stage workflow:
1. Generic conversion of bracketed tree format to an .xml format (basetree),
which is managed using the [`treetools.basetree`](treetools/basetree.py) module.
2. Pre-import script called to prepare the .xml file for import as a 
concordance.
3. Generic import of the .xml file using the `BaseTreeImporter`.
	
The pre-import script is, by default, the `script()` method of
[`scripts.pennout2cnc.py`](scripts/pennout2cnc.py). It does the following:
+ identifies the keyword(s) by adding an XML attribute `KEYWORD="1"`,
`KEYWORD="2"` to each keyword in the sentence;
+ identifies tokens dominated by other nodes in the regex using and
tags them by adding the XML attribute `KEYNODE_<group_name>="1"` to
each token;
+ deletes the `CODE` nodes (they clutter up the text);
+ identifies the `ID` node and copies it to the id attribute of the
`<tree>` element node where the `BaseTreeImporter` will look for it,
deleting the `ID` node as a token;
+ creates `ancestors` and `deep_ancestors` XML attributes for each token, which 
list the cat tags of ancestor constituents in the surface and deep structure
respectively, e.g. `ancestors="IP-MAT|IP-INF"` for a non-finite verb.
+ creates `ancestors_cs_id` and `deep_ancestors_cs_id` XML attributes,
which list the node numbers of ancestor constituents in the surface and
deep structure respectively, e.g. `ancestors_cs_id="1|6"`.
+ parses the CorpusSearch tokens using the `lcx_regex` parameter, storing all 
non-word tags as XML attributes, e.g. `lemma="aller"`.
	
All  XML attributes created by this script are added to the `.tags`
dictionary of each **Token** in the concordance by the `BaseTreeImporter`
and so are available to Annotator scripts.

If you want to modify the stage 2 pre-import script, here are some tips:
+ first, enable `PO_dump_xml` in the `[advanced]` section of the 
workflow file. This dumps the .xml file after it's been processed by
the pre-import script in step 2, which is helpful for debugging.
+ second, copy the default `pennout2cnc.py` file to any folder on
your computer and modify the `PO_script_file` parameter in the `[advanced]`
section of the workflow file to point to it.

Your workflow file should look like this:
```
[advanced]
PO_dump_xml=/home/myusername/tmp.xml
PO_script_file=/home/myusername/myscripts/mypennout2cnc.py
```
Instead of the default, the `PennOutImporter` will now call the `script()` method
of the module in `PO_script_file`.

To understand how to manipulate the .xml file using the basetree library,
please take a look at [doc/basetree_api.odt](doc/basetree_api.odt). The
`tree` argument passed to the script is an instance of the
`basetree.BaseTree` class, which inherits from `xml.dom.minidom.Document`.

## 5. Merging

The Merger modifies one concordance (the main concordance) using data from 
another concordance. It is the only ConMan module which allows combining or
comparing two sources of data and has three main functions:
1. adding or updating hit-level annotation in the main concordance;
2. adding or deleting hits in the main concordance;
3. adding or updating token-level annotation in the main concordance.
	
To enable the Merger module, pass the name of the file containing the other
concordance on the command line using the `-m` argument, e.g. `-m other_concordance.csv`

Scenario 1 is the default behaviour for a Merger and without configuration this
is all it will do. It is intended to inject annotation added by the user in
the form of an extra column in a .csv table back into the main concordance.

If you're using a workflow file, you should set the type of Merger 
and the type of Importer in the `setup` section and then configure the Importer,
if necessary, in the `other_importer` section, e.g.:
```
[setup]
merger=ConcordanceMerger
other_importer=TableImporter

[other_importer]
TI_dialect=tab
TI_fields=REF,LCX,KEYWORDS,RCX
```

### 5.1 Scenario 1: adding annotation to hits

This is the default scenario: the user has added a column of extra annotation
to a concordance in tabular format and we wish to read it back into the 
database.

By default, the merger assumes that the two concordances contain the same
**Hits** in the same order. If this isn't the case, you need to instruct the
Merger how to match the **Hits** in the two concordances. There are two options:
use the UUID (best) which ConMan attributes to every **Hit**, or use the reference
string from the corpus. This can be configured using the `CM_match_by` 
parameter, e.g.:
```
[setup]
merger=ConcordanceMerger

[merger]
CM_match_by=uuid #match by UUID
#CM_match_by=ref #match by reference
```

Additionally, if the user has updated existing tags, for example by correcting
automatic annotation, you must set the `CM_update_hit_tags` parameter to
`True` in order to update the annotation in the main concordance, e.g.:
```
[merger]
CM_update_hit_tags=True
```

### 5.2 Scenario 2: adding and deleting Hits

To use a second concordance to add or delete **Hits** from the main concordance,
you should first set the `CM_match_by` parameter as described above, since
the Merger needs to know which **Hits** are the same. Then, use `CM_add_hits=True`
to add any extra hits from the other concordance to the main concordance, 
and `CM_del_hits=True` to delete any **Hits** from the main concordance which aren't
in the other concordance.

For example, if the user has edited a table and deleted all **Hits** which aren't
relevant, set up the workflow file as follows:
```
[setup]
merger=ConcordanceMerger

[merger]
CM_match_by=uuid
CM_del_hits=true
```

### 5.3 Scenario 3: Updating token annotation

In principle, updating token-level annotation is achieved simply by setting
`CM_merge_tokens` (to add new tags) and `CM_update_token_tags` (to update
existing token-level tags) to `true` in the workflow file.

In practice, if we are updating token-level annotation, it's probably
because the other concordance is being read from a one-token-per-line format
file containing the output of a parser, tagger or lemmatizer. Since these
formats don't store token IDs and don't often provide a means to mark the
division into **Hits**, the biggest problem for the Merger is to match up the
**Tokens** and **Hits** in the two concordances.

In the remainder of the section, I assume that the other concordance is
being read from a one-token-per-line format file. In *all* these cases,
the two concordances should contain the same **Hits** in the same order.

#### 5.3.1 Identical tokenization with `hit_end_token` for hit division

The best case scenario is:
+ you've set a `hit_end_token` to mark the division into **Hits** and,
+ the third-party tool hasn't modified the tokenization.

Let's say your one-token-per-line format file marks
the end of a **Hit** with a special punctuation mark, e.g. `?!`, and none of the
third-party tools have retokenized the text. In this case, the following
settings in the workflow file will update the token-level annotation
successfully:
```
[setup]
merger=ConcordanceMerger
other_importer=ConllImporter

[other_importer]
TL_hit_end_token=?! # set the distinctive token which delimits hits in the Conll file

[merger]
CM_merge_tokens=True # add the Conll annotation to the original tokens
CM_update_token_tags=True # update any existing tags with the new values (optional) 
```

This is the quickest and most reliable method for updating **Token** tags.

#### 5.3.2 Retokenized, use `hit_end_token` for hit division

Even if you set a `hit_end_token`, some third-party tools will retokenize
the original text when processing it. If this is the case, you need to 
switch to using the `TextMerger`, which calls the *Tokenized Text Aligner*
on each **Hit** to ensure that the **Tokens** are correctly matched
(see [https://sourceforge.net/projects/tokenized-text-aligner/](https://sourceforge.net/projects/tokenized-text-aligner/)).

In this scenario, your workflow file will look like this:
```
[setup]
merger=TextMerger
other_importer=ConllImporter

[other_importer]
#TL_hit_end_token=?! # DON'T set a hit_end_token for the importer...

[merger]
TM_hit_end_token=?! # DO set a hit_end_token for the merger!
```

Note that the `hit_end_token` must be passed only to the Merger and not
to the Importer.

#### 5.3.3 No `hit_end_token`

If you have no `hit_end_token`, perhaps because it degrades parser or
lemmatizer performance, the `TextMerger` reverts to treating the two concordances
as texts. The alignment will be much, much slower.

Here are the correct settings for merging a concordance where the division
into **Hits** is irrecoverable:
```
[setup]
merger=TextMerger
```

## 6. Annotating

The Annotator module is designed for the automatic generation hit-level
annotation and the intention is that the user will write their own scripts here.

Four annotation scripts are provided with ConMan:
+ `KeywordTagAnnotator`: raises some token-level tags from the keyword to the
level of the **Hit**.
+ `PennAnnotator`: adds columns containing properties of the keywords
and other keynodes identified in a CorpusSearch query. Only works
for concordances created with the [`PennOutImporter`](#4-5-the-pennoutimporter).
+ `LgermFilterAnnotator`: disambiguates LGeRM lemmas by part-of-speech
+ `CoreContextAnnotator`: tags a subset of tokens in the hit as the core context.
See [section 7](#7-core-context).

### 6.1 KeywordTagAnnotator

If there's only one keyword in the concordance, it's useful for the
concordance to contain a separate column for its part-of-speech and lemma tag.
This is achieved by using the `KeywordTagAnnotator`.
The script takes a single argument: a list of `(keyword_tag, hit_tag)`
tuples specifying which **Token** tags to copy to the **Hit**.

For example, the following workflow file settings will project the
part-of-speech and lemma of the keyword to the **Hit** level:
```
[setup]
Annotator=KeywordTagAnnotator

[annotator]
tags=[('pos', 'kw_pos'), ('lemma', 'kw_lemma')]
```

Export the result using the `TableExporter` to get a .csv concordance with
extra `kw_pos` and `kw_lemma` columns.

### 6.2 PennAnnotator

The `PennAnnotator` adds properties of the keyword(s) and other keynodes
identified in a CorpusSearch query to the **Hit**:
+ `<node_name>_cat`: the Penn category tag for the node;
+ `<node_name>_form`: the string of tokens dominated by the node.

The `PennAnnotator` script takes a single `tags` argument, which is a
list of token-level tags which should be added to the hit for each
keynode.

For example, let's assume a CorpusSearch query identifying verbs and
subject. The CorpusSearch results look something like this:
```
11 IP-INF:  11 IP-INF, 16 VX, 12 NP-SBJ
```
The following workflow file will generate a tabular concordance
with extra columns `kw_cat`, `kw_lemma`, `subject_form`, `subject_cat`,
`subject_lemma` from the .out file:
```
[setup]
Importer=PennOutImporter
Annotator=PennAnnotator
Exporter=TableExporter

[importer]
# Parses a Penn token with extra attributes @rl= and @rt=
lcx_regex=(?P<word>.+)@rl=(?P<lemma_rnn>.+)@rt=(?P<pos_rnn>.+)
# Identifies the verb as a keyword and the subject as the keynode "subject"
PO_keyword_node_regex=\s(?P<keyword_node>[0-9]+)\sV[^,]+,\s(?P<subject>[0-9]+)\sNP-SBJ

[annotator]
# Add a tag containing the "lemma_rnn" of each token in the keyword
# or other keynodes to the concordance.
tags=['lemma_rnn']
```

### 6.3 Writing your own script

#### 6.3.1 Calling the script

Create a Python file anywhere on your computer for the script. The script
is enabled using the following settings in the workflow file:
```
[setup]
annotator=Annotator # Run an annotator

[annotator]
# Any parameters you specify here will be passed as keyword arguments to
# your script.

[advanced]
annotator_script_file=/home/me/myscripts/myannotator.py
```

#### 6.3.2 The `script()` method

Your script file must contain a `script()` method with two positional
arguments, `annotator` and `hit` and it must return a hit. Here is
the minimal "do nothing" function:
```
def script(annotator, hit):
    return hit
```

#### 6.3.3 Understanding Hits and Tokens

The `conman.concordance.Hit` object passed to the script is a list of 
`conman.concordance.Tokens` and has the following attributes:
+ `hit.kws`: list of keywords
+ `hit.tags`: dictionary of all hit-level tags
+ `hit.ref`: reference from corpus
+ `hit.uuid`: UUID (not writable)
For further documentation, see the DOCSTRING in [conman/concordance.py](conman/concordance.py).

**Tokens** are *sort of* strings (they're UserStrings), which means that sometimes
they behave like strings (e.g. two tokens are equal (`==`) if they have the same
form even if they have different IDs) and sometimes they don't (e.g. when
passed to `re.match` or `join`). So get into the habit of using `str()` if
you need a string and `is` rather than `==` if you want to be sure it's the
same **Token**.

**Tokens** have a single attribute, the dictionary `.tags`, which contains
all token-level annotation.

Here's a commented version of the `KeywordTagAnnotator` script to demonstrate
how **Hits** and **Tokens** can be processed by the Annotator module:
```
def script(annotator, hit, tags=[]):
    # The tags keyword argument is specified in the workflow file.
    # It contains a list of (kw_tag, hit_tag) tuples.
    # The main loop iterates over the tags list passed to the script.
    for kw_tag, hit_tag in tags:
    	# Initialize an empty list, which we will use to store the 
    	# keyword tags (there may be more than one keyword).
        l = []
        # Iterate over the keyword tokens, which are listed in hit.kws. 
        for kw in hit.kws:
	    # Check whether the token-level tag we are looking for is present
	    # in the .tags dictionary of this token (this avoids KeyError).
            if kw_tag in kw.tags:
            	# Append the value of kw_tag to l
                l.append(kw.tags[kw_tag])
            else:
            	# If the value wasn't in the .tags dictionary, append an empty string
            	# to l instead.
                l.append('')
	# Now, join the values for kw_tag for all the keywords with an
	# underscore and store this value in the hit.tags dictionary 
	# under the key provided by the user in the tags list.
        hit.tags[hit_tag] = '_'.join(l)
    # Return the modified hit.
    return hit
```

More complex queries are possible, for example using dependency annotation
imported from Conll or the `ancestors` attributes provided by the 
`PennOutImporter` to search for specific syntactic structures. All such token-level
annotation can be read from the `.tags` dictionary of the **Token**.

### 6.4 Advanced use cases

**New 30/10/23**. For advanced use cases, two further annotators are
provided to be used in combination with user-defined annotation scripts:
+ `EvaluationAnnotator`: Identical to the default annotator but contains
a `.summary` attribute (dictionary), the contents of which is displayed
on the screen once all the hits have been processed. What the `.summary`
dictionary contains is defined in the user-defined annotation script. 
Intended to store statistics documenting changes made by the annotation
script.
+ `ConllAnnotator`: Identical to the default annotator but provides some
useful functions for querying Conll-U tags encoded in the concordance
which can be accessed from the user-defined annotation script.

For further documentation, see the DOCSTRING in the
[conman/annotators.py](conman/annotators.py) file.

## 7. Core Context

It's possible to mark a subset of the **Tokens** in a **Hit** as the "core context".
The core context must include all the keywords. The idea behind this
is to speed up the parsing process by only exporting tokens within the same
clause as the keyword to a parser.

To use the core context, the following procedure must be used:
+ Pass 1:
	+ annotate the core context by using the `CoreContextAnnotator`
	+ export the result in Conll format by using the `ConllExporter` with
	`core_cx` set to `True` and a suitable `hit_end_token`
+ Pass 2:
	+ re-import the parsed data using the `ConllImporter`;
	+ merge the parsed data into the original concordance using the
	`ConcordanceMerger` or the `TextMerger` with `CM_core_cx` or `TM_core_cx`
	respectively set to `True`.
	
The `CoreContextAnnotator` requires a `delim_pattern` argument.
This is a regular expression which matches all tokens which are assumed to
delimit the core context, e.g. punctuation marks.

The following workflow file will import a concordance from a .csv file and
create a Conll file for a parser containing (i) all tokens after the last
punctuation to the left of the keyword(s), (ii) the keywords, (iii)
all tokens preceding the first punctuation after the keywords.
```
[setup]
importer=TableImporter
annotator=CoreContextAnnotator
exporter=ConllExporter

[exporter]
core_cx=true
CE_hit_end_token=?!

[annotator]
delim_pattern=r'[.,!?;:]' # Matches punctuation tokens
```

Once parsed, the following workflow file re-imports the Conll annotation,
adds the `head` and `deprel` tags of the keyword to the **Hit** 
and re-exports the result as a table.
```
[setup]
other_importer=ConllImporter
merger=ConcordanceMerger
annotator=KeywordTagAnnotator
exporter=TableExporter

[other_importer]
TL_hit_end_token=?!

[merger]
CM_core_cx=True
CM_merge_tokens=True

[annotator]
tags=[('conll_DEPREL', 'deprel'), ('conll_HEAD', 'head')]
```
