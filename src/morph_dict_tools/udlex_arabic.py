from morph_dict_tools.universal import *
import pandas as pd

def prepareArabicDict(upos_filter=None, verbose=False):
    """Prepare the Arabic dictionary (Apertium).
    """

    print('preprocess apertium') if verbose else None
    ar1 = "data/morph/UDLexicons.0.2/UDLex_Arabic-Apertium-E.conllul"
    cols = ["i", "j", "form", "lemma", "upos", "cpos", "ufeat", "something"]
    apertium = pd.read_csv(ar1, names=cols, delimiter="\t", index_col=False)
    apertium = apertium.drop(apertium[~apertium.i.isin([0,'0'])].index)
    apertium = apertium.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        apertium = apertium[apertium.upos.isin(upos_filter)]
    apertium = apertium.drop_duplicates()
    print('ap   : ', apertium.shape) if verbose else None
    
    apertium['ufeatdict'] = apertium.apply(lambda r:featStringToDict(r.ufeat),axis=1)
    return apertium

class ArabicMorphDict(MorphDict):
    def __init__(self, upos_filter=None, verbose=True):

        # prepare the lexicon df
        lex = prepareArabicDict(upos_filter=upos_filter, verbose=verbose)

        # basic stuff
        self.num_entries = lex.shape[0]
        self.upos_filter = upos_filter

        # create dict from df
        self.upos2lemma2ufeatdictandform = create_lexicon_dict_from_df(lex, verbose=verbose)
        del lex
    
    def lang_specific_lookup(self, token, candidatesWithLemma, targetufeats):
        targetufeats.pop('Definite', None)
        forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        if len(forms)==0 and token["upos"] == "VERB":
            # drop aspect, Fin Verbform and Ind Mood
            targetufeats.pop("Aspect", None)
            targetufeats.pop("VerbForm") if targetufeats.get("VerbForm") == "Fin" else None
            targetufeats.pop("Mood") if targetufeats.get("Mood") == "Ind" else None
            forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        return forms
