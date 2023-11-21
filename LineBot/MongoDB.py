'''
Copyright (c) 2023 Jacky Hou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from gridfs import GridFS
import pymongo
import Tools

db_client = None


def Login_db():
    global db_client
    login_string = f"mongodb://{Tools.MONGODB_USER}:{Tools.MONGODB_PWD}@{Tools.MONGODB_URL}"
    db_client = pymongo.MongoClient(login_string)
    return


def Load_db(db_name, collection_name):
    global db_client
    if db_client:
        db = db_client[db_name]
        collection = db[collection_name]
        return collection
    return None


def Load_dbs(db_name):
    global db_client
    if db_client:
        db = db_client[db_name]
        collection_objects = [db[collection_name]
                              for collection_name in db.list_collection_names()]
        return collection_objects
    return None


def Drop_db(db_name, collection_name):
    global db_client
    if db_client:
        db = db_client[db_name]
        db.drop_collection(collection_name)
    return


def Query_db(collection, tagname, value):
    document = collection.find_one({tagname: value})
    return document


def Insert_db(collection, struct):
    document = collection.insert_one(struct)
    return document


def Update_db(collection, filter, update):
    update_result = collection.update_one(filter, update)
    return update_result


def Delete_db(collection, filter):
    update_result = collection.delete_one(filter)
    return update_result


def Load_GridFS_db(db_name):
    global db_client
    if db_client:
        db = db_client[db_name]
        fs = GridFS(db)
        return fs
    return None


Login_db()
