"""Vector search example for KeraDB Python SDK."""

import math
import random
import keradb


def generate_random_embedding(dimensions: int) -> keradb.Embedding:
    """Create a random normalized vector."""
    embedding = [random.random() * 2 - 1 for _ in range(dimensions)]
    
    # Normalize the vector
    sum_squares = sum(x * x for x in embedding)
    norm = math.sqrt(sum_squares)
    embedding = [x / norm for x in embedding]
    
    return embedding


def add_noise(embedding: keradb.Embedding, noise_level: float) -> keradb.Embedding:
    """Add small random perturbations to create similar vectors."""
    result = [x + (random.random() * 2 - 1) * noise_level for x in embedding]
    
    # Re-normalize
    sum_squares = sum(x * x for x in result)
    norm = math.sqrt(sum_squares)
    result = [x / norm for x in result]
    
    return result


def main():
    print("=== KeraDB Vector Search Example ===\n")
    
    # 1. Connect to database
    print("1. Connecting to database...")
    client = keradb.connect("vector_demo.ndb")
    print("   ✓ Connected\n")
    
    # 2. Create a vector collection
    print("2. Creating vector collection...")
    dimensions = 128
    config = keradb.VectorConfig(
        dimensions=dimensions,
        distance=keradb.Distance.COSINE,
        m=16,
        ef_construction=200,
        ef_search=50,
    ).with_delta_compression()
    
    try:
        client.create_vector_collection("articles", config)
        print("   ✓ Collection created with delta compression")
    except Exception as e:
        print(f"   Note: {e}")
    print()
    
    # 3. Insert sample vectors with metadata
    print("3. Inserting sample article vectors...")
    
    articles = [
        {"title": "Introduction to Machine Learning", "category": "tech"},
        {"title": "Advanced Neural Networks", "category": "tech"},
        {"title": "Deep Learning Fundamentals", "category": "tech"},
        {"title": "Cooking Italian Pasta", "category": "food"},
        {"title": "Mediterranean Diet Guide", "category": "food"},
        {"title": "Travel Guide to Tokyo", "category": "travel"},
        {"title": "European Travel Tips", "category": "travel"},
        {"title": "AI Ethics and Society", "category": "tech"},
    ]
    
    # Generate base vectors for each category
    category_vectors = {
        "tech": generate_random_embedding(dimensions),
        "food": generate_random_embedding(dimensions),
        "travel": generate_random_embedding(dimensions),
    }
    
    inserted_ids = []
    for article in articles:
        # Create similar vectors within each category
        base_vec = category_vectors[article["category"]]
        vec = add_noise(base_vec, 0.1)
        
        vector_id = client.insert_vector("articles", vec, article)
        inserted_ids.append(vector_id)
        print(f"   ✓ Inserted: {article['title']} (ID: {vector_id})")
    
    print(f"\n   Inserted {len(inserted_ids)} vectors\n")
    
    # 4. Vector similarity search
    print("4. Performing vector similarity search...")
    tech_query = add_noise(category_vectors["tech"], 0.05)
    results = client.vector_search("articles", tech_query, k=3)
    
    print("\n   Top 3 tech-related results:")
    for result in results:
        print(f"   [{result.rank}] {result.document.metadata['title']}")
        print(f"       Category: {result.document.metadata['category']}")
        print(f"       Score: {result.score:.4f}")
    print()
    
    # 5. Search with different query
    print("5. Searching for food-related content...")
    food_query = add_noise(category_vectors["food"], 0.05)
    results = client.vector_search("articles", food_query, k=3)
    
    print("\n   Top 3 food-related results:")
    for result in results:
        print(f"   [{result.rank}] {result.document.metadata['title']}")
        print(f"       Category: {result.document.metadata['category']}")
        print(f"       Score: {result.score:.4f}")
    print()
    
    # 6. Get vector by ID
    print("6. Retrieving vector by ID...")
    doc = client.get_vector("articles", inserted_ids[0])
    if doc:
        print(f"   ✓ Retrieved: {doc.metadata['title']}")
        print(f"      ID: {doc.id}")
        print(f"      Embedding dimensions: {len(doc.embedding) if doc.embedding else 'N/A'}")
    print()
    
    # 7. Collection statistics
    print("7. Getting collection statistics...")
    stats = client.vector_stats("articles")
    print(f"   Vectors: {stats.vector_count}")
    print(f"   Dimensions: {stats.dimensions}")
    print(f"   Distance metric: {stats.distance.value}")
    print(f"   Memory usage: {stats.memory_usage:,} bytes ({stats.memory_usage / 1024:.2f} KB)")
    print(f"   HNSW layers: {stats.layer_count}")
    if stats.compression:
        print(f"   Compression: {stats.compression.value}")
        if stats.anchor_count:
            print(f"   Anchor vectors: {stats.anchor_count}")
        if stats.delta_count:
            print(f"   Delta vectors: {stats.delta_count}")
    print()
    
    # 8. List vector collections
    print("8. Listing vector collections...")
    collections = client.list_vector_collections()
    for coll in collections:
        print(f"   {coll['name']}: {coll['count']} vectors")
    print()
    
    # 9. Delete a vector
    print("9. Deleting a vector...")
    deleted = client.delete_vector("articles", inserted_ids[-1])
    if deleted:
        print(f"   ✓ Deleted vector {inserted_ids[-1]}")
        
    # Check updated count
    stats = client.vector_stats("articles")
    print(f"   Remaining vectors: {stats.vector_count}\n")
    
    # Close connection
    client.close()
    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
