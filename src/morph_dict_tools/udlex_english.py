from morph_dict_tools.universal import *
import pandas as pd

def prepareEnglishDict(upos_filter=None, verbose=False):
    """
    Prepare the English dictionary (Apertium and enlex). """
    cols = ["i", "j", "form", "lemma", "upos", "cpos", "ufeat", "something"]
    print('read and process apertium') if verbose else None
    apertium = pd.read_csv('data/morph/UDLexicons.0.2/UDLex_English-Apertium.conllul', delimiter="\t", names=cols, error_bad_lines=False)
    apertium = apertium.drop(apertium[~apertium.i.isin([0,'0'])].index)
    apertium = apertium.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        apertium = apertium[apertium.upos.isin(upos_filter)]
    apertium = apertium.drop_duplicates()

    print('read and process enlex') if verbose else None
    enlex = pd.read_csv('data/morph/UDLexicons.0.2/UDLex_English-EnLex.conllul', delimiter="\t", names=cols, error_bad_lines=False)
    enlex = enlex.drop(enlex[~enlex.i.isin([0,'0'])].index)
    enlex = enlex.drop(['i','j','something'], axis=1)
    if upos_filter is not None:
        enlex = enlex[enlex.upos.isin(upos_filter)]
    enlex = enlex.drop_duplicates()

    print('concatenate both and create feat dicts') if verbose else None
    english_morph = pd.concat([apertium,enlex], ignore_index=True).drop_duplicates()
    english_morph['ufeatdict'] = english_morph.apply(lambda r:featStringToDict(r.ufeat),axis=1)
    return english_morph

