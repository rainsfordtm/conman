#!/usr/bin/python3

# This file contains the 'script' function for raising keyword tags to 
# hit-level tags.

def script(annotator, tags=[]):
	hit = annotator.hit
    # Tags should be a list of (kw_tag, hit_tag) pairs
    for kw_tag, hit_tag in tags:
        l = []
        for kw in hit.kws:
            if kw_tag in kw.tags:
                l.append(kw.tags[kw_tag])
            else:
                l.append('')
        hit.tags[hit_tag] = '_'.join(l)
