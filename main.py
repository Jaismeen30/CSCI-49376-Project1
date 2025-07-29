from neo4j import GraphDatabase
from pymongo import MongoClient


URI = "bolt://localhost:7687"     
USERNAME = "neo4j"
PASSWORD = "Jaismeen30"

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "Project1"


class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    def query_disease_info(self, disease_id):
        query = """
        MATCH (d:Disease {id: $disease_id})
        OPTIONAL MATCH (t:Compound)-[:CtD]->(d)
        OPTIONAL MATCH (p:Compound)-[:CpD]->(d)
        OPTIONAL MATCH (g:Gene)-[:DaG]->(d)
        OPTIONAL MATCH (d)-[:DlA]->(a:Anatomy)
        RETURN 
            d.name AS disease_name,
            collect(DISTINCT t.name) AS treats,
            collect(DISTINCT p.name) AS palliates,
            collect(DISTINCT g.name) AS genes,
            collect(DISTINCT a.name) AS locations
        """
        with self.driver.session() as session:
            result = session.run(query, {"disease_id": disease_id})
            return result.single()
        
def get_disease_info(disease_id, nodes_collection, edges_collection):
    disease_doc = nodes_collection.find_one({"_id": disease_id})
    if not disease_doc:
        return f"Disease '{disease_id}' not found."

    disease_name = disease_doc.get("name", "[Unnamed]")

    related_edges = list(edges_collection.find({
        "$or": [
            {"source": disease_id},
            {"target": disease_id}
        ]
    }))

    treats = set()
    palliates = set()
    genes = set()
    anatomy = set()

    for edge in related_edges:
        src = edge["source"]
        tgt = edge["target"]
        meta = edge["metaedge"]

        if meta == "CtD" and tgt == disease_id:
            drug = nodes_collection.find_one({"_id": src})
            if drug:
                treats.add(drug.get("name") or src)

        elif meta == "CpD" and tgt == disease_id:
            drug = nodes_collection.find_one({"_id": src})
            if drug:
                palliates.add(drug.get("name") or src)

        elif meta == "DaG" and tgt == disease_id:
            gene = nodes_collection.find_one({"_id": src})
            if gene:
                genes.add(gene.get("name") or src)
        elif meta == "DuG" and tgt == disease_id:
            gene = nodes_collection.find_one({"_id": src})
            if gene:
                genes.add(gene.get("name") or src)

        elif meta == "DlA" and src == disease_id:
            anat = nodes_collection.find_one({"_id": tgt})
            if anat:
                anatomy.add(anat.get("name") or tgt)

    return {
        "Disease ID": disease_id,
        "Name": disease_name,
        "Treats": sorted(treats),
        "Palliates": sorted(palliates),
        "Caused by Genes": sorted(genes),
        "Occurs in Anatomy": sorted(anatomy)
    }



def print_menu():
    print("\n")
    print("1. Run a Cypher query")
    print("2. Create sample nodes and relationships")
    print("3. Get Disease info mongodb")
    print("4. Get Disease info")
    print("5. Exit")

def main():
    
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["Project1"]
    nodes_collection = db["nodes"]
    edges_collection = db["edges"]
    client = Neo4jClient(URI, USERNAME, PASSWORD)
    for edge in edges_collection.find({"metaedge": "DuG", "target": "Disease::DOID:10763"}):
        print(edge)


    try:
        while True:
            print_menu()
            choice = input("Choose an option (1-5): ")

            if choice == "1":
                query = input("\nEnter your Cypher query:\n> ")
                results = client.run_query(query)
                print("\nResults:")
                for row in results:
                    print(row)

            elif choice == "2":
                sample_query = """
                CREATE (c:Compound {name: 'Aspirin'})-[:CtD]->(d:Disease {name: 'Headache'})
                """
                client.run_query(sample_query)
                print("Sample data created.")

            
            elif choice == "3":
                disease_id = input("Enter Disease ID (e.g., Disease::DOID:10763): ")
                result = get_disease_info(disease_id, nodes_collection, edges_collection)
                print("\n=== Disease Information (MongoDB) ===")
                if isinstance(result, dict):
                    for key, val in result.items():
                        print(f"{key}: {val}")
                else:
                    print(result)

            elif choice == "4":
                disease_id = input("Enter disease ID (e.g. Disease::DOID:10763): ")
                result = client.query_disease_info(disease_id)
                if result:
                    print("\nDisease Info:")
                    for key, value in result.items():
                        print(f"{key}: {value}")
                        
            elif choice == "5":
                print("Goodbye!")
                break

            else:
                print("Invalid option. Please choose 1, 2, 3, 4 or 5 ")
    
    finally:
        client.close()
        
        

if __name__ == "__main__":
    main()