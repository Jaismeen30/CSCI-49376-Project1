import csv
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["Project1"]     
nodes_collection = db["nodes"]
edges_collection = db["edges"]    

with open("nodes2.tsv", newline='') as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter='\t')
    for row in reader:
        document = {
            "_id": row["id"],
            "name": row["name"],
            "kind": row["kind"]
        }
        nodes_collection.insert_one(document)
print("Nodes TSV data inserted into MongoDB.")

with open("edges2.tsv", newline='') as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter='\t')
    for row in reader:
        document = {
            "source": row["source"],
            "metaedge": row["metaedge"],
            "target": row["target"]
        }
        edges_collection.insert_one(document)

print("Edges (relationships) inserted into MongoDB.")
