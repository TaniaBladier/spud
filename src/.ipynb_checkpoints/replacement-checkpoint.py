import random
import copy

from src.ud_tools import get_token_with_id

def create_replacement_mask(dep_sent, upos_filter=None):
    """Create a mask for a sentence.

    The mask indicates which tokens can be replaced. I.e., the mask contains a -1
    for a token that can be replaced, and a 0 for tokens that can't (based on the
    upos_filter).

    :param dep_sent: a tokenlist
    :param upos_filter: a list of upos to filter for. If None, no filtering is done
    except for punctuation.
    :return: a mask
    """
    if upos_filter == None:
        mask = [0 if tok['upos']=='PUNCT' else -1 for tok in dep_sent]
    else:
        mask = [-1 if tok['upos'] in upos_filter else 0 for tok in dep_sent]
    return mask

def create_replacement_masks(dep_sents, upos_filter=None):
    """Create a list of masks for each sentence.

    :param dep_sents: a list of tokenlists
    :param upos_filter: a list of upos to filter for. If None, no filtering is done
    :return: a list of masks. A mask contains a -1 for a token that can be 
    replaced, and a 0 for tokens that can't (based on the upos_filter)
    """
    masks = []
    for dep_sent in dep_sents:
        masks.append(create_replacement_mask(dep_sent, upos_filter=upos_filter))
    return masks

def make_replacer(lang, syntactic_patterns, morphlex, upos_filter=None):

    if lang=='fr':
        return FrenchReplacer(syntactic_patterns, morphlex, upos_filter=upos_filter)
    elif lang=='en':
        return EnglishReplacer(syntactic_patterns, morphlex, upos_filter=upos_filter)
    else:
        return Replacer(syntactic_patterns, morphlex, upos_filter=upos_filter)




