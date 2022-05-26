Concordance Manager (ConMan)
============================

Concordance management and generation tools for SILPAC H1 WP2.

**Documentation in progress!**

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
\s[0-9]+\sVX,
```
The regex can either be set using the PO\_keyword\_node\_regex setting in the importer section of the
workflow file or by including "PO\_keyword\_node\_regex=\<regex\>" (no whitespace!) in the remark section of the
.out file (tip: this is copied directly from the remark section of the .q file).

2. You need to instruct ConMan how to interpret the token strings, since CorpusSearch tokens often include
lemmas. This is done by modifying the lcx_regex setting in the importer section of the workflow file.
The regex must as a minimum identify the symbolic group "word".


