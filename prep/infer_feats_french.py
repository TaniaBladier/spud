import sys, os
sys.path.append(os.getcwd() + '/src/')

from ud_tools import *
import copy

def infer_number_from_head_noun(dep_sent, verbose=False):
    dep_sent = copy.deepcopy(dep_sent)
    for tok in dep_sent:
        if tok['upos'] == 'ADJ':
            if tok['feats'] is not None and 'Number' not in tok['feats']:
                # print(tok['form'], 'has no number')
                # print(tok['feats'])
                # print()
                head = get_token_with_id(dep_sent, tok['head'])
                if head is None:
                    print('head is none! token: ', tok) if verbose else None
                    continue
                
                if head['feats'] is not None and 'Number' in head['feats']:
                    tok['feats']['Number'] = head['feats']['Number']
                    print(tok['form'], 'now has number', head['feats']['Number']) if verbose else None
                    # print(tok['feats'])
                    # print()
    return dep_sent

if __name__=="__main__":
    dep_sents_train = load_ud_treebank('data/ud-mod/UD_French-GSD/fr_gsd-ud-train_nocontractions.conllu', no_trees=True)
    dep_sents_dev = load_ud_treebank('data/ud-mod/UD_French-GSD/fr_gsd-ud-dev_nocontractions.conllu', no_trees=True)
    dep_sents_test = load_ud_treebank('data/ud-mod/UD_French-GSD/fr_gsd-ud-test_nocontractions.conllu', no_trees=True)

    new_dep_sents_train = [infer_number_from_head_noun(dep_sent) for dep_sent in dep_sents_train]
    new_dep_sents_dev = [infer_number_from_head_noun(dep_sent) for dep_sent in dep_sents_dev]
    new_dep_sents_test = [infer_number_from_head_noun(dep_sent) for dep_sent in dep_sents_test]

    serialize_sents_to_conllu_file(new_dep_sents_train, 'data/ud-mod/UD_French-GSD/fr_gsd-ud-train.conllu')
    serialize_sents_to_conllu_file(new_dep_sents_dev, 'data/ud-mod/UD_French-GSD/fr_gsd-ud-dev.conllu')
    serialize_sents_to_conllu_file(new_dep_sents_test, 'data/ud-mod/UD_French-GSD/fr_gsd-ud-test.conllu')

