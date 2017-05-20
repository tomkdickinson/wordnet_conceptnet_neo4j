# ConceptNet and WordNet to Neo4j

This python script converts ConceptNet and WordNet into an integrated model, allow search and expansion across both of
them.


## Example import command

./neo4j-admin import --database={NEO4J_LOCATION}/data/databases/wordnet_conceptnet.db \
--nodes={PATH_TO_DATASET_FOLDER}/synsets.csv \
--relationships={PATH_TO_DATASET_FOLDER}/relationships.csv \
--nodes={PATH_TO_DATASET_FOLDER}/words.csv
