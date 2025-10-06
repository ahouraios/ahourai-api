import os
import certifi
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.json.ensure_ascii = False

# --- Database Connection ---
try:
    # Get the MongoDB URI from environment variables
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI not found in environment variables.")

    # Create a new client and connect to the server
    # Using tlsCAFile=certifi.where() to handle SSL/TLS certificate verification
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    db = client['ahourai_db'] # Database name
    print("✅ Successfully connected to MongoDB Atlas!")

except Exception as e:
    print(f"❌ Could not connect to MongoDB: {e}")
    db = None

# --- Helper Function for JSON serialization ---
def serialize_doc(doc):
    """Converts a MongoDB doc to a JSON-serializable format."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# --- API Routes ---
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Ahourai Project API!", "status": "running"}), 200

@app.route('/principles', methods=['POST'])
def add_principle():
    """Adds a new principle to the database."""
    # CORRECTED LINE: Changed 'if not db' to 'if db is None'
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available."}), 500
    
    try:
        data = request.get_json()
        # Basic validation
        if not data or 'title' not in data or 'description' not in data:
            return jsonify({"status": "error", "message": "Missing 'title' or 'description' in request body."}), 400

        principles_collection = db['principles']
        result = principles_collection.insert_one(data)
        
        return jsonify({
            "status": "success",
            "message": "Principle added successfully.",
            "inserted_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/principles', methods=['GET'])
def get_principles():
    """Retrieves all principles from the database."""
    # CORRECTED LINE: Changed 'if not db' to 'if db is None'
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available."}), 500
        
    try:
        principles_collection = db['principles']
        principles = list(principles_collection.find({}))
        
        # Serialize each document
        serialized_principles = [serialize_doc(p) for p in principles]

        return jsonify({
            "status": "success",
            "count": len(serialized_principles),
            "data": serialized_principles
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/principles/<string:principle_id>', methods=['GET'])
def get_principle_by_id(principle_id):
    """Retrieves a single principle by its ID."""
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available."}), 500
        
    try:
        principles_collection = db['principles']
        
        # Convert string ID to MongoDB's ObjectId
        # This is a critical step, otherwise find_one won't work
        try:
            obj_id = ObjectId(principle_id)
        except Exception:
            return jsonify({"status": "error", "message": "Invalid ID format."}), 400

        principle = principles_collection.find_one({"_id": obj_id})
        
        if principle:
            return jsonify({
                "status": "success",
                "data": serialize_doc(principle)
            }), 200
        else:
            return jsonify({"status": "error", "message": "Principle not found."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# To run the app
if __name__ == '__main__':
    app.run(debug=True)
