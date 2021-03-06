# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2018 Xavier FOLCH
#

import os
import json
import pandas as pd
from tqdm import tqdm
from loader.deck_manager import MagicLoader, DeckManager
from collaborative_filtering.item_to_item import ItemToItem
from lsa.lsa_encoder import LSAManager
from multiprocessing import Pool, Manager
from time import time
import numpy as np

class JobData:
    '''
    Encapsulate data for jobs processing similarities
    '''
    def __init__(self,  game_mode, game_colors, game_card_catalog, game_deck_database, cards_content_similarities):
        self.game_mode = game_mode
        self.game_colors = game_colors
        self.game_card_catalog = game_card_catalog
        self.game_deck_database = game_deck_database
        self.cards_content_similarities = cards_content_similarities

def encoding_magic_card(card_loader):
    hash_id_texts = {}
    for multiverseid, card in card_loader.cards_multiverseid.items():
        hash_id_texts[multiverseid] = card.full_text

    lsa_manager = LSAManager(hash_id_texts)
    lsa_manager.encode()
    return lsa_manager

def encoding_magic_card_subsets(cards):
    hash_id_texts = {}
    for card in cards:
        hash_id_texts[card.multiverseid] = card.full_text

    lsa_manager = LSAManager(hash_id_texts)
    lsa_manager.encode()
    return lsa_manager

def load_magic_environment():
    print('Load deck')
    card_loader = MagicLoader()
    #card_loader.load('./../data/magic_cards/AllCards-x.json')
    card_loader.load_from_set('./../data/magic_cards/AllSets-x.json')
    return card_loader

def load_decks_database(card_loader):
    print('Clean deck')
    deck_loader = DeckManager()

    files = os.listdir("./../data/decks_mtgdeck_net")  # returns list
    paths = []
    for file in files:
        paths.append('./../data/decks_mtgdeck_net/' + file)
    deck_loader.load_from_mtgdeck_csv(paths, card_loader)
    deck_loader.extract_lands(card_loader.lands, card_loader)
    deck_loader.sort_decks()

    return deck_loader

def process_content_similarities(lsa_manager, multiverseid_in_decks):
    '''
    Compute the similarities for all the cards present in decks to avoid unecessary computing when
    processing the different decks modes and colors
    :param lsa_manager: lsa containing cards encoding
    :param multiverseid_in_decks: list of multiverseids present in all the decks to process
    :return: panda frame with all the similarities
    '''
    df = pd.DataFrame(np.nan, index=multiverseid_in_decks, columns=multiverseid_in_decks)
    for card_index1 in tqdm(range(len(multiverseid_in_decks))):
        for card_index2 in range(card_index1, len(multiverseid_in_decks)):
            card_1 = multiverseid_in_decks[card_index1]
            card_2 = multiverseid_in_decks[card_index2]

            similarity = lsa_manager.get_similarity(card_1, card_2)
            df.at[card_1, card_2] = similarity
            df.at[card_2, card_1] = similarity

    return df

