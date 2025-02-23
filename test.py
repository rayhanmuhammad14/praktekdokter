from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Koneksi ke MongoDB
client = MongoClient("mongodb+srv://rayhan123:m5VnblcoXTtzOhUh@kartustok.lq6vs.mongodb.net/?retryWrites=true&w=majority&appName=kartuStok")
db = client['kartuStok']
collection = db['kartustok']

@app.route("/", methods=["GET"])
def test_connection():
    try:
        db.command("ping")  # Tes koneksi ke database
        return jsonify({"message": "✅ Koneksi ke MongoDB berhasil!"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
