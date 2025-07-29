import csv
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["Project1"]     
collection = db["nodes"] 
collection = db["edges"]         


with open("edges2.tsv", newline='') as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter='\t')
    for row in reader:
        document = {
            "source": row["source"],
            "metaedge": row["metaedge"],
            "target": row["target"]
        }
        collection.insert_one(document)
print("Nodes TSV data inserted into MongoDB.")
print("Edges (relationships) inserted into MongoDB.")
