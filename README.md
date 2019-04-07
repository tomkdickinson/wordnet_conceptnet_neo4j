# ConceptNet and WordNet to Neo4j

This script converts ConceptNet and WordNet into an integrated model, allowing search and expansion across both of
them.

## Docker

To make this script more accessible, you can run this code as a docker container with:

```docker run --network=host tomkdickinson/wordnet-conceptnet-neo4j```

You will find Neo4J running on localhost:7474. 

The default username/password is neo4j/neo4j, and when running for the first time it will ask you to change your password.