import json
def prepareWordLists():
    first_ipa_letters=set()
    words_starting_with_ju = set()
    word_to_ipa_strings = dict()
    first_ipa_letters_to_words = dict()
    with open("data/morph/wiktextract/en/kaikki.org-dictionary-English.json", "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            orig_ipas = [s['ipa'] for s in entry['sounds'] if 'ipa' in s] if 'sounds' in entry else []
            ipas = []
            for ipa in orig_ipas:
                if ipa[0] in ["/","["]:
                    ipa = ipa[1:]
                while ipa[0] in ['ˈ', 'ˌ']:
                    ipa = ipa[1:]
                ipas.append(ipa)
            for ipa in ipas:
                if ipa[0] in ["/","["]:
                    ipa = ipa[1:]
                first_ipa_letters.add(ipa[0])
                if ipa[0] not in first_ipa_letters_to_words:
                    first_ipa_letters_to_words[ipa[0]] = set()
                first_ipa_letters_to_words[ipa[0]].add(entry['word'])
            if entry['word'].lower().startswith('u') and 'sounds' in entry:
                # ipas = [s['ipa'] for s in entry['sounds'] if 'ipa' in s]
                for ipa in ipas:
                    if ipa.startswith('ju') or ipa.startswith("/ˈj"):
                        words_starting_with_ju.add(entry['word'])
            word = entry['word']
            if word not in word_to_ipa_strings:
                word_to_ipa_strings[word] = set()
            word_to_ipa_strings[word].update(set(orig_ipas))
    en_ipa_consonants = ['b', 'c', 'd', 'f', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't','v','w','x', 'z', 'ŋ', 'ʒ', 'ç', 'ð', 'ɕ', 'ɖ', 'ɡ', 'ɫ', 'ɬ', 'ɯ', 'ɲ', 'ɸ', 'ɻ', 'ɾ', 'ʁ', 'ʃ', 'ʈ','ʍ', 'ʔ', 'ʙ', 'ˀ', 'θ', 'χ','ẽ','q','ɓ', 'ɦ', 'ʋ']
    en_ipa_vowels = ['a', 'e', 'i', 'o', 'u', 'y', 'ä', 'æ', 'õ', 'ĩ','ũ', 'ɐ','ɑ', 'ɒ', 'ɔ', 'ɘ', 'ə', 'ɚ', 'ɛ','ɜ', 'ɝ', 'ɤ', 'ɨ', 'ɵ', 'ʉ', 'ʊ', 'ʌ','ø', 'ɞ']
    en_ipa_others = [' ', '(', '-', '~', 'ǀ','ǃ', 'ɪ', 'ɹ','ː']
    not_sorted_yet = sorted([l for l in first_ipa_letters if l not in en_ipa_consonants and l not in en_ipa_vowels and l not in en_ipa_others])
    # print(len(not_sorted_yet), sorted(not_sorted_yet))
    words_starting_with_vowel = set()
    words_starting_with_consonants = set()
    for ipa_start, words in first_ipa_letters_to_words.items():
        if ipa_start in en_ipa_vowels:
            words_starting_with_vowel.update(words)
        elif ipa_start in en_ipa_consonants:
            words_starting_with_consonants.update(words)
    present_in_both = sorted({x for x in words_starting_with_vowel if x in words_starting_with_consonants})

    remove_from_vowels_list = []
    remove_from_consonants_list = []
    for word in present_in_both:
        if len(word) == 1:
            remove_from_consonants_list.append(word)
        elif word[0] in ["A", "I", "a"]:
            remove_from_consonants_list.append(word)
        elif word[0] in ["E", "c", "d"]:
            remove_from_vowels_list.append(word)
    remove_from_vowels_list += ['had', 'hang', 'hangnail', 'has', 'hasta', 'have', 'haver', 'he', 'her', 'herbal', 'herbary', 'hers', 'herself', 'him', 'his', 'language', 'languages', 'unionised', 'unionized', 'would', 'xennial','yeast', 'yem', 'yere', 'smail', 'thank you']
    remove_from_consonants_list += ['xor', 'olive']
    for word in remove_from_consonants_list:
        if word in words_starting_with_consonants:
            words_starting_with_consonants.remove(word)
    for word in remove_from_vowels_list:
        if word in words_starting_with_vowel:
            words_starting_with_vowel.remove(word)
    with open('data/morph/wiktextract/en/words_starting_with_consonants.txt', 'w') as f:
        f.write('\n'.join(sorted(words_starting_with_consonants)))
    with open('data/morph/wiktextract/en/words_starting_with_vowels.txt', 'w') as f:
        f.write('\n'.join(sorted(words_starting_with_vowel)))
    print('words starting with consonants: ', len(words_starting_with_consonants))
    print('words starting with vowels: ', len(words_starting_with_vowel))

class EnglishMorphDict(MorphDict):
    def __init__(self, upos_filter=None, verbose=True):

        # prepare the lexicon df
        lex = prepareEnglishDict(upos_filter=upos_filter, verbose=verbose)
        
        # create dict from df
        self.upos2lemma2ufeatdictandform = create_lexicon_dict_from_df(lex, verbose=verbose)

        # basic stuff
        self.num_entries = lex.shape[0]
        self.upos_filter = upos_filter
        self.consonants = 'bcdfghjklmnpqrstvwxyz'
        del lex

        # create the lists of words starting with consonstants/vowels
        prepareWordLists()

        # load the lists of words starting with consonants/vowels
        with open('data/morph/wiktextract/en/words_starting_with_consonants.txt', 'r') as f:
            self.words_starting_with_consonants = [w.lower() for w in f.read().splitlines()]
        with open('data/morph/wiktextract/en/words_starting_with_vowels.txt', 'r') as f:
            self.words_starting_with_vowels = [w.lower() for w in f.read().splitlines()]
        


    def lang_specific_lookup(self, token, candidatesWithLemma, targetufeats):

        upos = token['upos']
        if upos == "VERB": 
            if targetufeats.get('VerbForm') =='Fin':
                targetufeats.pop('VerbForm')
            if targetufeats.get('Tense') =='Past':
                targetufeats.pop('Person', None)
                targetufeats.pop('Number', None)
        
        forms = [form for form,ufeatdict in candidatesWithLemma if all1in2(targetufeats,ufeatdict)]
        return forms

    def word_starts_with_consonant(self, word):
        """True if word is in the list of words with consonants."""
        return word in self.words_starting_with_consonants
    
    def word_starts_with_vowel(self, word):
        """True if word is in the list of words with vowels."""
        return word in self.words_starting_with_vowels

    def word_likely_starts_with_consonant(self, word):
        """True if word is in the list of words with consonants, or if it starts with a consonant letter."""
        return self.word_starts_with_consonant(word) or word[0] in self.consonants
    
    def word_likely_starts_with_vowel(self, word):
        """True if word is in the list of words with vowels, or if it doesnt start with a vowel letter."""
        return self.word_starts_with_vowel(word) or word[0] not in self.consonants

    