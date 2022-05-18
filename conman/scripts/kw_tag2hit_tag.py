#!/usr/bin/python3

# This file contains the 'script' function for raising keyword tags to 
# hit-level tags.

def script(hit, tags=[]):
    # Tags should be a list of (kw_tag, hit_tag) pairs
    for kw_tag, hit_tag in tags:
        l = []
        for kw in hit.kws:
            l.append(kw.tags.get(kw_tag))
        hit.tags[hit_tag] = '_'.join(l)
    return hit