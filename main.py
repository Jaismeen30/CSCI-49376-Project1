from neo4j import GraphDatabase
from pymongo import MongoClient


URI = "bolt://localhost:7687"     
USERNAME = "neo4j"
PASSWORD = "Jaismeen30"

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "hetionet"


class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()


    
    def query_disease_info(self, disease_id):
        query = """
        MATCH (d:Disease {id: $disease_id})
        MATCH (t:Compound)-[:CtD]->(d)
        MATCH (p:Compound)-[:CpD]->(d)
        OPTIONAL MATCH (d)-[:DaG|DuG|DdG]->(g:Gene)
        MATCH (d)-[:DlA]->(a:Anatomy)
        RETURN 
            d.name AS Disease_name,
            collect(DISTINCT t.name) AS Treatments,
            collect(DISTINCT p.name) AS Palliates,
            collect(DISTINCT g.name) AS Genes,
            collect(DISTINCT a.name) AS Locations
        """
        with self.driver.session() as session:
            result = session.run(query, {"disease_id": disease_id})
            return result.single()
        

def find_compounds(db):
    nodes = db["nodes"]
    edges = db["edges"]
    # all compound to gene regulation edges
    compound_gene_edges = list(edges.find({
        "metaedge": {"$in": ["CuG", "CdG"]}
    }))

    # anatomy to gene regulation edges
    anatomy_gene_edges = list(edges.find({
        "metaedge": {"$in": ["AdG", "AuG"]}
    }))

    #Index by gene for quick lookup
    gene_to_anatomy = {}
    for edge in anatomy_gene_edges:
        gene_id = edge["target"]
        gene_to_anatomy.setdefault(gene_id, []).append(edge)

    #link genes through anatomy to diseases
    anatomy_to_diseases = {}
    for edge in edges.find({"metaedge": "DlA"}):
        anatomy_id = edge["target"]
        disease_id = edge["source"]
        anatomy_to_diseases.setdefault(anatomy_id, set()).add(disease_id)

    #exclude known treatments/palliatives
    excluded_compounds = set(
        (e["source"]) 
        for e in edges.find({"metaedge": {"$in": ["CtD", "CpD"]}})
    )
    
    candidate_compounds = set()
    for edge in compound_gene_edges:
        compound_id = edge["source"]
        gene_id = edge["target"]
        compound_reg = edge["metaedge"]

        for anat_edge in gene_to_anatomy.get(gene_id, []):
            anatomy_id = anat_edge["source"]
            anat_reg = anat_edge["metaedge"]

            # Check for opposite directionality
            if (compound_reg == "CuG" and anat_reg == "AdG") or (compound_reg == "CdG" and anat_reg == "AuG"):
                    if compound_id not in excluded_compounds:
                        candidate_compounds.add(compound_id)

   
    results = nodes.find({
        "id": {"$in": list(candidate_compounds)},
        
    })
    return  [doc["name"] for doc in results if "name" in doc]

   


def print_menu():
    print("\n")
    print("1. Get Disease info")
    print("2. Compounds that can treat a new disease ")
    print("3. Exit")

def main():
    
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["hetionet"]
    nodes = db["nodes"]
    edges = db["edges"]
    
    client = Neo4jClient(URI, USERNAME, PASSWORD) 

    try:
        while True:
            print_menu()
            choice = input("Choose an option (1-3): ")

            if choice == "1":
                disease_id = input("Enter disease ID (e.g. Disease::DOID:10763): ")
                result = client.query_disease_info(disease_id)
                if result:
                    print("\nDisease Info:")
                    for key, value in result.items():
                        if isinstance(value, list):
                            print(f"{key}:\n  {', '.join(str(v) for v in value)}\n")
                        else:
                            print(f"{key}: {value}\n")

            elif choice == "2":
                result = find_compounds(db)
                if result:
                    print("Compounds that can treat new diseases:")
                    for name in result:
                        print(f"- {name}")
                    
            elif choice == "3":
                print("Exit")
                break

            else:
                print("Invalid option. Please choose 1, 2, or 3")
    
    finally:
        client.close()
        
        

if __name__ == "__main__":
    main()