
from ud_tools import tokTree2tokSent
import random


def find_subtree_with_token_ix(dep_tree, i):
    """given a dep tree and an index, find the subtree with that index. 
    
    :param dep_tree: a TokenTree dependency tree
    :param i: the index of the token (aka token['id']) 
    :return: the subtree where the token at the root has the index i
    """
    if dep_tree.token['id'] == i:
        return dep_tree
    for c in dep_tree.children:
        in_children = find_subtree_with_token_ix(c,i) 
        if in_children is not None:
            return in_children
    return None



# others_(ignore/consider) are decided on a case-by-case basis per relation.
ud_rels = {
    "core-args":["nsubj", "obj", "iobj", "csubj", "ccomp", "xcomp"],
    "non-core deps":["obl", "vocative", "expl", "dislocated", "advcl", "advmod", "discourse", "aux", "cop", "mark"],
    "nominal-deps":["nmod", "appos", "nummod", "acl", "amod", "det", "clf", "case"],
    "others_ignore":["cc", "punct", "root", "dep", "reparandum", "conj", "list", "parataxis"],
    "others_consider":["compound", "fixed", "flat", "orphan", "goeswith"],
}


"""
    :param include_self_in_deprels: Default is false. whether to include the mother token 
            in the deprels to children. Needed e.g.for French with pre- and succeeding adjectives.
    :param ignore_dependent_order: Default is true. Whether to ignore the order of the dependents
            (e.g. treating them as a list or set)
    :param ignore_deprels_for_children: 
            a dict for upos -> list of deprels to ignore for children. If None, no deprels are ignored
            and every deprel is considered.
"""
pattern_configs = {
    "ar": {
        "include_self_in_deprels":False,
        "ignore_dependent_order":True
    },
    "de": {
        "include_self_in_deprels":False, #?
        "ignore_dependent_order":True,    #?
        "ignore_deprels_for_children":{
            "ADJ": ud_rels["non-core deps"] + ud_rels["nominal-deps"] + ud_rels["others_ignore"],
            "VERB": ud_rels["non-core deps"] + ud_rels["nominal-deps"] + ud_rels["others_ignore"],
        }, #?
    },
    "en": {
        "include_self_in_deprels":False, #?
        "ignore_dependent_order":True,    #?
        "ignore_deprels_for_children":{
            "ADJ": ud_rels["non-core deps"] + ud_rels["nominal-deps"] + ud_rels["others_ignore"],
            "VERB": ud_rels["non-core deps"] + ud_rels["nominal-deps"] + ud_rels["others_ignore"],
        }, #?
    },
    "id": {
        "include_self_in_deprels":False, #?
        "ignore_dependent_order":True,    #?
    },
    "fr": {
        "include_self_in_deprels":True, #!
        "ignore_dependent_order":False  #!
    },
    "ru": {
        "include_self_in_deprels":False,
        "ignore_dependent_order":True,
        "ignore_deprels_for_children":{
            "VERB": ud_rels["others_ignore"] + ud_rels["nominal-deps"] + ud_rels["non-core deps"]
        }
    }
}


