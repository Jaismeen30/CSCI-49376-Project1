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