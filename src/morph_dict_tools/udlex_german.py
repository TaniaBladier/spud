import pandas as pd
from morph_dict_tools.universal import *


def prepareGermanDict(upos_filter=None, verbose=False):
    """prepare a big lexicon dataframe for german
    
    based on Apertium and Delex
    
    :param upos_filter: if not None, only include entries with this upos
    :param verbose: if True, print progress
    :return: a dataframe with the lexicon
    """
    de1 = "data/morph/UDLexicons.0.2/UDLex_German-Apertium.conllul"
    de2 = "data/morph/UDLexicons.0.2/UDLex_German-DeLex.conllul"
    cols = ["i", "j", "form", "lemma", "upos", "cpos", "ufeat", "something"]

    # prepare apertium lexicon
    print('read and preprocess apertium') if verbose else None
    apertium = pd.read_csv(de1, names=cols, delimiter="\t", index_col=False, error_bad_lines=False)
    apertium = apertium.drop(apertium[~apertium.i.isin([0,'0'])].index)
    apertium = apertium.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        apertium = apertium[apertium.upos.isin(upos_filter)]
    apertium = apertium.drop_duplicates()

    # prepare delex lexicon
    print('read and preprocess delex') if verbose else None
    # rm problematic lines
    with open(de2, 'r') as f:
        lines = f.read().splitlines()
    # lines 34, 35, 36, 37 need to go
    lines = lines[:33] + lines[38:]
    with open(de2+"prepr", 'w') as f:
        f.write('\n'.join(lines))
    
    delex = pd.read_csv(de2+"prepr", names=cols, delimiter="\t", index_col=False, encoding_errors="ignore", error_bad_lines=False)
    delex = delex.drop(delex[~delex.i.isin([0,'0'])].index)
    delex = delex.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        delex = delex[delex.upos.isin(upos_filter)]
    delex = delex.drop_duplicates()

    # merge apertium and delex
    print('ap: ', apertium.shape) if verbose else None  
    print('del: ', delex.shape) if verbose else None 
    print('concatenate both and create feat dicts') if verbose else None
    german = pd.concat([apertium,delex], ignore_index=True).drop_duplicates()
    german["ufeat"] = german.apply(lambda r: r.ufeat.replace('Number=SingGender=Masc', 'Number=Sing|Gender=Masc').replace('Number=PlurGender=Masc','Number=Plur|Gender=Masc'), axis=1)
    german['ufeatdict'] = german.apply(lambda r:featStringToDict(r.ufeat),axis=1)

    return german

class GermanMorphDict(MorphDict):
    def __init__(self, upos_filter=None, verbose=True):

        # prepare the lexicon df
        lex = prepareGermanDict(upos_filter=upos_filter, verbose=verbose)

        # basic stuff
        self.num_entries = lex.shape[0]
        self.upos_filter = upos_filter
        self.adj_suffixes = ["er", "em", "en", "e", "es"] 

        # create dict from df
        self.upos2lemma2ufeatdictandform = create_lexicon_dict_from_df(lex, verbose=verbose)
        del lex
    
    def lang_specific_lookup(self, token, candidatesWithLemma, targetufeats):

        upos = token['upos']
        if upos in ["NOUN","PROPN"]:
            targetufeats.pop('Person', None)
        elif upos == "VERB" and targetufeats.get('VerbForm') =='Fin':
            targetufeats.pop('VerbForm')
        
        forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        if upos == "ADJ":
            if len(forms)== 0:
                # Degree=Pos is sometimes missing in the morph lex. Therfore, we add it here
                for form, ufeatdict in candidatesWithLemma:
                    if "Degree" not in ufeatdict:
                        ufeatdict["Degree"] = "Pos"
                forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
            # filter those forms that have the same ending as the replaced form
            # positive / comp. / superlative should be detected by features
            old_ending = self.determine_adj_suffix(token['form'])

            if old_ending in self.adj_suffixes:
                forms_with_same_ending = [form for form in forms if self.determine_adj_suffix(form) == old_ending]
                if len(forms_with_same_ending) > 0:
                    forms = forms_with_same_ending
        return forms

    def determine_adj_suffix(self, adjform):
        """Returns "e" if the adjform ends with "e", 
        otherwise the last two letters of the adjform."""

        if adjform[-1] in self.adj_suffixes:
            return adjform[-1]
        else:
            return adjform[-2:]
    