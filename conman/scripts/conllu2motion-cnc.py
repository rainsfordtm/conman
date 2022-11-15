#!/usr/bin/python3

# This file contains the 'script' function for identifying sentences from 
# conll input with a motion verb as their root.

mv_lemmas = [
	'abattre',
	'aller',
	'amener',
	'apporter',
	'arriver',
	'assëoir',
	'avoyer',
	'chasser',
	'chevaucher',
	'choir',
	'conduire',
	'coucher',
	'courir',
	'départir',
	'descendre',
	'échapper',
	'entrer',
	'envoyer',
	'errer',
	'fuir',
	'gésir',
	'issir',
	'jeter',
	'lever',
	'mander',
	'mener',
	'mettre',
	'monter',
	'mouvoir',
	'partir',
	'passer',
	'pendre',
	'poindre',
	'porter',
	'puyer',
	'remettre',
	'repairer',
	'retourner',
	'retraire',
	'revenir',
	'saillir',
	'sëoir',
	'suivre',
	'tourner',
	'traire',
	'trépasser',
	'venir',
	'virer',
	'voler'
]

def script(annotator, hit):
    
    if hit.kws:
        lemma = hit.kws[0].tags['conll_LEMMA']
        hit.tags['mv_head'] = 'y' if lemma in mv_lemmas else 'n'
        hit.tags['kw_lemma'] = lemma
    else:
        hit.tags['mv_head'] = '--'
        hit.tags['kw_lemma'] = '--'
    