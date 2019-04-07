import nltk
import nltk.corpus
import csv
import json
import logging as log
import gzip
import math
import os
import re

log.basicConfig(level=log.INFO)


class WordNode:
    def __init__(self, id, name, pos, is_lemma=False, is_concept=False, concept_uri=None):
        self._id = id
        self._name = name
        self._pos = pos
        self._concept_uri = concept_uri
        self._is_lemma = is_lemma
        self._is_concept = is_concept
        if not is_lemma and not is_concept:
            raise Exception('WordNode must be at least either a lemma or a concept')

    @staticmethod
    def get_header():
        return ['id:ID', 'name', 'pos', 'conceptUri', ':LABEL']

    def get_row(self):
        labels = []
        if self._is_lemma:
            labels.append('Lemma')
        if self._is_concept:
            labels.append('Concept')
        return [self._id, self._name, self._pos, self._concept_uri, ';'.join(labels)]

    @property
    def get_id(self):
        return self._id

    def set_is_concept(self):
        self._is_concept = True

    @property
    def get_concept_uri(self):
        return self._concept_uri

    def set_concept_uri(self, concept_uri):
        self._concept_uri = concept_uri


class SynsetNode:
    def __init__(self, id, pos, definition):
        self._label = 'Synset'
        self._id = id
        self._pos = pos
        self._definition = definition

    @property
    def get_id(self):
        return self._id

    @property
    def get_pos(self):
        return self._pos

    @property
    def get_definition(self):
        return self._definition

    @property
    def get_label(self):
        return self._label


