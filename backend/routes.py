import json
import os
import sys

import pymongo
from bson import json_util
from bson.objectid import ObjectId
from flask import abort, jsonify, make_response, request, url_for  # noqa; F401
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult

from . import app

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route('/')
def index():
    return {"message": "Hello"}


@app.route('/health')
def health():
    return jsonify({"status":"Ok"}), 200

@app.route('/count')
def count():
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route('/song')
def songs():
    songs = db.songs.find({})
    songs = list(songs)  # Convert cursor to list


# Remove ObjectId (since it’s not JSON serializable)
    for song in songs:
        song["_id"] = str(song["_id"])  # Convert ObjectId to string

    if songs is not None:
        return jsonify(songs), 200
    else:
        return jsonify({"message": "songs not found"}), 404\
        
    


@app.route('/song/<int:id>', methods=["GET"])
def get_song_by_id(id):
    song = db.songs.find_one({"id":id})
    if song is not None:
        return jsonify(str(song)), 200
    else:
        return jsonify({"message": "song not found"}), 404


@app.route('/song', methods=["POST"])
def create_song():
    song_data = request.get_json()
    songs = db.songs.find({})
    for song in songs:
        if song_data['id'] == song['id']:
            return jsonify({"Message": "song with id {song['id']} already present"}), 302

    res = db.songs.insert_one(song_data)
    return jsonify({"inserted id": f"{res.inserted_id}"}), 201


@app.route('/song/<int:id>', methods=["PUT"])
def update_song(id):
    song_data = request.get_json()
    song = db.songs.find_one({"id": id})
    if song is not None:
        res = db.songs.update_one({"id" : id}, {"$set" : song_data})
        if res.modified_count != 0:
            song = db.songs.find_one({"id": id})
            return jsonify(str(song)), 200
        else:
            return jsonify({"message": "song found, but nothing updated"})

    return jsonify({"message": "song not found"}), 404


@app.route('/song/<int:id>', methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id":id})
    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    
    return jsonify({}), 204