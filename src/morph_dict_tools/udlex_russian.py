import pandas as pd
from morph_dict_tools.universal import *

def prepareRussianDict(upos_filter=None, verbose=False):
    cols = ["i", "j", "form", "lemma", "upos", "cpos", "ufeat", "something"]
    ru1 = 'data/morph/UDLexicons.0.2/UDLex_Russian-Apertium.conllul'
    print('read and preprocess apertium') if verbose else None
    apertium = pd.read_csv(ru1, names=cols, delimiter="\t", index_col=False)
    if upos_filter is not None:
        apertium = apertium[apertium.upos.isin(upos_filter)]
    apertium.drop_duplicates(inplace=True)
    print('create feat dicts') if verbose else None
    apertium['ufeatdict'] = apertium.apply(lambda r:featStringToDict(r.ufeat),axis=1)
    return apertium

class RussianMorphDict(MorphDict):

    def __init__(self, upos_filter=None, verbose=True):

        # prepare the lexicon df
        lex = prepareRussianDict(upos_filter=upos_filter, verbose=verbose)

        # basic stuff
        self.num_entries = lex.shape[0]
        self.upos_filter = upos_filter

        self.refl_suffixes = ["ся", "сь"]

        # create dict from df
        self.upos2lemma2ufeatdictandform = create_lexicon_dict_from_df(lex, verbose=verbose)
        del lex

    def lang_specific_lookup(self, token, candidatesWithLemma, targetufeats):
        
            
        forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        if len(forms) == 0 and token['upos']=='PROPN':
            targetufeats.pop('Animacy', None)
            forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        if len(forms) == 0 and token['upos'] in ['ADJ', 'ADV'] and targetufeats.get('Degree')=='Pos':
            targetufeats.pop('Degree', None)
            forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        if len(forms) == 0 and token['upos']=='VERB':
            # if the verb token is reflexive ("-ся" oder "-сь"), only replace with reflexive forms
            # and if not, vice versa
            if token["form"][-2:] in self.refl_suffixes:
                candidatesWithLemmaFiltered = [c for c in candidatesWithLemma if c[0][-2:] in self.refl_suffixes]
            else: 
                candidatesWithLemmaFiltered = [c for c in candidatesWithLemma if c[0][-2:] not in self.refl_suffixes]
            
            if targetufeats.get('VerbForm') in ['Fin', None]:
                # eventually do the same for Imp Aspect, Act Voice, Ind Mood?
                targetufeats.pop('VerbForm', None)
                candidatesWithLemmaFiltered = [c for c in candidatesWithLemma if c[1].get('VerbForm') in ['Fin', None]]
                forms = [form for form,ufeatdict in candidatesWithLemmaFiltered if all1in2(targetufeats,ufeatdict)]
            if len(forms) == 0 and targetufeats.get("Aspect") == "Imp":
                targetufeats.pop("Aspect", None)
                candidatesWithLemmaFiltered = [c for c in candidatesWithLemmaFiltered if c[1].get("Aspect") in ["Imp", None]]
                forms = [form for form,ufeatdict in candidatesWithLemmaFiltered if all1in2(targetufeats,ufeatdict)]
            if len(forms) == 0 and targetufeats.get("Mood") in ["Ind", None]:
                targetufeats.pop("Mood", None)
                candidatesWithLemmaFiltered = [c for c in candidatesWithLemmaFiltered if c[1].get("Mood") in ["Ind", None]]
                forms = [form for form,ufeatdict in candidatesWithLemmaFiltered if all1in2(targetufeats,ufeatdict)]
            if len(forms) == 0 and targetufeats.get("Voice") in ["Act", None]:
                targetufeats.pop("Voice", None)
                candidatesWithLemmaFiltered = [c for c in candidatesWithLemmaFiltered if c[1].get("Voice") in ["Act", None]]
                forms = [form for form,ufeatdict in candidatesWithLemmaFiltered if all1in2(targetufeats,ufeatdict)]
        return forms

