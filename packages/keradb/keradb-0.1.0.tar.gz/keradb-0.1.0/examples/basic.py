"""Basic usage example for KeraDB Python SDK."""

import keradb


def main():
    # Connect to database (MongoDB-compatible API)
    print("Connecting to database...")
    client = keradb.connect("example.ndb")
    
    # Get database and collection
    db = client.database()
    users = db.collection("users")
    
    # Insert documents
    print("\n--- Inserting documents ---")
    result1 = users.insert_one({
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com"
    })
    print(f"Inserted Alice with ID: {result1.inserted_id}")
    
    result2 = users.insert_one({
        "name": "Bob",
        "age": 25,
        "email": "bob@example.com"
    })
    print(f"Inserted Bob with ID: {result2.inserted_id}")
    
    # Find by ID
    print("\n--- Finding by ID ---")
    alice = users.find_one({"_id": result1.inserted_id})
    print(f"Found Alice: {alice}")
    
    # Update
    print("\n--- Updating ---")
    update_result = users.update_one(
        {"_id": result1.inserted_id},
        {"$set": {"age": 31}}
    )
    print(f"Updated {update_result.modified_count} document(s)")
    
    # Find all
    print("\n--- Finding all ---")
    all_users = users.find().all()
    print(f"All users: {all_users}")
    
    # Count
    print("\n--- Counting ---")
    count = users.count_documents({})
    print(f"Total users: {count}")
    
    # List collections
    print("\n--- Listing collections ---")
    collections = db.list_collection_names()
    for name in collections:
        print(f"Collection: {name}")
    
    # Pagination
    print("\n--- Pagination ---")
    page1 = users.find().limit(1).skip(0).all()
    print(f"Page 1: {page1}")
    
    page2 = users.find().limit(1).skip(1).all()
    print(f"Page 2: {page2}")
    
    # Filtering
    print("\n--- Filtering ---")
    adults = users.find({"age": {"$gte": 30}}).all()
    print(f"Adults (age >= 30): {adults}")
    
    # Delete
    print("\n--- Deleting ---")
    delete_result = users.delete_one({"_id": result2.inserted_id})
    print(f"Deleted {delete_result.deleted_count} document(s)")
    
    # Final count
    final_count = users.count_documents({})
    print(f"\nFinal user count: {final_count}")
    
    # Close connection
    client.close()
    print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
