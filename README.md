
### Environment

All dependencies are listed an `environment.yml`, which you can use to create a conda environment: 

```
conda env create -f environment.yml
```

## Data

Get UDLexicon and unzip to data/UDLexicon

```
wget http://atoll.inria.fr/~sagot/UDLexicons.0.2.zip -O data/morph/UDLexicons.0.2.zip
unzip data/morph/UDLexicons.0.2.zip -d data/morph/
```

Get Wiktionary data 

```
mkdir data/morph/wiktextract/en -p
wget https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.json -P data/morph/wiktextract/en/
wget https://kaikki.org/dictionary/French/kaikki.org-dictionary-French.json -P data/morph/wiktextract/fr/

```

Download Preprocessed ArabicMorphDict

```
wget --no-check-certificate 'https://docs.google.com/uc?export=download&id=1o9uBFXNt6hiM7Eys44lLd5w4WKbeCPwT' -O data/morph/pickles/ArabicMorphDict.pickle
```

Download and unzip UD treebanks. Note that these commands are fitted to UD release 2.10! 

```
wget https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-4758/ud-treebanks-v2.10.tgz?isAllowed=y -O data/ud-treebanks-v2.10.tgz

mkdir -p data/ud-treebanks-v2.10/UD_Arabic-PADT/
tar -xzf data/ud-treebanks-v2.10.tgz -C data/ud-treebanks-v2.10/UD_Arabic-PADT --strip-components=2 ud-treebanks-v2.10/UD_Arabic-PADT

mkdir -p data/ud-treebanks-v2.10/UD_English-EWT/
tar -xzf data/ud-treebanks-v2.10.tgz -C data/ud-treebanks-v2.10/UD_English-EWT --strip-components=2 ud-treebanks-v2.10/UD_English-EWT

mkdir -p data/ud-treebanks-v2.10/UD_French-GSD/
tar -xzf data/ud-treebanks-v2.10.tgz -C data/ud-treebanks-v2.10/UD_French-GSD --strip-components=2 ud-treebanks-v2.10/UD_French-GSD

mkdir -p data/ud-treebanks-v2.10/UD_German-HDT/
tar -xzf data/ud-treebanks-v2.10.tgz -C data/ud-treebanks-v2.10/UD_German-HDT --strip-components=2 ud-treebanks-v2.10/UD_German-HDT

mkdir -p data/ud-treebanks-v2.10/UD_Russian-SynTagRus/
tar -xzf data/ud-treebanks-v2.10.tgz -C data/ud-treebanks-v2.10/UD_Russian-SynTagRus --strip-components=2 ud-treebanks-v2.10/UD_Russian-SynTagRus
```

### Preprocess UD treebanks

```
mkdir -p data/ud-mod/UD_Arabic-PADT/
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_Arabic-PADT/ar_padt-ud-train.conllu > data/ud-mod/UD_Arabic-PADT/ar_padt-ud-train_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_Arabic-PADT/ar_padt-ud-dev.conllu > data/ud-mod/UD_Arabic-PADT/ar_padt-ud-dev_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_Arabic-PADT/ar_padt-ud-test.conllu > data/ud-mod/UD_Arabic-PADT/ar_padt-ud-test_nocontractions.conllu
python prep/arabic_remove_diacritics.py

mkdir -p data/ud-mod/UD_English-EWT/
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_English-EWT/en_ewt-ud-train.conllu > data/ud-mod/UD_English-EWT/en_ewt-ud-train_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_English-EWT/en_ewt-ud-dev.conllu > data/ud-mod/UD_English-EWT/en_ewt-ud-dev_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_English-EWT/en_ewt-ud-test.conllu > data/ud-mod/UD_English-EWT/en_ewt-ud-test_nocontractions.conllu
# remove lines starting with indexes [0-99].1 (e.g. 11.1)
grep -v "^[0-9][0-9]*\.[0-9]" data/ud-mod/UD_English-EWT/en_ewt-ud-train_nocontractions.conllu > data/ud-mod/UD_English-EWT/en_ewt-ud-train.conllu
grep -v "^[0-9][0-9]*\.[0-9]" data/ud-mod/UD_English-EWT/en_ewt-ud-dev_nocontractions.conllu > data/ud-mod/UD_English-EWT/en_ewt-ud-dev.conllu
grep -v "^[0-9][0-9]*\.[0-9]" data/ud-mod/UD_English-EWT/en_ewt-ud-test_nocontractions.conllu > data/ud-mod/UD_English-EWT/en_ewt-ud-test.conllu

mkdir -p data/ud-mod/UD_French-GSD/
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_French-GSD/fr_gsd-ud-train.conllu > data/ud-mod/UD_French-GSD/fr_gsd-ud-train_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_French-GSD/fr_gsd-ud-dev.conllu > data/ud-mod/UD_French-GSD/fr_gsd-ud-dev_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_French-GSD/fr_gsd-ud-test.conllu > data/ud-mod/UD_French-GSD/fr_gsd-ud-test_nocontractions.conllu
python prep/infer_feats_french.py

mkdir -p data/ud-mod/UD_German-HDT/
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_German-HDT/de_hdt-ud-train.conllu > data/ud-mod/UD_German-HDT/de_hdt-ud-train_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_German-HDT/de_hdt-ud-dev.conllu > data/ud-mod/UD_German-HDT/de_hdt-ud-dev_nocontractions.conllu
grep -v "^[0-9][0-9]*-[0-9]" data/ud-treebanks-v2.10/UD_German-HDT/de_hdt-ud-test.conllu > data/ud-mod/UD_German-HDT/de_hdt-ud-test_nocontractions.conllu
python prep/infer_case_german.py
```


## Picle MorphDicts

This step is necessary to precompile all morphological dictionaries, which significantly speeds up loading them afterwards. 

`python prep/pickle_morphdicts.py`

## Build SPUD treebanks

Check `build_spud.ipynb` for instructions on how to run it for an existing treebank, and how to extend it to a new one! 

