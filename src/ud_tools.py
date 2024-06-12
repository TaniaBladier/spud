from conllu import parse

def get_token_with_id(dep_sent, id):
    """
    Get the token with the given id.
    :param dep_sent: a tokenlist
    :param id: the id of the token
    :return: the token with the given id
    """
    for tok in dep_sent:
        if tok['id'] == id:
            return tok
    return None

def toklist2tree(toklist):
    """
    Convert a TokenList to a TokenTree.
    """
    return toklist.to_tree()


def tokTree2tokSent(tokTree):
    """
    Convert a TokenTree to a TokenList.
    """
    return parse(tokTree.serialize())[0]


def sent2str(tokenList):
    """
    Convert a TokenList to a string.
    """
    return ' '.join([t['form'] for t in tokenList])

def serialize_sents_to_conllu_file(sents, filename):
    with open(filename, 'w') as f:
        for sent in map(lambda x:x.serialize(), sents):
            f.write(sent)

def load_ud_treebank(filename, verbose=True, cutoff=None, no_trees=False):
    """
    Loads a treebank from a file.
    :param filename: the filename of the treebank
    :param verbose: whether to print progress information
    :param cutoff: the number of sentences to load
    :param no_trees: whether to load the trees or only the tokenlists
    :return: a tuple of the list of tokenlists, and a map object for the trees"""
    print("read file ", filename) if verbose else None 
    with open(filename, 'r') as f:
        raw_data = f.readlines()
    raw_data = ''.join(raw_data)
    print('parse data into token lists') if verbose else None
    dep_sents = parse(raw_data)
    print('apply cutoff of ', cutoff) if verbose else None
    if cutoff is not None:
        dep_sents = dep_sents[:cutoff]

    if no_trees:
        return dep_sents
    print('convert token lists to trees') if verbose else None
    dep_trees = list(map(toklist2tree, dep_sents))
    print('Done parsing')
    del raw_data
    return dep_sents, dep_trees

def create_markup_for_tok_list_pair(toklist1, toklist2, markup="**"):
    """
    Given two sentences, highlight all tokens from the second 
    sentence that are different from the first sentence. 
    :param toklist1: a tokenlist
    :param toklist2: a tokenlist
    :param markup: the markup to use for highlighting
    :return: a string containing the second sentence
    """
    result = ""
    for tok1, tok2 in zip(toklist1, toklist2):
        if tok1['form'] != tok2['form']:
            result += markup + tok2['form'] + markup
        else:
            result += tok1['form']
        result += " "
    return result

def write_sentence_pairs_to_file(sents_1, sents_2, filename):
    """Write a list of sentence pairs to a file.

    The first sentence is printed as is. 
    The second sentence is highlighted with ** (markdown boldface) around the
    differences to the first sentence.

    :param sents_1: a list of tokenlists. The first sentence in each pair.
    :param sents_2: a list of tokenlists. The second sentence in each pair.
    :param filename: the file to write to
    """
    with open(filename, "w") as f:
        for i, (sent1, sent2) in enumerate(zip(sents_1, sents_2)):
            f.write(str(i) + '  \n')
            f.write(sent2str(sent1)+'  \n')
            f.write(create_markup_for_tok_list_pair(sent1, sent2) + "\n")
            f.write('\n')

