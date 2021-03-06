# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2018 Xavier FOLCH
#
# Bayesian Personal Ranking with KNN model
# Bibliogrpahy: https://arxiv.org/ftp/arxiv/papers/1205/1205.2618.pdf

from scipy.special import expit
from collections import deque, defaultdict
import numpy as np
import pandas as pd
import json
from io import BytesIO
import base64

class BPRKNN:
    def __init__(self, cards, training_decks, testing_decks):
        self.nb_cards = len(cards)
        self.cards = cards
        self.encoder = {}
        self.decoder = {}
        self.decks = deque()
        self.test_cards = deque()
        self.C = np.ndarray((self.nb_cards, self.nb_cards), dtype=np.float64)
        self.momentum = np.zeros((self.nb_cards, self.nb_cards), dtype=np.float64)
        self.scores = deque()
        self.last_evaluations = deque()

        self.generate_translators(cards)

        if training_decks != None:
            self.decks.extend(self.encode_list_decks(training_decks))

        if testing_decks != None:
            self.test_cards.extend(self.encode_deck(testing_decks))

    def generate_translators(self, cards):
        for i, card in enumerate(cards):
            self.encoder[card] = i
            self.decoder[i] = card

    def encode_list_decks(self, decks_to_process):
        decks = deque()
        for deck in decks_to_process:
            decks.append(self.encode_deck(deck))
        return decks

    def encode_deck(self, deck_to_encode):
        encoded_deck = deque()
        for card in deck_to_encode:
            encoded_deck.append(self.encoder[card])
        return encoded_deck

    def build(self, parameters):
        self.build_model(N=parameters['N'], lbd_I=parameters['lbd_I'], lbd_J=parameters['lbd_J'],
                         learning_rate=parameters['learning_rate'], epoch=parameters['epoch'], batch_size=parameters['batch_size'],
                         decay=parameters['decay'], nb_early_learning = parameters['nb_early_learning'],
                         min_leaning_rate = parameters['min_leaning_rate'], normalize=parameters['normalize'])

    def build_model(self, N=5, lbd_I=0.05, lbd_J=0.01, learning_rate=0.01, epoch=30, batch_size=50, decay=0.5, nb_early_learning = 10, min_leaning_rate = 0.025, normalize=False):
        if len(self.decks) == 0 or len(self.test_cards) == 0: return;

        # print('Build models ...')
        self._init_coefficients()

        ep = 0
        while ep < epoch and learning_rate >= min_leaning_rate:
            #print('Epoch ' + str(ep) + ', learning rate: ' + str(learning_rate))
            decks, items_i, items_j = self._get_sampling(batch_size)

            #update learning rate
            learning_rate = self._step_decay(learning_rate, decay, nb_early_learning)
            #print('learning rate: ' + str(learning_rate))

            #print('Train...')
            for i in range(batch_size):
                self._train(decks[i], items_i[i], items_j[i], lbd_I, lbd_J, learning_rate)

            evaluation = self._eval(N)
            #print('HR: ' + str(round(evaluation[0], 4)) + ', ARHR: ' + str(round(evaluation[1], 4)))

            self.scores.append(evaluation)
            self._add_evaluations(evaluation[0], evaluation[1], nb_early_learning)
            ep += 1

        if normalize:
            self._normalize()

    def _get_testing_scores(self, built_deck, n_recommendations):
        '''
        Return the top N recommendations greater than 0 depending of the card selected in the deck passed in argument
        :param built_deck: deck being built by user
        :param n_recommendations: number of recommendations
        :return: list of items recommended
        '''
        deck = np.zeros(self.nb_cards)
        for id in built_deck:
            deck[id] = 1

        res = np.zeros(self.nb_cards)
        for i in range(self.nb_cards):
            res[i] = self.C[i].dot(deck)

        for index in built_deck:
            res[index] = 0.0

        recommendations = res.argsort()[::-1][:n_recommendations]
        non_zero = [x for x in recommendations if res[x] > 0.0]

        return np.array(non_zero), res

    def get_top_N_recommendations(self, built_deck, n_recommendations):
        '''
        Return the top N recommendations greater than 0 depending of the card selected in the deck passed in argument
        :param built_deck: deck being built by user
        :param n_recommendations: number of recommendations
        :return: list of items recommended
        '''
        encoded_deck = self.encode_deck(built_deck)
        recommendations, results = self._get_testing_scores(encoded_deck, n_recommendations)
        decoded_results = deque()
        for index in recommendations:
            decoded_results.append(self.decoder[index])

        res = pd.Series(0.0, index=decoded_results)
        for i, card in enumerate(decoded_results):
            res[card] = results[recommendations[i]]

        res = res.nlargest(n_recommendations)
        return res[res > 0.0]

    def get_contributions(self, recommendations, built_deck, thresold=None, max_contributors = 5):
        '''
        Return for each recommendations the n cards with the most influence on the recommendation
        :param recommendations: list of recommendations
        :param built_deck: selected cards by the player used for the recommendations
        :param thresold: minimum percentage value to be considered have an influence on the recommendations
        :param max_contributors: maximum number of influential cards returned for each recommendation
        :return: hash with the recommendation as key, and an array of pair values (contributor, percentage of contribution)
        '''
        encoded_recommendations = self.encode_deck(recommendations)
        encoded_deck = self.encode_deck(built_deck)
        contribution = {}

        if thresold is None:
            thresold = 1.0/len(built_deck)

        matrix_contributions = np.zeros((len(recommendations), len(built_deck)), dtype=np.float64)
        for i, rec_card in enumerate(encoded_recommendations):
            sum = 0.0
            for j, built_card in enumerate(encoded_deck):
                matrix_contributions[i][j] = self.C[rec_card][built_card]
                sum += self.C[rec_card][built_card]

            matrix_contributions[i] = matrix_contributions[i] / sum
            indexes = matrix_contributions[i].argsort()[::-1]

            relevant_cards = [(self.decoder[encoded_deck[x]], matrix_contributions[i][x]) for x in indexes if matrix_contributions[i][x] > thresold]
            contribution[self.decoder[rec_card]] = relevant_cards[0:max_contributors]
        return contribution

    def save_coefficients(self, path):
        '''
        Save model's coefficients and cards used when learning the model
        '''

        self.save_string_coefficients(path)

        ''' For numpy binary format
        serialized_model = {}
        memfile = BytesIO()
        np.save(memfile, self.C, allow_pickle=False)
        memfile.seek(0)
        serialized_model['coefficients'] = memfile.read().decode('latin-1') # latin-1 maps byte n to unicode code point n

        #serialized_model['coefficients'] = json.dumps([str(self.C.dtype), base64.b64encode(self.C), self.C.shape])

        serialized_model['cards'] = self.cards

        with open(path, 'w') as outfile:
            json.dump(serialized_model, outfile)
        '''

    def save_binary_coefficients(self, path):
        np.save(path, self.C, allow_pickle=False)

    def save_string_coefficients(self, path):
        serialized_model = {}

        serialized = []
        for i in range(len(self.C)):
            serialized.append(self.C[i].tolist())

        serialized_model['coefficients'] = serialized
        serialized_model['cards'] = self.cards

        with open(path, 'w') as outfile:
            json.dump(serialized_model, outfile)

    @staticmethod
    def load_coefficients(path):
        '''
        Load model's coefficients and cards from saving file
        '''

        with open(path) as f:
            data = json.load(f)

        model = BPRKNN(data['cards'], None, None)

        memfile = BytesIO()
        memfile.write(data['coefficients'].encode('latin-1'))
        memfile.seek(0)
        model.C = np.load(memfile)

        return model

    @staticmethod
    def load_coefficients_from_string(path):
        with open(path) as f:
            data = json.load(f)

        model = BPRKNN(data['cards'], None, None)
        model.C = np.asarray(data['coefficients'],dtype=np.float64).reshape((len(model.cards), len(model.cards)))
        a = 0
        return model

    @staticmethod
    def get_default_parameters():
        return {'N':5, 'lbd_I':0.05, 'lbd_J':0.01, 'learning_rate':0.01, 'epoch':30, 'batch_size':50, 'decay':0.5,
                'nb_early_learning': 10, 'min_leaning_rate': 0.025, 'normalize':False}

    def _train(self, deck, item_i, item_j, lbd_I, lbd_J, learning_rate):
        '''
        Learn coefficients for C based on stochastic gradient descent
        :param deck: current deck processed
        :param item_i: item i in deck
        :param item_j: item j in deck
        '''

        x_di = sum([self.C[item_i,card] for card in deck if item_i != card])
        x_dj = sum([self.C[item_j,card] for card in deck if item_j != card])
        x_dij = x_di - x_dj

        gradientC = defaultdict(float)
        for card in deck:
            if card != item_i:
                gradientC[(item_i, card)] += (1 - expit(x_dij)) + lbd_I * self.C[item_i,card]
                gradientC[(card, item_i)] += (1 - expit(x_dij)) + lbd_I * self.C[card,item_i]
            else:
                gradientC[(item_i, card)] += lbd_I * self.C[item_i,card]
                gradientC[(card, item_i)] += lbd_I * self.C[card,item_i]

            if card != item_j:
                gradientC[(item_j, card)] += -(1 - expit(x_dij)) + lbd_J * self.C[item_j,card]
                gradientC[(card, item_j)] += -(1 - expit(x_dij)) + lbd_J * self.C[card,item_j]
            else:
                gradientC[(item_j, card)] += lbd_J * self.C[item_j,card]
                gradientC[(card, item_j)] += lbd_J * self.C[card,item_j]

        for a, b in gradientC:
            self.C[a, b] += self._compute_momentum(a, b, learning_rate, gradientC[(a,b)])


    def _eval(self, N):
        '''
        Compute DeltaC
        '''

        nb_hits = 0
        arhr = 0
        for i, deck in enumerate(self.decks):
            recommendations, _ = self._get_testing_scores(deck, N)
            if self.test_cards[i] in recommendations:
                position = np.argwhere(recommendations==self.test_cards[i])[0][0] + 1 #array index starts at 0 ...
                arhr += 1.0 / position
                nb_hits += 1
        hr = nb_hits / len(self.decks)
        arhr = arhr / len(self.decks)
        return [hr, arhr]

    def _init_coefficients(self):
        '''
        Initialize the model's coefficients
        '''
        #print('Init coefficients ...')
        self.C = np.random.rand(self.nb_cards, self.nb_cards)
        for i in range(self.nb_cards):
            self.C[i, i] = 0.0
            for j in range(i + 1, self.nb_cards):
                self.C[j, i] = self.C[i,j]

    def _get_sampling(self, batch_size):
        '''
        Return a random triplet of deck, card, card
        The random function is normally distributed
        :return: triplet (deck, card selected in deck, card not selected in deck)
        '''

        #print('Get samplings ...')

        samp_decks = deque()
        samp_items_i = deque()
        samp_items_j = deque()

        for _ in range(batch_size):
            index_deck = np.random.randint(0, len(self.decks))
            while len(self.decks[index_deck]) <= 1:
                index_deck = np.random.randint(0, len(self.decks))

            index_item_i = np.random.randint(0, len(self.decks[index_deck]))

            difference = list(frozenset(range(self.nb_cards)).difference(self.decks[index_deck]))
            index_item_j = np.random.randint(0, len(difference))

            samp_decks.append(self.decks[index_deck])
            samp_items_i.append(self.decks[index_deck][index_item_i])
            samp_items_j.append(difference[index_item_j])

        return [samp_decks, samp_items_i, samp_items_j]

    def _step_decay(self, learning_rate, decay, n_eval):
        if not self._is_still_learning(n_eval):
            #print('Not learning anymore ...')
            learning_rate = learning_rate * decay
            self.last_evaluations.clear() #wait n epochs before reevaluating
        return learning_rate

    def get_scores(self):
        return self.scores

    def get_name(self):
        return 'bprknn'

    def _compute_momentum(self, a, b, learning_rate, gradientC):
        '''
        source: https://towardsdatascience.com/stochastic-gradient-descent-with-momentum-a84097641a5d
        :return: current momentum
        '''

        coefficient = 0.5

        #self.momentum[(a,b)] = coefficient * self.momentum[a,b + (1.0-coefficient) * self.gradientC[(a,b)]
        #res = learning_rate *self.momentum[(a,b)]

        self.momentum[a,b] = coefficient * self.momentum[a,b] + learning_rate * gradientC
        return self.momentum[a,b]

    def _add_evaluations(self, hr, arhr, n_eval):
        if len(self.last_evaluations) >= n_eval:
            self.last_evaluations.popleft()
        self.last_evaluations.append((hr,arhr))

    def _is_still_learning(self, n_eval):
        if len(self.last_evaluations) >= n_eval:
            current_hr, current_arhr, delta_hr, delta_arhr = 0, 0, 0, 0
            previous_hr, previous_arhr = self.last_evaluations[n_eval - 1]
            for i in reversed(range(n_eval - 1)):
                current_hr, current_arhr = self.last_evaluations[i]
                delta_hr += (current_hr - previous_hr)
                delta_arhr += (current_arhr - previous_arhr)
                previous_hr = current_hr
                previous_arhr = current_arhr

            #print('delta: ' + str(abs(delta_hr + delta_arhr)))
            return abs(delta_hr + delta_arhr) > 0.001

        else:
            #print('delta: N/A')
            return True

    def _normalize(self):
        for j in range(len(self.C)):
            norm = np.linalg.norm(self.C[:][j])
            self.C[:][j] /= norm