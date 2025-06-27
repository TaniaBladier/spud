from morph_dict_tools.wiktextract_universal import *

wiktextract_pos_to_upos = {
    'adj':'ADJ', 
    'adv':'VERB',
    'noun':'NOUN', 
    'verb':'VERB'
}

import json
def load_muted_and_aspirated_h_words():

    print('loading muted h words')
    muted = []
    aspirated = []
    with open("data/morph/wiktextract/fr/kaikki.org-dictionary-French.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            word = entry["word"]
            if word.startswith('h'):
                entrystr = str(entry)
                if "mute h" in entrystr:
                    muted.append(word)
                elif "aspirated h" in entrystr:
                    aspirated.append(word)
    muted = sorted(muted)
    aspirated = sorted(aspirated)
    with open('data/morph/wiktextract/fr/muted_h_words.txt', 'w') as f:
        f.write('\n'.join(muted))
    with open('data/morph/wiktextract/fr/aspirated_h_words.txt', 'w') as f:
        f.write('\n'.join(aspirated))
    

class FrenchWiktionary(Wiktionary):

    def __init__(self):
        super().__init__()
        self.lang = 'fr'
        self.pos2word2ipa = dict()
        with open("data/morph/wiktextract/fr/kaikki.org-dictionary-French.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if 'sounds' in entry:
                    pos = entry['pos']
                    word = entry['word']
                    ipas = {d['ipa'] for d in entry['sounds'] if 'ipa' in d}
                    if pos not in self.pos2word2ipa:
                        self.pos2word2ipa[pos] = dict()
                    if word in self.pos2word2ipa[pos]:
                        self.pos2word2ipa[pos][word].update(ipas)
                    else:
                        self.pos2word2ipa[pos][entry['word']] = ipas

        # load muted h words
        load_muted_and_aspirated_h_words()
        with open('data/morph/wiktextract/fr/muted_h_words.txt', 'r') as f:
            self.muted_h_words = set(f.read().splitlines())
        with open('data/morph/wiktextract/fr/aspirated_h_words.txt', 'r') as f:
            self.aspirated_h_words = set(f.read().splitlines())


    def lookup_ipa(self, word, pos=None):
        """Lookup the IPA for a word in the Wiktionary.
        
        :param word: the word to lookup
        :param pos: the part of speech of the word. If None, the word is looked up in all pos.
        :return: a set of IPA strings
        """
        if pos is not None:
            pos = pos.lower()
            if pos not in self.pos2word2ipa:
                return None
            if word not in self.pos2word2ipa[pos]:
                return None
            return self.pos2word2ipa[pos][word]
        else:
            # collect for all pos
            ipas = set()
            for pos in self.pos2word2ipa:
                if word in self.pos2word2ipa[pos]:
                    ipas.update(self.pos2word2ipa[pos][word])
            return ipas


    def is_aspirated_h(self, word):
        """Check if the word is explicitly annotated as an aspirated h."""
        return word in self.aspirated_h_words

    def is_muted_h(self, word):
        """Check if the word is explicitly annotated as a muted h."""
        return word in self.muted_h_words

    def is_probably_muted_h(self, word):
        """Default case: not listed as aspirated"""
        return not self.is_aspirated_h(word) 