import nltk
import numpy as np
import pandas as pd
from googletrans import Translator
from googletrans import LANGCODES
from nltk.tokenize import word_tokenize, sent_tokenize


KNETER_LANGS = list(LANGCODES.values())
HL_POS = [i for i in range(0, len(KNETER_LANGS)) if KNETER_LANGS[i] == "de"][0]
Trans = Translator()


def mapped_translation(sents, src='de', dest='en'):
    translated = make_translation(sents, src=src, dest=dest)
    words, sent_idx =  mapped_sents_2_words(sents)
    translated_words, translated_sent_idx = mapped_sents_2_words(translated)
    return sent_idx, translated_sent_idx


def mapped_sents_2_words(sents):
    words = []
    sent_idx = []
    sn = 0
    for s in sents:
        w = word_tokenize(s)
        words += w
        sent_idx += [sn]*len(w)
        sn+=1
    return words, sent_idx


def parse_txt_file(path, mode='words'):
    with open(path, 'r') as f:
        lines = f.readlines()

    lines = ''.join(lines)
    if mode == 'words':
        out = word_tokenize(lines)
    if mode == 'sents':
        out = sent_tokenize(lines)
    return out


def get_lang_pos(LC, lang):
    try:
        return [i for i in range(0, len(LC)) if LC[i] == lang][0]
    except IndexError:
        raise ValueError(f'"{lang}" not a know language code.')


def make_translation(sents, src='de', dest='en'):
    Trans = Translator()
    translation = []
    for s in sents:
        translation.append(Trans.translate(s, src=src, dest=dest).text)
    return translation


def translation_chain(txt, lang_chain, print_steps=False):
    lang_chain = [
        entry if isinstance(entry, int) else get_lang_pos(KNETER_LANGS, entry)
        for entry in lang_chain
    ]
    for l in range(0, len(lang_chain) - 1):
        txt = Trans.translate(
            txt, src=KNETER_LANGS[lang_chain[l]], dest=KNETER_LANGS[lang_chain[l + 1]]
        ).text
        if print_steps:
            # print(txt)
            print(Trans.translate(txt, dest=KNETER_LANGS[HL_POS], src=KNETER_LANGS[lang_chain[l + 1]]).text)

    return txt


def txt_mapper(txt):
    token_col = nltk.word_tokenize(txt)
    token_num_col = list(range(len(token_col)))

    sent_tokens = nltk.sent_tokenize(txt)
    txt_tokens = [nltk.word_tokenize(s) for s in sent_tokens]
    txt_tagged = nltk.pos_tag_sents(txt_tokens)

    sent_num_col = np.zeros(len(token_col))
    entity_labels = np.empty(len(token_col), dtype="object")

    i = 0
    sent_num = 0
    for s in txt_tagged:
        sent_num_col[i : i + len(s)] = sent_num
        shallow_tree = nltk.ne_chunk(s)
        for k, kk in enumerate(shallow_tree):
            label = getattr(kk, "label", None)
            if label is not None:
                label = label()
            entity_labels[i + k] = label
        sent_num += 1
        i = i + len(s)

    tag_col = [item[1] for sublist in txt_tagged for item in sublist]

    frame_dict = {
        "token": token_col,
        "token_num": token_num_col,
        "sent_num": sent_num_col.astype(int),
        "tag": tag_col,
        "entity": entity_labels,
    }
    txt_map = pd.DataFrame(frame_dict)
    return txt_map


def shuffle_text(text_map, shuffle_tag="NNP"):
    sub_view = text_map[text_map["tag"] == shuffle_tag]
    np.random.shuffle(sub_view.token_num.values)
    sent_col = text_map.sent_num.copy()
    text_map.iloc[sub_view.token_num.values, :] = sub_view
    text_map.loc[:, "sent_num"] = sent_col
    return text_map


def mix_texts(text_maps):
    pass


if __name__ == "__main__":
    txt = "Die Mikrobiologie wird nach verschiedenen Gesichtspunkten in Spezialgebiete unterteilt."
    txt = translation_chain(txt, ["de", "en"])
    text_map_original = txt_mapper(txt)
    text_map = text_map_original.copy()
    for kind in text_map.tag.unique():
        text_map = shuffle_text(text_map, shuffle_tag=kind)
    txt_o = " ".join(text_map.token.to_list())
    txt_o = translation_chain(txt_o, ["en", "de"])
    print(txt_o)
