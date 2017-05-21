# ConceptNet and WordNet to Neo4j

This python script converts ConceptNet and WordNet into an integrated model, allow search and expansion across both of
them.

## Requirements
You will have to download ConceptNet from https://github.com/commonsense/conceptnet5/wiki/Downloads and include the
csv.gz in the same directory as the script.

You will also need to install nltk with:

```pip install nltk```

And download the WordNet database with it.


## Example import command

./neo4j-admin import --database={NEO4J_LOCATION}/data/databases/wordnet_conceptnet.db \
--nodes={PATH_TO_DATASET_FOLDER}/synsets.csv \
--relationships={PATH_TO_DATASET_FOLDER}/relationships.csv \
--nodes={PATH_TO_DATASET_FOLDER}/words.csv
