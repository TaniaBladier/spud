import os, sys
sys.path.append(os.getcwd() + '/src/')

import pandas as pd
import wiktextract
from morph_dict_tools.universal import *
from morph_dict_tools.wiktextract_french import *

def prepareFrenchDict(upos_filter=None, verbose=False):
    """Prepare the French dictionary (Apertium and Lefff)."""

    fr1 = "data/morph/UDLexicons.0.2/UDLex_French-Apertium-E1000-6.conllul"
    fr2 = "data/morph/UDLexicons.0.2/UDLex_French-Lefff.conllul"
    cols = ["i", "j", "form", "lemma", "upos", "cpos", "ufeat", "something"]

    print('read and preprocess apertium') if verbose else None
    apertium = pd.read_csv(fr1, names=cols, delimiter="\t", index_col=False, error_bad_lines=False)
    apertium = apertium.drop(apertium[~apertium.i.isin([0,'0'])].index)
    apertium = apertium.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        apertium = apertium[apertium.upos.isin(upos_filter)]
    apertium = apertium.drop_duplicates()

    print('read and preprocess lefff') if verbose else None
    # rm problematic lines
    with open(fr2, 'r') as f:
        lines = f.read().splitlines()
    # line 22
    lines = lines[:22] + lines[23:]
    with open(fr2+"prepr", 'w') as f:
        f.write('\n'.join(lines))
    lefff = pd.read_csv(fr2+"prepr", names=cols, delimiter="\t", index_col=False, error_bad_lines=False)
    lefff = lefff.drop(lefff[~lefff.i.isin([0,'0'])].index)
    lefff = lefff.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        lefff = lefff[lefff.upos.isin(upos_filter)]
    lefff = lefff.drop_duplicates()

    print('ap   : ', apertium.shape) if verbose else None  
    print('lefff: ', lefff.shape) if verbose else None 
    print('concatenate both and create feat dicts') if verbose else None
    print('merge apertium and lefff') if verbose else None
    french = pd.concat([apertium,lefff], ignore_index=True)
    french = french.drop_duplicates()
    print('french: ', french.shape) if verbose else None
    # force as str
    french["form"] = french["form"].astype(str)
    french['ufeatdict'] = french.apply(lambda r:featStringToDict(r.ufeat),axis=1)
    return french

class FrenchMorphDict(MorphDict):
    def __init__(self, upos_filter=None, verbose=True):

        # prepare the lexicon df
        lex = prepareFrenchDict(upos_filter=upos_filter, verbose=verbose)

        # basic stuff
        self.num_entries = lex.shape[0]
        self.upos_filter = upos_filter

        # create dict from df
        self.upos2lemma2ufeatdictandform = create_lexicon_dict_from_df(lex, verbose=verbose)
        del lex

        self.wiktionary = FrenchWiktionary()
    
    def lang_specific_lookup(self, token, candidatesWithLemma, targetufeats):
        
        forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        return forms