class Replacer:
    def __init__(self, syntactic_patterns, morphlex, upos_filter=None):
        """Create a replacement object.
        
        :param syntactic_patterns: a SyntacticPatterns object
        :param morphlex: a MorphDict object
        :param upos_filter: a list of upos to filter for. If None, no filtering is done
        """
        self.syntactic_patterns = syntactic_patterns
        self.morphlex = morphlex
        self.upos_filter = upos_filter

    def replace_tokens_in_sentences(self, dep_sents, dep_trees, fraction=1., cutoff=10000000, verbose=True):
        """
        Replace tokens in a list of sentences.

        :param dep_sents: a list of tokenlists
        :param dep_trees: a list of tokentrees
        :param fraction: a float between 0 and 1. The fraction of tokens to replace.
        :param cutoff: the number of sentences after which to stop
        :param verbose: a boolean. If True, print progress
        :return: a list of tokenlists and a list of tokentrees with replaced tokens
        """
        # initial steps
        new_dep_sents = []
        new_dep_trees = []
        masks = create_replacement_masks(dep_sents, upos_filter=self.upos_filter)
        all_matches_per_upos = dict()
        all_no_forms_for_matches = dict()

        # loop over sentences
        for k,(dep_sent, dep_tree, mask) in enumerate(zip(dep_sents, dep_trees, masks)):
            if verbose and k % 100 == 0:
                print(k,end=", ", flush=True)
            if k > cutoff:
                break

            # replace tokens
            new_dep_sent, new_dep_tree, matches_per_upos, no_forms_for_matches = self.replace_tokens_in_sentence(
                dep_sent, 
                dep_tree, 
                mask,
                fraction=fraction, 
                verbose=True)

            # save results
            for upos, matches in matches_per_upos.items():
                if upos not in all_matches_per_upos:
                    all_matches_per_upos[upos] = []
                all_matches_per_upos[upos] += matches
            for upos, matches in no_forms_for_matches.items():
                if upos not in all_no_forms_for_matches:
                    all_no_forms_for_matches[upos] = []
                all_no_forms_for_matches[upos] += matches
            new_dep_sents.append(new_dep_sent)
            new_dep_trees.append(new_dep_tree)

        # return results
        if verbose:
            return new_dep_sents, new_dep_trees, all_matches_per_upos, all_no_forms_for_matches
        else:
            return new_dep_sents, new_dep_trees

    def replace_tokens_in_sentence(self, dep_sent, dep_tree, mask, fraction=1., verbose=True):

        # initial steps
        mask_with_ix = list(enumerate(mask))
        dep_tree = copy.deepcopy(dep_tree)
        dep_sent = copy.deepcopy(dep_sent)
        matches_per_upos = dict()
        no_forms_for_matches = dict()

        # list of tokens that can be replaced
        try_tokens = [t[0] for t in mask_with_ix if t[1]==-1] 
        random.shuffle(try_tokens)

        # progress indicators
        goal_to_replace = int(len(try_tokens) * fraction)
        replaced_tokens = 0

        # try all possible tokens
        for try_token in try_tokens:
            if replaced_tokens >= goal_to_replace: # hit the goal
                break

            token = dep_sent[try_token]
            matches = self.syntactic_patterns.find_matches_for_token(token, dep_tree) # tuples (form, lemma)
            matches = [m for m in matches if m[1] != token['lemma']] # remove matches with the same lemma
            # stats
            if token['upos'] not in matches_per_upos:
                matches_per_upos[token['upos']] = []
            matches_per_upos[token['upos']].append(len(matches))

            # no matches for this token -> can't replace
            if len(matches)==0:
                continue

            # find an appropriate form
            random.shuffle(matches)
            if self.morphlex is not None:
                # go through lemmas and find the first form that fits
                for _, new_lemma in matches:
                    forms_for_matches = self.morphlex.lookup(new_lemma, token)
                    if len(forms_for_matches)>0:
                        # TODO is this part language-specific? Can it be part of the morphlex, which could return just 1 form?
                        # select the most frequent element in the list. Works well for German nouns
                        new_word = max(set(forms_for_matches), key=forms_for_matches.count)
                        break
                    
                # if no form was found, log this case and try the next token
                if len(forms_for_matches) == 0:
                    if token['upos'] not in no_forms_for_matches:
                        no_forms_for_matches[token['upos']] = []
                    no_forms_for_matches[token['upos']].append((token, len(matches)))
                    continue    
            else:
                new_word, new_lemma = matches[0]

            # change the tree
            dep_sent[try_token]['form'] = new_word
            dep_sent[try_token]['lemma'] = new_lemma
            dep_tree = dep_sent.to_tree()
            replaced_tokens += 1
            mask[try_token] = 1
        
        # force first token to be uppercase
        if dep_sent[0]['form'][0].islower():
            dep_sent[0]['form'] = dep_sent[0]['form'][0].capitalize() + dep_sent[0]['form'][1:]
        # postprocess (language dependent)
        dep_sent, dep_tree, mask = self.postprocess(dep_sent, dep_tree, mask)

        # adapt metadata
        dep_sent = self.adapt_text_in_metadata(dep_sent)
        dep_tree = dep_sent.to_tree()

        # return
        if verbose:
            return dep_sent, dep_tree, matches_per_upos, no_forms_for_matches
        else:
            return dep_sent, dep_tree

    def adapt_text_in_metadata(self, dep_sent):
        tok_list_right_spacing = []
        for tok in dep_sent:
            tok_list_right_spacing.append(tok['form'])
            misc_none = tok['misc']==None
            spaceafterNo = not(misc_none) and tok['misc'].get('SpaceAfter')=='No'
            if not(spaceafterNo):
                tok_list_right_spacing.append(' ')
        dep_sent.metadata['text'] = ''.join(tok_list_right_spacing).strip()
        return dep_sent
    
    def postprocess(self, dep_sent, dep_tree, mask):
        return dep_sent, dep_tree, mask