def do_job(game_mode, game_colors, game_card_catalog, game_deck_database, cards_content_similarities, queue):
    """
    Process item to itemm recommendations for all the cards in the game deck database for the colors set in argument
    :param game_mode: mode from which the decks are coming from
    :param game_colors: colors to process in the deck database
    :param game_card_catalog: list of cards in all the decks
    :param game_deck_database: list of decks
    :param cards_content_similarities: matrix containing the similarities by text for all the cards
    :param queue: result queue used to send back the results
    :return: none
    """
    similiraties = {}
    for color in game_colors:
        print('Start processing ' + game_mode + ' - ' + str(MagicLoader.get_json_color(color)) + ':')
        deck_database = game_deck_database[color]
        card_catalog = game_card_catalog[color]

        item_recommender = ItemToItem(list(card_catalog))

        print(game_mode + ' - ' + str(MagicLoader.get_json_color(color)) + ': Load Ratings...')
        item_recommender.load_ratings(deck_database)

        print(game_mode + ' - ' + str(MagicLoader.get_json_color(color)) + ': Compute similarities...')
        item_recommender.compute_similarities(deck_database, ItemToItem.compute_cosine_angle_binary)

        print(game_mode + ' - ' + str(MagicLoader.get_json_color(color)) + ': Get recommendations for '+ str(len(card_catalog)) + ' cards ...')
        for id_card in card_catalog:
            if id_card not in similiraties:
                similiraties[id_card] = {}

            # recommendations = item_recommender.get_recommendation(id_card, 5, cards_content_similarities)
            recommendations = get_item_recommendation(id_card, item_recommender, cards_content_similarities, 5)

            suggestions = []
            for id_rec, score in recommendations.items():
                suggestions.append({'multiverseid': int(id_rec), 'itemSimilarity': round(score[0], 3),
                                    'contentSimilarity': round(score[1], 3)})

            if game_mode not in similiraties[id_card]:
                similiraties[id_card][game_mode] = {}

            if game_mode not in similiraties[id_card][game_mode]:
                similiraties[id_card][game_mode][color] = None

            similiraties[id_card][game_mode][color] = suggestions
        print(game_mode + ' - ' + str(MagicLoader.get_json_color(color)) + ': Done!')
    queue.put(similiraties)

def worker(id, jobs_queue, results_queue):
    while True:
        data = jobs_queue.get()
        if data is None:
            return 0

        game_colors = data.game_colors
        game_deck_database = data.game_deck_database
        game_card_catalog = data.game_card_catalog
        game_mode = data.game_mode
        cards_content_similarities = data.cards_content_similarities
        queue = results_queue

        do_job(game_mode, game_colors, game_card_catalog, game_deck_database, cards_content_similarities, queue)

def get_content_recommendation(multiverseid, cards_content_similarities, nb_recommendations):
    similarities = cards_content_similarities[multiverseid]
    similarities = similarities.sort_values(ascending=False)

    recommendations = []
    nb_recommendations = min(nb_recommendations, len(similarities)) + 1
    for i in range(1,nb_recommendations): #to avoid itself in the recommendations
        recommendations.append({'multiverseid': int(similarities.index[i]), 'contentSimilarity': round(similarities.iloc[i],3), 'itemSimilarity': None})

    return recommendations

def get_item_recommendation(multiverseid, item_manager, cards_content_similarities, nb_recommendations):
        '''
        Return the list of the first nb_recommendations
        :param card_id: id card of which we want the recommendations
        :param nb_recommendations: number of recommendations to return
        :param lsa: language semantic analysis object from lsa package
        :return: dictionary {card_id: recommendation}
        '''

        item_similarities = item_manager.items_similarities.loc[multiverseid]

        #Remove null or negative similarities
        item_similarities = item_similarities[item_similarities > 0.0].dropna()
        content_similarities = cards_content_similarities[multiverseid]

        similarities = pd.DataFrame(columns=['card_id','item_similarity','content_similarity'])
        for new_card_id in item_similarities.index:
            new_card = pd.DataFrame(index=[new_card_id], columns=['item_similarity','content_similarity'])
            new_card['item_similarity'] = item_similarities.loc[new_card_id]
            new_card['content_similarity'] = content_similarities[new_card_id]
            similarities = similarities.append(new_card)

        similarities = similarities.sort_values(['item_similarity', 'content_similarity'], ascending=[False, False])
        recommendations = {}
        nb = min(nb_recommendations, len(similarities))
        for i in range(nb):
            sim = similarities.iloc[i]
            recommendations[similarities.index[i]] = [sim['item_similarity'],sim['content_similarity']]
        return recommendations

