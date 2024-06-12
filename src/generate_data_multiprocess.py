import os, sys
sys.path.append(os.getcwd() + '/src/')

from ud_tools import *
from syntactic_patterns import *


from morph_dict_tools.universal import *
from morph_dict_tools.udlex_german import *
from morph_dict_tools.udlex_english import *
from morph_dict_tools.udlex_french import *
from morph_dict_tools.udlex_arabic import *
from morph_dict_tools.udlex_russian import *
from replacement import *

import multiprocessing as mp
from multiprocessing import Process
import copy

tb_path_mod = "data/ud210/modified-ud-treebanks/"
tb_path_orig = "data/ud210/ud-treebanks-v2.10/"
tb_paths = {
    "ar": {
        "train": [tb_path_mod + "UD_Arabic-PADT/ar_padt-ud-train.conllu"],
        "dev": [tb_path_mod + "UD_Arabic-PADT/ar_padt-ud-dev.conllu"],
        "test": [tb_path_mod + "UD_Arabic-PADT/ar_padt-ud-test.conllu"]
    },
    "de": {
        "train": [tb_path_mod + "UD_German-HDT/de_hdt-ud-train.conllu"], 
        "dev": [tb_path_mod + "UD_German-HDT/de_hdt-ud-dev.conllu"], 
        "test": [tb_path_mod + "UD_German-HDT/de_hdt-ud-test.conllu"]},
    "en": {
        "train": [tb_path_mod + "UD_English-EWT/en_ewt-ud-train.conllu"],
        "dev": [tb_path_mod + "UD_English-EWT/en_ewt-ud-dev.conllu"],
        "test": [tb_path_mod + "UD_English-EWT/en_ewt-ud-test.conllu"]},
    "fr": {
        "train": [tb_path_mod + "UD_French-GSD/fr_gsd-ud-train.conllu"],
        "dev": [tb_path_mod + "UD_French-GSD/fr_gsd-ud-dev.conllu"],
        "test": [tb_path_mod + "UD_French-GSD/fr_gsd-ud-test.conllu"]},        
    "ru": {
        "train": [tb_path_orig + "UD_Russian-SynTagRus/ru_syntagrus-ud-train.conllu"],
        "dev": [tb_path_orig + "UD_Russian-SynTagRus/ru_syntagrus-ud-dev.conllu"],
        "test": [tb_path_orig + "UD_Russian-SynTagRus/ru_syntagrus-ud-test.conllu"]},
    }


class ReplacerProcessHelper():
    def __init__(self, lang, synt_patterns, morphdict, upos_filter=None): 
        self.replacer = make_replacer(lang, synt_patterns, morphdict, upos_filter=upos_filter)
        self.lang = lang

    def fwd(self, sents, trees, slice_number):
        new_sents, _, _, _ = self.replacer.replace_tokens_in_sentences(sents, trees)
        print('Created ', len(new_sents), ' new sentences')
        # return_dict[slice_number] = new_sents

        print('Saving sentences to conllu file')
        filename = f"_{self.lang}_sents_slice_{slice_number}.conllu"
        with open(filename, 'w') as f:
            for sent in map(lambda x:x.serialize(), new_sents):
                f.write(sent)
        del self.replacer
        print('Done with slice ', slice_number)

def parallel_replacement(lang=None, sents=None, trees=None, morphdict=None, synt_patterns=None, upos_filter=None, num_processes=4):
    processes = []
    tb_size = len(sents)
    print('num_processes', num_processes)
    print('treebank size', tb_size)
    # slice treebank into parts
    slice_size = int(len(sents) / num_processes)+1
    print('slice_size', slice_size)
    start=0

    manager = mp.Manager()
    return_dict = manager.dict()
    print('build and start processes')
    for i in range(num_processes):
        if start == tb_size:
            break
        end = min((i + 1) * slice_size, tb_size)
        print('i', i, 'start', start, 'end', end)

        pats = copy.deepcopy(synt_patterns)
        md = copy.deepcopy(morphdict)
        up_f = copy.deepcopy(upos_filter)
        rph = ReplacerProcessHelper(lang, pats, md, upos_filter=up_f)
 
        p = Process(target=rph.fwd, args=(sents[start:end], trees[start:end], i))
        processes.append(p)
        p.start()
        start = end
    #print('start processes')
    #for p in processes:
    #    p.start()
    print('join processes')
    for p_n,p in enumerate(processes):
        print('join process', p_n)
        p.join()
    
    print('done creating. Now reloading and merging')
    new_sents = []
    for i in range(num_processes):
        print(i)
        new_sents += load_ud_treebank(f"_{lang}_sents_slice_{i}.conllu", no_trees=True)
    print('remove tmp files')
    for i in range(num_processes):
        os.remove(f"_{lang}_sents_slice_{i}.conllu")
    return new_sents


def main():
    langs=["en", "fr"] # ["en", "de"] # ["en", "fr", "ru", "de"] # list(tb_paths.keys())
    print(langs)
    print('load morphdicts')
    morphdicts = {lang: load_morphdict_from_pickle(lang) for lang in langs}
    treebanks = dict() 
    for lang in langs:
        print('load treebanks for ', lang)
        treebanks[lang] = {
            "train": load_ud_treebank(tb_paths[lang]["train"][0]),
            "dev": load_ud_treebank(tb_paths[lang]["dev"][0]),
            "test": load_ud_treebank(tb_paths[lang]["test"][0])
        }
    upos_filter = ["NOUN", "PROPN", "VERB", "ADJ"]

    # load syntactic patterns for all languages
    synt_patterns = {lang:dict() for lang in langs}
    for lang in langs:
        print('load syntactic patterns for ', lang)
        pattern_config = pattern_configs[lang]
        # train
        synt_patterns[lang]["train"] = SyntacticPatterns(treebanks[lang]["train"][1], upos_filter=upos_filter, pattern_config=pattern_config)
        # dev/test
        dev_test_trees = treebanks[lang]["dev"][1] + treebanks[lang]["test"][1]
        synt_patterns[lang]["dev+test"] = SyntacticPatterns(dev_test_trees, upos_filter=upos_filter, pattern_config=pattern_config)

    # optimized for 64GB RAM, 32 swap
    # first for train set, second for dev+test
    lang_to_num_processes={
        "ar": [16,8],
        "de": [7,5],
        "en": [3,2],
        "fr": [4,2],
        "ru": [5,3],
    }
    cutoff=100000000
    out_dir = "out/upos-only/" #"out/ud/"
    for lang in langs:
        print('replace tokens in train', lang)
        new_sents = parallel_replacement(
            lang=lang,
            sents=treebanks[lang]["train"][0][:cutoff], 
            trees=treebanks[lang]["train"][1][:cutoff], 
            morphdict=morphdicts[lang], 
            synt_patterns=synt_patterns[lang]["train"], 
            upos_filter=upos_filter,
            num_processes=lang_to_num_processes[lang][0])
        print('\nsave new treebank')
        serialize_sents_to_conllu_file(new_sents, f"{out_dir}{lang}_train.conllu")

        print('replace tokens in dev', lang)
        new_sents = parallel_replacement(
            lang=lang,
            sents=treebanks[lang]["dev"][0][:cutoff],
            trees=treebanks[lang]["dev"][1][:cutoff],
            morphdict=morphdicts[lang],
            synt_patterns=synt_patterns[lang]["dev+test"],
            upos_filter=upos_filter,
            num_processes=lang_to_num_processes[lang][1])
        print('\nsave new treebank')
        serialize_sents_to_conllu_file(new_sents, f"{out_dir}{lang}_dev.conllu")


if __name__=='__main__':
    main()

