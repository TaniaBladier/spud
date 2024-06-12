import os, sys
sys.path.append(os.getcwd() + '/src/')

from ud_tools import *
from syntactic_patterns import *

def serialize_sents_to_conllu_file(sents, filename):
    with open(filename, 'w') as f:
        for sent in sents:
            f.write(sent.serialize())


if __name__=='__main__':
    splits = ['train', 'dev', 'test']
    for split in splits:
        print("split: ", split)
        tb_in = f"data/ud-mod/UD_German-HDT/de_hdt-ud-{split}_nocontractions.conllu"
        tb_out = f"data/ud-mod/UD_German-HDT/de_hdt-ud-{split}.conllu"
        dep_sents, dep_trees = load_ud_treebank(tb_in)

        matched = 0
        tried = 0
        no_det_daughters = 0
        no_prep_daughters = 0
        for i, (dep_sent, dep_tree) in enumerate(zip(dep_sents, dep_trees)):
            for tok in dep_sent:
                if tok['upos'] in ['NOUN', 'PROPN']:
                    if tok['feats'] is not None and 'Case' not in tok['feats']:
                        tried += 1
                        tok_subtree = find_subtree_with_token_ix(dep_tree, tok['id'])
                        if tok_subtree is None:
                            print('found no subtree for', tok['id'])
                            break
                        det_daughters = [c.token for c in tok_subtree.children if c.token['deprel'] == 'det']
                        if len(det_daughters) > 1:
                            #print(sent2str(dep_sent))
                            #print(tok['form'], 'has multiple det daughters. Sent no.', i)
                            #print(det_daughters)
                            #print()
                            det_daughters = det_daughters[:1]
                        if len(det_daughters) > 0:
                            det_daughter = det_daughters[0]
                            if det_daughter['feats'] is None:
                                continue
                            tok_gender = tok['feats'].get('Gender',None)
                            daughter_gender = det_daughter['feats'].get('Gender', None)
                            gender_matches = (tok_gender == None) or (daughter_gender==None) or tok_gender==daughter_gender
                            tok_number = tok['feats'].get('Number',None)
                            daughter_number = det_daughter['feats'].get('Number', None)
                            number_matches = (tok_number == None) or (daughter_number==None) or tok_number==daughter_number

                            if gender_matches and number_matches and 'Case' in det_daughter['feats']:
                                tok['feats']['Case'] = det_daughter['feats']['Case']
                                matched +=1
                            else:
                                #print('no match for noun ', tok['form'])
                                #print(tok_subtree.print_tree())
                                pass
                        else:                   
                            prep_daughters = [c.token for c in tok_subtree.children if c.token['deprel'] == 'case' and c.token['upos'] == 'ADP']
                            if len(prep_daughters) > 1:
                                #print(sent2str(dep_sent))
                                #print(tok['form'], 'has multiple prep daughters. Send no.', i)
                                #print(prep_daughters)
                                #print()
                                prep_daughters = prep_daughters[:1]
                            if len(prep_daughters) == 1:
                                prep_daughter = prep_daughters[0]
                                if prep_daughter['feats'] is None:
                                    continue
                                tok_gender = tok['feats'].get('Gender',None)
                                daughter_gender = prep_daughter['feats'].get('Gender', None)
                                gender_matches = (tok_gender == None) or (daughter_gender==None) or tok_gender==daughter_gender
                                tok_number = tok['feats'].get('Number',None)
                                daughter_number = prep_daughter['feats'].get('Number', None)
                                number_matches = (tok_number == None) or (daughter_number==None) or tok_number==daughter_number
                                if gender_matches and number_matches and 'Case' in prep_daughter['feats']:
                                    tok['feats']['Case'] = prep_daughter['feats']['Case']
                                    matched += 1
                            else:
                                no_prep_daughters += 1

        serialize_sents_to_conllu_file(dep_sents, tb_out)
