import numpy as np
import nltk
from subprocess import call, Popen
import time

from nltk.corpus import udhr
from nltk.tokenize import word_tokenize, sent_tokenize
from threading import Thread
from queue import Queue
from pynput.keyboard import Listener
from kneter import translation_chain
from googletrans import Translator


class TextKneter():
    def __init__(self, txt_list):
        self.txt_list = txt_list
        self.glitch_prob = 0
        self.read_heads = [0 for k in range(len(txt_list))]
        self.word_maps = [make_w_index(txt_list[k]) for k in range(len(txt_list))]
        self.bigrams = [nltk.bigrams(txt_list[k]) for k in range(len(txt_list))]
        self.cond_dists = [nltk.ConditionalFreqDist(self.bigrams[k]) for k in range(len(txt_list))]
        self.corpus_head = 0
        self.nxt_word = None


    def read_step(self):
        glitch = np.random.choice([True, False], p=[self.glitch_prob, 1 - self.glitch_prob])
        if glitch:
            glitch_word = draw_from_custom(self.cond_dists[self.corpus_head][self.txt_list[self.corpus_head][self.read_heads[self.corpus_head]]])
            self.read_heads[self.corpus_head] = np.random.choice(self.word_maps[self.corpus_head][glitch_word]) + 1
            self.nxt_word = f"{glitch_word}"
        else:
            self.nxt_word = f"{self.txt_list[self.corpus_head][self.read_heads[self.corpus_head]]}"
            self.read_heads[self.corpus_head] += 1
        if self.read_heads[self.corpus_head] >= len(self.txt_list[self.corpus_head]):
            self.read_heads[self.corpus_head] = 0
        return self.nxt_word

    def alter_corpus(self, k=1):
        c_old = self.corpus_head
        self.corpus_head = (self.corpus_head + k) % len(self.txt_list)
        self.read_heads[self.corpus_head] = self.read_heads[c_old] % len(self.txt_list[self.corpus_head])

    def alter_gprob(self, p=0):
        self.glitch_prob = p


def draw_from_custom(f_dist:dict):
    v_list = list(f_dist.values())
    k_list = list(f_dist.keys())
    p = np.array(v_list) / np.sum(v_list)
    return np.random.choice(k_list, p=p)


def make_w_index(w_list):
    words = list(nltk.FreqDist(w_list).keys())
    w_index = dict(zip(words,[[]]*len(words)))
    for w in enumerate(w_list):
        w_index[w[1]] = w_index[w[1]] + [w[0]]
    return w_index





if __name__ == "__main__":

    w_list = udhr.words('German_Deutsch-Latin1')
    w_list2 = udhr.words('English-Latin1')
    reader = TextKneter([w_list, w_list2])