class Exporter:
    """
    This class exports WordNet into a csv file for ingestion into Neo4J
    """

    def __init__(self, dataset_folder, concept_location=None, language_filter=None):
        self.dataset_folder = dataset_folder
        os.makedirs(self.dataset_folder, exist_ok=True)
        self.relationships = []
        self.relationship_index = {}
        self.words = []
        self.synsets = []
        self.lemma_map = {}
        self.concept_location = concept_location
        self.language_filter = language_filter

    def export(self):
        self.extract_wordnet()
        if self.concept_location is not None:
            self.extract_conceptnet()
        self.write_results()

    def extract_wordnet(self):
        """
        Extracts wordnet
        :return:
        """
        log.info('Extracting WordNet')
        all_synsets = list(nltk.corpus.wordnet.all_synsets())
        last_progress = 0
        for i, synset in enumerate(all_synsets):
            self.synsets.append(SynsetNode(synset.name(), synset.pos(), synset.definition()))
            self.extract_relationships(synset)
            self.extract_lemmas(synset)
            progress = math.floor((i / len(all_synsets) * 100))
            if progress > last_progress:
                last_progress = progress
                log.info("%f%% Synsets extracted" % progress)

    def extract_conceptnet(self):
        log.info('Extracting ConceptNet')
        last_progress = 0
        with gzip.open(self.concept_location, 'rt') as f:
            lines = csv.reader(f, delimiter='\t')
            i = 0
            for line in lines:
                start = self.extract_concept(line[2])
                end = self.extract_concept(line[3])
                if start is not None and end is not None:
                    self.add_concept_node(start)
                    self.add_concept_node(end)
                    dataset, weight = self.extract_edge_details(line[4])
                    self.add_relationship(start.get_id, end.get_id, re.sub('/r/', '', line[1]), dataset, weight)

                i += 1
                progress_round = 10000
                progress = math.floor(i / progress_round) * progress_round
                if progress > last_progress:
                    last_progress = progress
                    log.info('Extracted %i concept assertions' % progress)

    def extract_edge_details(self, edge_string):
        try:
            dataset = None
            weight = None
            edge = json.loads(edge_string)
            if 'dataset' in edge:
                dataset = edge['dataset']
            if 'weight' in edge:
                try:
                    weight = float(edge['weight'])
                except Exception as e:
                    log.error(e)
            return dataset, weight
        except Exception as e:
            log.error(e)
            return None, None

    def add_concept_node(self, concept):
        if concept is not None:
            if concept.get_id in self.lemma_map:
                self.lemma_map[concept.get_id.lower()].set_is_concept()
            else:
                self.lemma_map[concept.get_id.lower()] = concept
            self.lemma_map[concept.get_id.lower()].set_concept_uri(concept.get_concept_uri)

    def extract_concept(self, concept_uri):
        concept_parts = concept_uri[1:].split('/')
        if self.language_filter is None or concept_parts[1] == self.language_filter:
            if len(concept_parts) > 3:
                return WordNode(id='%s.%s' % (concept_parts[2], concept_parts[3]), pos=concept_parts[3],
                                name=concept_parts[2], concept_uri=concept_uri, is_concept=True)
            else:
                return WordNode(id=concept_parts[2], pos=None, name=concept_parts[2], concept_uri=concept_uri,
                                is_concept=True)
        return None

    def extract_relationships(self, synset):
        # Hyponyms - Child
        for related_node in synset.hyponyms():
            self.add_relationship(related_node.name(), synset.name(), 'IsA', weight=2, dataset="/d/wordnet/3.1")

        # Hypernyms - Parent
        for related_node in synset.hypernyms():
            self.add_relationship(synset.name(), related_node.name(), 'IsA', weight=2, dataset="/d/wordnet/3.1")

        # Holonyms

        # Member Holonyms
        for related_node in synset.member_holonyms():
            self.add_relationship(synset.name(), related_node.name(), 'PartOf', weight=2, dataset="/d/wordnet/3.1")

        # substance_holonyms
        for related_node in synset.substance_holonyms():
            self.add_relationship(synset.name(), related_node.name(), 'PartOf', weight=2, dataset="/d/wordnet/3.1")

        # part_holonyms
        for related_node in synset.part_holonyms():
            self.add_relationship(synset.name(), related_node.name(), 'PartOf', weight=2, dataset="/d/wordnet/3.1")

        # Meronyms Child

        # Member meronyms
        for related_node in synset.member_meronyms():
            self.add_relationship(related_node.name(), synset.name(), 'PartOf', weight=2, dataset="/d/wordnet/3.1")

        # substance_meronyms
        for related_node in synset.substance_meronyms():
            self.add_relationship(related_node.name(), synset.name(), 'PartOf', weight=2, dataset="/d/wordnet/3.1")

        # part_meronyms
        for related_node in synset.part_meronyms():
            self.add_relationship(related_node.name(), synset.name(), 'PartOf', weight=2, dataset="/d/wordnet/3.1")

        # Domains

        # topic_domains
        for related_node in synset.topic_domains():
            self.add_relationship(synset.name(), related_node.name(), 'Domain', weight=2, dataset="/d/wordnet/3.1")

        # region_domains
        for related_node in synset.region_domains():
            self.add_relationship(synset.name(), related_node.name(), 'Domain', weight=2, dataset="/d/wordnet/3.1")

        # usage_domains
        for related_node in synset.usage_domains():
            self.add_relationship(synset.name(), related_node.name(), 'Domain', weight=2, dataset="/d/wordnet/3.1")

        # attributes
        for related_node in synset.attributes():
            self.add_relationship(synset.name(), related_node.name(), 'Attribute', weight=2, dataset="/d/wordnet/3.1")
        # entailments
        for related_node in synset.entailments():
            self.add_relationship(synset.name(), related_node.name(), 'Entailment', weight=2, dataset="/d/wordnet/3.1")
        # causes
        for related_node in synset.causes():
            self.add_relationship(synset.name(), related_node.name(), 'Cause', weight=2, dataset="/d/wordnet/3.1")
        # also_sees
        for related_node in synset.also_sees():
            self.add_relationship(synset.name(), related_node.name(), 'AlsoSee', weight=2, dataset="/d/wordnet/3.1")
        # verb_groups
        for related_node in synset.verb_groups():
            self.add_relationship(synset.name(), related_node.name(), 'VerbGroup', weight=2, dataset="/d/wordnet/3.1")
        # similar_tos
        for related_node in synset.similar_tos():
            self.add_relationship(synset.name(), related_node.name(), 'SimilarTo', weight=2, dataset="/d/wordnet/3.1")

    def extract_lemmas(self, synset):
        for lemma in synset.lemmas():
            id = ('%s.%s' % (lemma.name().lower(), synset.pos())).lower()
            if id not in self.lemma_map:
                self.lemma_map[id] = WordNode(id, lemma.name().lower(), synset.pos(), is_lemma=True)
            self.add_relationship(id, synset.name(), 'InSynset', weight=2, dataset="/d/wordnet/3.1")

    def index_relationship(self, start, end, rel_type):
        self.relationship_index.setdefault(start, {})
        self.relationship_index[start].setdefault(end, [])
        self.relationship_index[start][end].append(rel_type)

    def add_relationship(self, start, end, rel_type, dataset=None, weight=None):
        """
        Checks and adds only bi-directional relationships
        :param start:
        :param end:
        :param rel_type:
        :param dataset:
        :param weight:
        :return:
        """
        if (start in self.relationship_index and end in self.relationship_index[start] and rel_type in
            self.relationship_index[start][end]) or \
                (end in self.relationship_index and start in self.relationship_index[end] and rel_type in
                 self.relationship_index[end][start]):
            pass
        else:
            self.index_relationship(start, end, rel_type)
            self.index_relationship(end, start, rel_type)
            self.relationships.append([start, end, dataset, weight, rel_type])

    def write_results(self):
        log.info("Writing synsets")
        with open('%s/synsets.csv' % self.dataset_folder, 'w', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['id:ID', 'pos:string', 'definition:string', ':LABEL'])
            for synset in self.synsets:
                writer.writerow([synset.get_id, synset.get_pos, synset.get_definition, synset.get_label])

        log.info('Writing Relationships')
        with open('%s/relationships.csv' % self.dataset_folder, 'w', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([':START_ID', ':END_ID', 'dataset:string', 'weight:double', ':TYPE'])
            for relationship in self.relationships:
                writer.writerow(relationship)

        log.info('Writing Words')
        with open('%s/words.csv' % self.dataset_folder, 'w', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(WordNode.get_header())
            for id in self.lemma_map:
                writer.writerow(self.lemma_map[id].get_row())


if __name__ == '__main__':
    nltk.download('wordnet')
    Exporter('neo4j_csv_imports', 'conceptnet-assertions.csv.gz', language_filter='en').export()
