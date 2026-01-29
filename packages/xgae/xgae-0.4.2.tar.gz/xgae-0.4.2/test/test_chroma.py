import chromadb

chroma_client = chromadb.EphemeralClient()

# default use 'ONNXMiniLM_L6_V2' embedding function
collection = chroma_client.get_or_create_collection(name="fault_collection")

collection.upsert(
    documents=[
        "Fault location and analysis of fault causes",
        "This is a analyse about alarm"
    ],
    ids=["id1", "id2"],
    metadatas=[{"type": 1}, {"type": 2}]
)

querys = ["locate fault and solution",
          "alarm search"
          ]

for query in querys:
    results = collection.query(
        query_texts=query,
        n_results=2,
        #where={"type": 1},
        where={"type": {"$gt": 0}},
        where_document = {"$contains": "fault"}
    )
    print("*"*50)
    print(f"query='{query}', id={results['ids'][0]}, score={results['distances'][0]}")

