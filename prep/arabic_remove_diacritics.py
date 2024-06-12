import os, sys
sys.path.append(os.getcwd() + '/src/')

from ud_tools import *
import pyarabic.araby as araby
import copy

if __name__=="__main__":
    tb_path_mod = "data/ud-mod/"
    tbs_in = {
        "train": tb_path_mod + "UD_Arabic-PADT/ar_padt-ud-train_nocontractions.conllu",
        "dev": tb_path_mod + "UD_Arabic-PADT/ar_padt-ud-dev_nocontractions.conllu",
        "test": tb_path_mod + "UD_Arabic-PADT/ar_padt-ud-test_nocontractions.conllu"
    }
    splits = ['train', 'dev', 'test']
    for split in splits:
        sents = load_ud_treebank(tbs_in[split], no_trees=True)
        # remove diacritics
        print('remove diacritics for ', split)
        print('num of sents: ', len(sents))
        sents_without_dia = list()
        for sent in sents:
            sent_new = copy.deepcopy(sent)
            for token in sent_new:
                token['form'] = araby.strip_diacritics(token['form'])
                token['lemma'] = araby.strip_diacritics(token['lemma'])
            sents_without_dia.append(sent_new)
        serialize_sents_to_conllu_file(sents_without_dia, f"{tb_path_mod}UD_Arabic-PADT/ar_padt-ud-{split}.conllu")