class SyntacticPatterns():
    def __init__(self, treebank, upos_filter=None, verbose=False, pattern_config=dict()):
        """Aggregates all patterns from a treebank, and sorts them.

        :param treebank: the treebank
        :param upos_filter: a list of upos to filter on. If None, no filtering is done
        :param verbose: whether to print progress information
        :param pattern_config: a dict of configs for the pattern matching. See pattern_configs for an example. 
                                If a parameter is not specified, the less restrictive one is used. 
        """

        self.upos_filter = upos_filter
        # include_self_in_deprels=False, ignore_deprels_for_dependents=None, ignore_dependent_order=False
        if 'include_self_in_deprels' not in pattern_config:
            pattern_config['include_self_in_deprels'] = False
        if 'ignore_deprels_for_dependents' not in pattern_config:
            pattern_config['ignore_deprels_for_dependents'] = dict()
        if 'ignore_dependent_order' not in pattern_config:
            pattern_config['ignore_dependent_order'] = True
        self.pattern_config=pattern_config

        patterns = self.aggregate_patterns_from_treebank(
            treebank, 
            upos_filter=upos_filter, 
            verbose=verbose)
        # drop duplicates
        print('Patterns before dropping duplicates: ', len(patterns)) if verbose else None
        patterns = list(set(patterns))
        print('Patterns after dropping duplicates: ', len(patterns)) if verbose else None
        self.num_patterns = len(patterns)
        # create dictionary of patterns
        self.patterns_dict = dict() # upos -> deprel -> deprels_to_children -> list(forms)
        for (form,lemma,deprel,upos,deprels_to_children) in patterns:
            if upos not in self.patterns_dict:
                self.patterns_dict[upos] = dict()
            if deprel not in self.patterns_dict[upos]:
                self.patterns_dict[upos][deprel] = dict()
            if deprels_to_children not in self.patterns_dict[upos][deprel]:
                self.patterns_dict[upos][deprel][deprels_to_children] = []
            self.patterns_dict[upos][deprel][deprels_to_children].append((form,lemma))
    

    def find_matches(self, upos, deprel, deprels_to_children):
        """Finds all tuples of form and lemma for a pattern.

        :param upos: the upos of the pattern
        :param deprel: the deprel of the pattern
        :param deprels_to_children: the deprels to the children of the pattern
        :return: a list of forms
        """
        if upos not in self.patterns_dict:
            return []
        if deprel not in self.patterns_dict[upos]:
            return []
        if deprels_to_children not in self.patterns_dict[upos][deprel]:
            return []
        return self.patterns_dict[upos][deprel][deprels_to_children]


    def find_matches_for_token(self, token, dep_tree):
        """Finds all tuples of form and lemma that match the given token.

        :param token: the token
        :param dep_tree: the dependency tree of the sentence
        :return: a list of forms and lemmas
        """
        upos = token['upos']
        deprel = token['deprel']
        i = token['id']
        deprels_to_children = str(self.find_deprels_to_children(dep_tree, i))
        return self.find_matches(upos, deprel, deprels_to_children)
    

    def __len__(self):
        """Returns the number of patterns."""
        return self.num_patterns

    def stats(self):
        """Returns a summary dict of the syntactic patterns.
        
        The dict can be put in a user-friendly format with
        pd.DataFrame(synt_patterns.stats()) or similar.
        """
        res_dict = dict()
        for pos in self.upos_filter:
            replacement_list_length_counter = dict()
            num_patterns_for_pos = 0
            for deprel in self.patterns_dict[pos]:
                num_patterns_for_pos += len(self.patterns_dict[pos][deprel])
                for deprels_to_children in self.patterns_dict[pos][deprel]:
                    length = len(self.patterns_dict[pos][deprel][deprels_to_children])
                    replacement_list_length_counter[length] = replacement_list_length_counter.get(length, 0) + 1
            total_number_of_replacements = sum([k*v for k,v in replacement_list_length_counter.items()])
            mean_number_of_replacements = total_number_of_replacements / num_patterns_for_pos
            res_dict_for_pos = {
                'No. of patterns': num_patterns_for_pos,
                'Patterns with one replacement': replacement_list_length_counter[1],
                'total No. of replacements': total_number_of_replacements,
                'mean No. of replacements': mean_number_of_replacements
            }
            res_dict[pos] = res_dict_for_pos
        return res_dict

    # a pattern is a tuple (form, lemma, upos, deprel_to_head, list(deprels_to_children))
    def aggregate_patterns_from_treebank(self, dep_trees, upos_filter=None, verbose=False):
        """Aggregates all patterns from a treebank.

        :param dep_trees: the list of dependency trees (aka the treebank)
        :param upos_filter: a list of upos to filter on. If None, no filtering is done
        :param verbose: whether to print progress information
        :return: a list of patterns"""
        patterns_nested_list = []
        k = 0
        for tree in dep_trees: 
            new_patterns = self.find_patterns(
                tree, 
                patterns=[], 
                morphfeats=False, 
                upos_filter=upos_filter)
            patterns_nested_list.append(new_patterns)
            k = k + 1
            if verbose and k % 10000 == 0:
                print('processed ', k, ' trees')
            if k > 100000000:
                break
        patterns = [item for sublist in patterns_nested_list for item in sublist]
        return patterns

    def find_patterns(self, dep_tree, patterns=[], morphfeats=False, upos_filter=None):
        """Finds all patterns in a dependency tree. 

        A pattern is defined as a tuple of
        form, lemma, dependency relation to head, upos, dependency relation list to children,
        and optionally morphological features 

        :param dep_tree: the dependency tree
        :param patterns: a list of patterns to find. Always initialize as []
        :param morphfeats: whether to include morphological features in the patterns
        :param upos_filter: a list of upos to filter on. If None, no filtering is done
        :return: a list of patterns
        """

        # basic parts
        upos = dep_tree.token['upos']
        # only include the current token if it has the right upos
        if upos_filter is None or upos in upos_filter:
            form = dep_tree.token['form']
            lemma = dep_tree.token['lemma']
            deprel = dep_tree.token['deprel']

            # feats
            feats = dep_tree.token['feats']
            feats = 'EMPTY' if feats is None else str(sorted(feats.items()))

            # morph feats
            deprels_to_children = self.find_deprels_to_children(
                dep_tree, 
                dep_tree.token['id'])
            if morphfeats:
                tup = (form, lemma, deprel, upos, str(deprels_to_children), feats)
            else:
                tup = (form, lemma, deprel, upos, str(deprels_to_children))
            patterns.append(tup)

        # recursive step
        for c in dep_tree.children:
            patterns = self.find_patterns(
                c, 
                patterns=patterns, 
                morphfeats=morphfeats, 
                upos_filter=upos_filter)
        return patterns


    def find_deprels_to_children(self, dep_tree, i):
        """Returns a list of deprels to children of the token with id i.

        :param dep_tree: a TokenTree dependency tree
        :param i: the index of the token (aka token['id'])
        :return: a list of deprels to children of the token with id i
        """
        # find relevant subtree
        relevant_subtree = find_subtree_with_token_ix(dep_tree, i)
        # aggregate deprels to children
        children_id_to_deprel = [(c.token['id'], c.token['deprel']) for c in relevant_subtree.children]
        # filter irrelevant dependents:
        upos = relevant_subtree.token['upos']
        if upos in self.pattern_config['ignore_deprels_for_dependents']:
            old_len = len(children_id_to_deprel)
            children_id_to_deprel = [(c_id, deprel) for c_id, deprel in children_id_to_deprel if deprel not in self.pattern_config['ignore_deprels_for_dependents'][upos]]
            #if old_len > len(children_id_to_deprel):
            #    print('filtered ', old_len - len(children_id_to_deprel), ' children for ', upos)
        # include self at the right spot if requested
        if self.pattern_config['include_self_in_deprels']:
            children_id_to_deprel.append((relevant_subtree.token['id'],'MOTHER'))
        # sort by id. Necessary if include_self, if not, it maybe doesn't matter
        children_id_to_deprel.sort(key=lambda x: x[0])
        children_deprels = [c[1] for c in children_id_to_deprel]
        if self.pattern_config['ignore_dependent_order']:
            children_deprels.sort()
        return children_deprels


class SyntacticPatternsPOSOnly(SyntacticPatterns):

    def __init__(self, treebank, upos_filter=None, verbose=True, pattern_config=dict()):
        self.upos_filter = upos_filter
        self.upos2formlemma = dict()

        print('Aggregating patterns...') if verbose else None
        for i,dep_tree in enumerate(treebank):
            for token in tokTree2tokSent(dep_tree):
                upos = token['upos']
                form = token['form']
                lemma = token['lemma']
                if upos_filter is None or upos in upos_filter:
                    if upos not in self.upos2formlemma:
                        self.upos2formlemma[upos] = set()
                    self.upos2formlemma[upos].add((form, lemma))
            if verbose and i % 1000 == 0:
                print(i, end=", ", flush=True)
        self.num_patterns = sum([len(ps) for ps in self.upos2formlemma.values()])

    def find_matches_for_token(self, token, dep_tree, k=10):
        """Like the superclass method, but returns k random matches."""

        return random.sample(self.upos2formlemma[token['upos']], k)