def process_recommendations(decks_by_mode, cards_content_similarities):
    '''
    Producer / Consumer model for multithreading
    :param: hash of decks grouped by game mode
    :return: queue with the results
    '''

    deck_series = []
    for mode in decks_by_mode.keys():
        deck_loader = decks_by_mode[mode]
        deck_database = deck_loader.grouped_decks
        card_catalog = deck_loader.grouped_cards

        print('mode: ' + mode)
        for color in deck_loader.grouped_decks.keys():
            print('  - ' + str(MagicLoader.get_json_color(color)) + ': ' + str(len(deck_loader.grouped_decks[color])))
            deck_series.append(JobData(mode, [color], card_catalog, deck_database, cards_content_similarities))

    number_wokers = 4
    manager = Manager()
    pool = Pool(processes=number_wokers)
    jobs_queue = manager.Queue()
    results_queue = manager.Queue()

    for item in deck_series:
        jobs_queue.put(item)

    # stop workers
    for i in range(number_wokers):
        jobs_queue.put(None)

    for i in range(number_wokers):
        results = pool.apply_async(worker, (i, jobs_queue, results_queue))

    pool.close()
    pool.join()

    return results_queue

def compute_similarities_multi_thread():
    start= time()

    print('Load magic environment')
    card_loader = load_magic_environment()

    files = os.listdir("./../data/decks_mtgdeck_net_extended")  # returns list
    paths = []
    for file in files:
        paths.append('./../data/decks_mtgdeck_net_extended/' + file)

    decks = {}
    multiverseid_in_decks = set()
    for mode in MagicLoader.HASH_GAME_STRING_CODE.keys():
        for path in paths:
            if mode.lower() in path:
                deck_loader = DeckManager()
                deck_loader.load_from_mtgdeck_csv([path], cards_loader=card_loader, ignore_land=True)
                deck_loader.sort_decks()
                multiverseid_in_decks = multiverseid_in_decks.union(deck_loader.cards)
                decks[mode] = deck_loader

        if mode in decks:
            print('Mode ' + str(mode) + ':')
            for color, list_decks in decks[mode].grouped_decks.items():
                print(' - ' + MagicLoader.get_json_color(color) + ': ' + str(len(list_decks)) + ' decks')

    # In the context of this study only:
    # To be sure that all the cards in the final recommendation json will have similarities score
    # On real website, procede with all Magic Cards to be more exhaustive
    print('Convert only the text of magic cards in decks into vector: ' + str(len(multiverseid_in_decks)) + ' cards')
    list_multiverseid_in_decks = list(multiverseid_in_decks)
    cards_in_decks = card_loader.extract_cards(list_multiverseid_in_decks)
    lsa_manager = encoding_magic_card_subsets(cards_in_decks)

    cards_content_similarities = process_content_similarities(lsa_manager, list_multiverseid_in_decks)
    results_queue = process_recommendations(decks, cards_content_similarities)

    print('End processing ratings and similarities')
    print('Consolidate results')

    similiraties = {}
    #for game_similarity in tqdm(iter(queue.get, None)):
    while not results_queue.empty():
        game_similarity = results_queue.get()
        for card in game_similarity.keys():
            key_card = str(card)
            if key_card not in similiraties:
                similiraties[key_card] = {}

            for game_mode in game_similarity[card].keys():
                if game_mode not in similiraties[key_card]:
                    similiraties[key_card][game_mode] = {}

                for color in game_similarity[card][game_mode].keys():
                    similiraties[key_card][game_mode][MagicLoader.get_json_color(color)] = game_similarity[card][game_mode][color]

    print('Save data into json')
    export = []
    for multiverseid, recommendations in tqdm(similiraties.items()):
        json_card = {}
        card = card_loader.cards_multiverseid[int(multiverseid)]
        json_card['multiverseid'] = card.multiverseid
        json_card['name'] = card.name
        json_card['manaCost'] = card.mana_cost
        json_card['types'] = card.types
        json_card['colors'] = card.get_colors_names()
        json_card['contentRecommendations'] = get_content_recommendation(int(multiverseid), cards_content_similarities, 5)
        json_card['itemRecommendations'] = similiraties[multiverseid]
        export.append(json_card)

    with open('./../similarities_multi.json', 'w') as f:
        print(str(export))
        json.dump(export, f)

    print('required time = ' + str((time() - start)) + ' seconds')

if __name__ == "__main__":
    compute_similarities_multi_thread()