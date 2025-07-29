from neo4j import GraphDatabase


URI = "bolt://localhost:7687"     
USERNAME = "neo4j"
PASSWORD = "Jaismeen30"


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

def print_menu():
    print("\n--- Neo4j CLI ---")
    print("1. Run a custom Cypher query")
    print("2. Create sample nodes and relationships")
    print("3. Run built-in Disease ID query")
    print("4. Exit")

def main():
    client = Neo4jClient(URI, USERNAME, PASSWORD)

    try:
        while True:
            print_menu()
            choice = input("Choose an option (1-3): ")

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
                disease_id = input("Enter disease ID (e.g. Disease::DOID:10763): ")
                result = client.query_disease_info(disease_id)
                if result:
                    print("\nDisease Info:")
                    for key, value in result.items():
                        print(f"{key}: {value}")
                else:
                    print("No results found.")

            elif choice == "4":
                print("Goodbye!")
                break

            else:
                print("Invalid option. Please choose 1, 2, or 3.")
    
    finally:
        client.close()
        
        

if __name__ == "__main__":
    main()