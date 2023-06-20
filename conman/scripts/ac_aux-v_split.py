#!/usr/bin/python3

# This file contains the 'script' function for processing a
# concordance with at least two keywords, the first of which is aux and
# the second of which is v.

def script(annotator):
	hit = annotator.hit
    if len(hit.kws) >= 2:
        hit.tags['aux_form'] = hit.kws[0]
        hit.tags['verb_form'] = hit.kws[-1]
        hit.tags['aux_lemma'] = hit.kws[0].tags.get('lemma', '')
        hit.tags['verb_lemma'] = hit.kws[-1].tags.get('lemma', '')
