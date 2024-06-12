import os, sys
sys.path.append(os.getcwd() + '/src/')

import pickle

from morph_dict_tools.udlex_german import *
from morph_dict_tools.udlex_english import *
from morph_dict_tools.udlex_french import *
from morph_dict_tools.udlex_arabic import *
from morph_dict_tools.udlex_russian import *

if __name__=='__main__':
    os.makedirs('data/morph/pickles/', exist_ok=True)

    morphdictClasses = [EnglishMorphDict, FrenchMorphDict, GermanMorphDict, RussianMorphDict, ArabicMorphDict] # [ArabicMorphDict] # [EnglishMorphDict, FrenchMorphDict, GermanMorphDict, RussianMorphDict] # [ArabicMorphDict]
    for morphdict in morphdictClasses:
        print('loading ', morphdict.__name__)
        md = morphdict()
        print('saving ', morphdict.__name__)
        pickle.dump(md, open('data/morph/pickles/' + md.__class__.__name__ + '.pickle', 'wb'))
