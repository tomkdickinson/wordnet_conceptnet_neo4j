# Python Build
FROM python:3.7.3-alpine as dataset_build

WORKDIR /build/

RUN apk update && apk add bash && apk add curl
COPY download_conceptnet.sh .
RUN sh download_conceptnet.sh

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY wordnet_conceptnet_to_neo4j.py .

RUN python wordnet_conceptnet_to_neo4j.py


# Neo4J instance build
FROM openjdk:8-jre-alpine

ENV PATH=$PATH:/neo4j/bin/:.

# Setup Neo4J
RUN apk update && apk add bash
RUN wget http://dist.neo4j.org/neo4j-community-3.5.4-unix.tar.gz
RUN tar -xvf neo4j-community-3.5.4-unix.tar.gz -C .
RUN mv neo4j-community-3.5.4 neo4j


COPY --from=0 /build/neo4j_csv_imports/. /imports/.
RUN neo4j-admin import --database=graph.db --relationships=/imports/relationships.csv --nodes=/imports/words.csv --nodes=/imports/synsets.csv
RUN rm -rf /imports

# Container
FROM openjdk:8-jre-alpine

EXPOSE 7474 7473 7687
ENV PATH=$PATH:/neo4j/bin/:.

# Setup Neo4J
RUN apk update && apk add bash

COPY --from=1 /neo4j .

CMD neo4j console