class FrenchReplacer(Replacer):
    def __init__(self, syntactic_patterns, morphlex, upos_filter=None):
        super().__init__(syntactic_patterns, morphlex, upos_filter)
        self.french_vowels_text = ['a', 'e', 'i', 'o', 'u', 'y']
        self.french_gender_to_sing_article = {'Masc': 'le', 'Fem': 'la'}

    def is_mute_h(self, word):
        """TODO: The right vowel list, based on ipa. Better use 
        
        wiktionary.is_muted_h"""
        ipas = self.morphlex.wiktionary.lookup_ipa(word)
        for ipa in ipas:
            if ipa[0] in ["/","["]:
                ipa = ipa[1:]
            if ipa[0] in self.french_vowels_text:
                return True
        return False 
    
    def is_h_aspire(self, word):
        """Check. Better use wiktionary_is_aspirated_h"""
        ipas = self.morphlex.wiktionary.lookup_ipa(word)
        for ipa in ipas:
            if ipa[0] in ["/","["]:
                ipa = ipa[1:]
            if ipa[0] == "h":
                return True
        return False

    def postprocess(self, dep_sent, dep_tree, mask):
        """Postprocess the generated sentence
        
        Determiners: Replace le/la <=> l' depending on vowels / mute 
        Prepositions: Replace de <=> d' depending on vowels / mute 
        """
        for i,tok in enumerate(dep_sent):
            word_starts_uppercase = tok['form'][0].isupper()
            tokform = tok['form'].lower()
            # replace le/la with l' if necessary
            if tokform in ['le', 'la', 'de']:
                # replace or not? 
                if i + 1 < len(mask):
                    if mask[i+1] == 1:
                        nextform = dep_sent[i+1]['form'].lower()
                        # replace if next token starts with a vowel
                        if nextform[0] in self.french_vowels_text or (nextform[0] == 'h' and self.morphlex.wiktionary.is_probably_muted_h(nextform)):
                            if tokform.startswith('l'):
                                tokform = "l'"
                            elif tokform.startswith('d'):
                                tokform = "d'"
                            if tok['misc'] is None:
                                tok['misc'] = dict()
                            tok['misc']['SpaceAfter'] = 'No'
            elif tokform in ["l'", "d'"]:
                # replace with le/la/les if necessary
                if mask[i+1] == 1:
                    nextform = dep_sent[i+1]['form'].lower()
                    head = get_token_with_id(dep_sent, tok['head'])
                    # replace if next token does not start with a vowel
                    # aka form does not start with a vowel letter, and form does not start with a mute h
                    
                    if not(nextform[0] in self.french_vowels_text) and not(nextform[0] == 'h' and self.morphlex.wiktionary.is_probably_muted_h(nextform)):
                        if tokform.startswith('l'):
                            #print('TOKFORM', tokform)
                            if head:
                                feats = head['feats'] if head['feats'] is not None else dict()
                                if not(feats.get('Number')=='Plur') and 'Gender' in feats:
                                    tokform = self.french_gender_to_sing_article[feats["Gender"]]
                            else:
                                dict()
                        elif tokform.startswith('d'):
                            tokform = 'de'
                        if tok['misc'] is not None:
                            tok['misc'].pop('SpaceAfter', None)
                            if len(tok['misc'])==0:
                                tok['misc'] = None
            if word_starts_uppercase:
                tokform = tokform[0].upper() + tokform[1:]
            tok['form'] = tokform
        dep_tree = dep_sent.to_tree()
        return dep_sent, dep_tree, mask

class EnglishReplacer(Replacer):
    def __init__(self, syntactic_patterns, morphlex, upos_filter=None):
        super().__init__(syntactic_patterns, morphlex, upos_filter)

    def postprocess(self, dep_sent, dep_tree, mask):
        """Postprocess the generated sentence
        
        Determiners: Replace a/an depending on start of next word
        """
        for i,tok in list(enumerate(dep_sent))[:-1]:
            word_starts_uppercase = tok['form'][0].isupper()
            tokform = tok['form'].lower()
            # replace a/an with an if necessary
            if tokform in ['a', 'an']:
                # replace or not? 
                if mask[i+1] == 1:
                    nextform = dep_sent[i+1]['form'].lower()
                    # replace if next token starts with a vowel
                    if tokform=='a':
                        if self.morphlex.word_likely_starts_with_vowel(nextform):
                            tokform = 'an'
                    elif tokform=='an':
                        if self.morphlex.word_likely_starts_with_consonant(nextform):
                            tokform = 'a'
            if word_starts_uppercase:
                tokform = tokform[0].upper() + tokform[1:]
            tok['form'] = tokform
        dep_tree = dep_sent.to_tree()
        return dep_sent, dep_tree, mask
