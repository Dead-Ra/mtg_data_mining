import os
from loader_magic import MagicLoader, DeckManager
from collaborative_filtering.item_to_item import ItemToItem
from lsa_encoder import DataCleaner, LSAEncoder

def encoding_magic_card():
    loader = MagicLoader()
    loader.load('./../data/magic_cards/AllCards-x.json')
    cleaner = DataCleaner(loader.texts, loader.names)
    cleaner.clean()
    lsa_transformer = LSAEncoder(cleaner.clean_data)
    lsa_transformer.fit()
    lsa_transformer.print_similarity()
    return lsa_transformer

def load_magic_environment():
    print('Load deck')
    card_loader = MagicLoader()
    card_loader.load('./../data/magic_cards/AllCards-x.json')
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

    '''
    list_files = os.listdir("./../db_decks")  # returns list
    deck_loader.load_from_csv(list_files, card_loader)
    deck_loader.extract_lands(card_loader.lands, card_loader)
    '''

    return deck_loader

if __name__ == "__main__":
    print('Load magic environment')
    card_loader = load_magic_environment()
    deck_loader = load_decks_database(card_loader)

    print('Convert card text into vector')
    lsa_transformer = encoding_magic_card()

    catalog = sorted(list(deck_loader.cards))
    item_recommender = ItemToItem(list(deck_loader.cards))
    print('Get ratings')
    item_recommender.load_ratings(deck_loader.decks)
    print('Compute similarities')
    item_recommender.compute_similarities(deck_loader.decks)
    print('Get recommendations for 16622')
    recommendations = item_recommender.get_recommendation(16622, 10)
    print('Recommendation for ' + str(card_loader.hash_id_name[16622]) + ':')#16622, 620
    for id_card, score in recommendations.items():
        print('   - ' + str(card_loader.hash_id_name[id_card]) + ': ' + str(score))

    print('Get recommendations for 620')
    recommendations = item_recommender.get_recommendation(620, 10)
    print('Recommendation for ' + str(card_loader.hash_id_name[620]) + ':')#16622, 620
    for id_card, score in recommendations.items():
        print('   - ' + str(card_loader.hash_id_name[id_card]) + ': ' + str(score))