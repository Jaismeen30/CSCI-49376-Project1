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
        MATCH (t:Compound)-[:CtD]->(d)
        MATCH (p:Compound)-[:CpD]->(d)
        OPTIONAL MATCH (d)-[:DaG|DuG|DdG]->(g:Gene)
        MATCH (d)-[:DlA]->(a:Anatomy)
        RETURN 
            d.name AS Disease_name,
            collect(DISTINCT t.name) AS Treats,
            collect(DISTINCT p.name) AS Palliates,
            collect(DISTINCT g.name) AS Genes,
            collect(DISTINCT a.name) AS Locations
        """
        with self.driver.session() as session:
            result = session.run(query, {"disease_id": disease_id})
            return result.single()
           
        
    def find_compounds(self):
            query = """
            MATCH (case1:Compound)-[:CuG]->(g:Gene)<-[:AdG]-(a1:Anatomy)<-[:DlA]-(d:Disease)
            WHERE NOT ( (case1)-[:CtD]->(d) OR (case1)-[:CpD]->(d) )
            
            MATCH (case2:Compound)-[:CdG]->(g:Gene)<-[:AuG]-(a2:Anatomy)<-[:DlA]-(d)
            WHERE NOT ( (case2)-[:CtD]->(d) OR (case2)-[:CpD]->(d) )
            
            RETURN DISTINCT collect(DISTINCT case1.name) + collect(DISTINCT case2.name) AS Compounds
            """
            with self.driver.session() as session:
                result = session.run(query)
                return  result.single()
                #return record["Compounds"] if record else []

        




def print_menu():
    print("\n")
    print("1. Get Disease info")
    print("2. Compounds that can treat a new disease ")
    print("3. Exit")

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
            choice = input("Choose an option (1-3): ")

            if choice == "1":
                disease_id = input("Enter disease ID (e.g. Disease::DOID:10763): ")
                result = client.query_disease_info(disease_id)
                if result:
                    print("\nDisease Info:")
                    for key, value in result.items():
                        print(f"{key}: {value}")
            elif choice == "2":
                #print("Compounds:")
                result = client.find_compounds()
                if result:
                    print(result)
            
            
            elif choice == "3":
                print("Exit")
                break

            else:
                print("Invalid option. Please choose 1, 2, or 3")
    
    finally:
        client.close()
        
        

if __name__ == "__main__":
    main()