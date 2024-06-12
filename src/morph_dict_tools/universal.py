import pickle




def all1in2(dict1,dict2):
    """true if all k,v pairs in dict1 are in dict2"""
    return all([dict2.get(k)==v for k,v in dict1.items()])

def featStringToDict(featString, verbose=False):
    """Turns a UD feature string into a dictionary.

    If the featString is '_', returns an empty dictionary.
    If verbose, print if a k,v pair can't be parsed.

    :param featString: string of features, e.g. "Number=Sing|Case=Nom"
    :return: dictionary of features, e.g. {"Number":"Sing","Case":"Nom"}
    """
    if featString=='_':
        return dict()
    split = featString.split('|')
    if len(split)==0:
        return dict()
    for s in split:
        if len(s.split('=')) != 2:
            print(split) if verbose else None
            return dict()
    result = {k.split('=')[0]: k.split("=")[1] for k in split}
    return result


def create_lexicon_dict_from_df(df, verbose=False):
    """Create a dictionary from a dataframe.
    
    The dataframe should have the columns "lemma", "upos", "ufeat", "form".
    The dictionary will have the format
    upos -> lemma -> [list of (form, ufeatdict)]

    :param df: dataframe with the columns "lemma", "upos", "ufeat", "form"
    :param verbose: if True, print progress
    :return: dictionary of the format described above
    """

    upos2lemma2ufeatdictandform = dict()
    print('turn dataframe into dict. Might take a few minutes') if verbose else None
    print('Number of entries to convert: ', df.shape[0]) if verbose else None
    for ix, row in df.iterrows():
        if verbose and ix % 250000 == 0:
            print(ix) if verbose else None
        if row.upos not in upos2lemma2ufeatdictandform:
            upos2lemma2ufeatdictandform[row.upos] = dict()
        if row.lemma not in upos2lemma2ufeatdictandform[row.upos]:
            upos2lemma2ufeatdictandform[row.upos][row.lemma] = []
        upos2lemma2ufeatdictandform[row.upos][row.lemma].append((row.form, row.ufeatdict))
    return upos2lemma2ufeatdictandform

def load_morphdict_from_pickle(lang):
    """Load a morphdict from a picle file (with no upos filter)"""
    if lang == 'ar':
        return pickle.load(open('data/morph/pickles/ArabicMorphDict.pickle', 'rb'))
    elif lang == 'de':
        return pickle.load(open('data/morph/pickles/GermanMorphDict.pickle', 'rb'))
    elif lang == 'en':
        return pickle.load(open('data/morph/pickles/EnglishMorphDict.pickle', 'rb'))
    elif lang == 'fr':
        return pickle.load(open('data/morph/pickles/FrenchMorphDict.pickle', 'rb'))
    elif lang == 'id':
        return pickle.load(open('data/morph/pickles/IndonesianMorphDict.pickle', 'rb'))
    elif lang == 'ru':
        return pickle.load(open('data/morph/pickles/RussianMorphDict.pickle', 'rb'))
    elif lang == 'tr':
        return pickle.load(open('data/morph/pickles/TurkishMorphDict.pickle', 'rb'))
    elif lang == 'zh':
        return pickle.load(open('data/morph/pickles/ChineseMorphDict.pickle', 'rb'))
    else:
        raise ValueError('lang not supported')

class MorphDict():
    def __init__():
        pass

    def lookup(self, lemma, token):
        """returns a list of all forms that match the given lemma and the tokens's upos and 
        have all the token's ufeats.
        
        First, some language-unspecific steps are performed. Then, the lookup is perfoemd in the
        language-specific subclass. 

        :param lemma: the lemma to look up. I.e., the lemma of the forms that are returned
        :param token: the token at which the replacement happens (the token which gets a new form/lemma)
        :return: a list of all forms that match the given lemma and the tokens's upos and ufeats
        """

        # determine candidates (universal)
        upos = token['upos']
        targetufeats = dict() if token['feats'] is None else token['feats'].copy() 
        forms = []
        if upos not in self.upos2lemma2ufeatdictandform:
            return forms
        if lemma not in self.upos2lemma2ufeatdictandform[upos]:
            return forms
        candidatesWithLemma = self.upos2lemma2ufeatdictandform[upos][lemma]
        if "ArabicMorphDict" in str(type(self)):
            return [lemma]
        # filter based on ending with '-' - occurs in de and en so far
        old_form = token['form']
        candidatesWithLemma = [c for c in candidatesWithLemma if c[0].endswith('-') == old_form.endswith('-')]
        # determine forms (language specific)
        return self.lang_specific_lookup(token, candidatesWithLemma, targetufeats)

    def lang_specific_lookup(self, token, candidatesWithLemma, targetufeats):
        """only implemented in subclasses"""
        pass
    
    def __len__(self):
        return self.num_entries
