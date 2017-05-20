rm -rf ../data/databases/wordnet.db/ && \
./neo4j-admin import --database=wordnet.db \
--nodes=/Users/tkd29/PycharmProjects/Neo4JConceptNet/dataset/synsets.csv \
--relationships=/Users/tkd29/PycharmProjects/Neo4JConceptNet/dataset/relationships.csv \
--nodes=/Users/tkd29/PycharmProjects/Neo4JConceptNet/dataset/words.csv

# ConceptNet and WordNet to Neo4j

This python script converts ConceptNet and WordNet into an integrated model, allow search and expansion across both of
them.