### FLOW 
# create project ---> upload document ---> query


### APIs to writes

## 1. create project under the user
#     params - user_id
#     returns projects_id

## 2. file upload api to be modified to add provision to add any document to a project
#     params - user_id, project_id, doc file
#     returns document_id

## 3. 
# 
# 
#  

import json
import pandas as pd
import os
import requests
import time
import uuid
from werkzeug.utils import secure_filename

from information_retriever import InformationRetriever

#from pymongo import MongoClient
#client = MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass%20Community&ssl=false")
#db = client['legal_search']
#user_collections = db['users']

from flask import Flask, request, Response, render_template
from flask_cors import CORS

#from flask_ngrok import run_with_ngrok

app = Flask(__name__)
#CORS(app)
#run_with_ngrok(app)

ir = InformationRetriever()

user_collection = {}
user_collection['users'] = ['123', '456']                    #list of users registered

projects = []

#user_collection['users']['documents'] = []                  #list of documents under the user
#user_collection['users']['document_names'] = []

temp_docs = []


@app.route("/")
def home():
   return "SEMANTIC SEARCH API"


@app.route("/create_project", methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':

        if 'user_id' in request.args:
            user_id = str(request.args['user_id'])
        else:
            return Response(response=({'error' : "No user_id provided"}), 
                        status=401, mimetype="application/json")
        
        one_project = {}
        new_project_id = str(uuid.uuid4())
        one_project['project_id'] = new_project_id
        one_project['deleted_by_user'] = False
        one_project['documents'] = []
        projects.append(one_project)
        
        return Response(response=json.dumps({'project_id':(new_project_id)}), 
                            status=200, mimetype="application/json")


@app.route("/delete_project", methods=['GET','POST'])
def delete_project():
    if request.method == 'POST':

        if 'user_id' in request.args:
            user_id = str(request.args['user_id'])
        else:
            return Response(response=({'error' : "No user_id provided"}), 
                        status=401, mimetype="application/json")
        
        if 'project_id' in request.args:
            project_id = str(request.args['project_id'])
        else:
            return Response(response=({'error' : "No project_id provided"}), 
                        status=401, mimetype="application/json")
        
        print("-------------------------- before deleting")
        print(projects)
        for i in projects:
            if i['project_id'] == str(project_id):
                i['deleted_by_user'] = True
        print("-------------------------- after deleting")
        print(projects)
        
        return Response(response=json.dumps({'message':f"Deleted project :: {project_id} "}))


@app.route('/file_upload', methods=['GET', 'POST'])
def file_upload():
    if request.method == 'POST':

        if 'user_id' in request.args:
            user_id = str(request.args.get('user_id'))

            if user_id in user_collection['users']:

                if 'project_id' in request.args:
                    project_id = str(request.args['project_id'])
                    single_doc = {}
                    f = request.files['file']
                    f.save(secure_filename(f.filename))
                    
                    document_id = str(uuid.uuid4())
                    print("Document id :: ", document_id)
                    
                    single_doc = {}
                    single_doc['document_id'] = document_id
                    single_doc['document_name'] = f.filename
                    temp_docs.append(single_doc)

                    for i in projects:
                        if i['project_id'] == project_id:
                            if len(i['documents']) == 5:
                                return Response(response=({'error' : "You can only index 5 documents in a project"}), 
                                            status=401, mimetype="application/json")
                            i['documents'].append(single_doc) 

                    ## Extracting from pdf
                    doc = ir.extract_from_pdf(single_doc['document_name'])
                    docs = ir.preprocess(doc)
                    print("Number of docs added to document store from uploaded pdf :: ", len(docs))
                    
                    index_metadata = {'document_name':single_doc['document_name'], 'user_id':user_id, 'project_id':project_id, 'document_id':document_id}
                    useDense = False
                    ir.index(docs, index_metadata, useDense)
                    
                    print("Document store document count :: ", ir.document_store.get_document_count())
                    print(" :::: Completed Indexing :::: ")
                    #user_collection['users'][user_id]['documents'].append(document_id)
                    #user_collection['users'][user_id]['documents'][document_id]['filename'] = doc_name
                    
                    return Response(response=json.dumps({'document_id':str(document_id)}), 
                            status=200, mimetype="application/json")
                
                else:
                    ##create a new project
                    return Response(response=({'error' : "No project_id exists"}), 
                            status=401, mimetype="application/json")


            else:
                return Response(response=({'error' : "No user_id exists"}), 
                            status=401, mimetype="application/json")
        
        else:
            return Response(response=({'error':'No user_id exists'}), 
                            status=200, mimetype="application/json")
        

@app.route("/text/query", methods=["POST"])
def query():
    #document_id = document_id
    k_retrievers = 10

    if request.method == "POST":

        if 'user_id' in request.args:
            user_id = str(request.args['user_id'])
        else:
            return Response(response=json.dumps("Error: No user id provided."), 
                    status=401, mimetype="application/json")
        
        if user_id in user_collection['users']:
            user_id = user_id
        else:
            return Response(response=json.dumps("No such user_id exists, Please make sure the user_id provided is correct."), 
                    status=401, mimetype="application/json")

        if 'project_id' in request.args:
            project_id = str(request.args['project_id'])
        else:
            return Response(response=json.dumps("Error: No project id provided."), 
                    status=401, mimetype="application/json")

        if 'document_id' in request.args:#user_collection[user_id]['documents']:
            document_id = str(request.args['document_id'])
        else:
            document_id = ""
        #else:
        #    return Response(response=json.dumps(f"Error: Error: No such document_id exists for {document_id}, Please make sure the document_id provided is correct."), 
        #            status=401, mimetype="application/json")

        if 'query' in request.args:
            print(":: query ::", request.args['query'])
            query = request.args['query']
        else:
            return Response(response=json.dumps("Error: No document provided."),
                status=401, mimetype="application/json")
        
        if 'top_k' in request.args:
            k_retrievers = request.args['top_k']
        
        filters = {'project_id': project_id, 'document_id':document_id}
        print(" :::: Retrieving :::: ")
        
        useDense = False
        out = ir.retrieve(query, k_retrievers, useDense)#, filters)

        return Response(response=json.dumps(out), 
                    status=200, mimetype="application/json")


@app.route("/delete_all", methods=['POST'])
def delete():
    if request.method == 'POST':
        ir.delete_all()
        count = ir.get_doc_count()
        print(ir.get_doc_count())
        
        return Response(response=json.dumps({'message':"deleted all documents", 'document_count':count}))


if __name__ == "__main__":
    app.run()


















'''@app.route("/text/index", methods=["POST"])
## api to index documents for a specific user_id.
#  expects user_id in the url(dynamic url), document name as parameter
def index():

    if request.method == "POST":
        
        if 'user_id' in request.args:
            user_id = request.args['user_id']
        else:
            return Response(response=json.dumps("Error: No user id provided."), 
                    status=401, mimetype="application/json")

        ## checking if user already exists
        if user_id in user_collection['users']:
            #if 'document_id' in request.args:  
            document_id = str(request.args.get('document_id'))
            #else:
            ##    return Response(response=json.dumps("Error: No document provided."), 
            #        status=401, mimetype="application/json")

            #try:
                ##convert pdf to dicts format with metadata-user_id and document_id
                #doc_name = user_collection['users']['documents'][document_id]['filename']
            for i in range(len(temp_docs)):
                if document_id == temp_docs[i]['document_id']:
                    doc_name = temp_docs[i]['document_name']
                    doc = ir.extract_from_pdf(doc_name)
                    print("type(doc):: ", type(doc))
                    print(doc)
                    docs = ir.preprocess(doc)
                    ir.index(user_id, document_id, doc_name, docs)
                    print("document store document count :: ")
                    print(ir.document_store.get_document_count())
                    print("completed indexing")

                    out = {}
                    out['documentId'] = document_id
                    return Response(response=json.dumps(out), 
                            status=200, mimetype="application/json")
                else:
                    return Response(response=json.dumps("No document id found"), 
                            status=401, mimetype="application/json")
            
            #except:
            #    return Response(response=json.dumps("Error: Indexing not complete, please try sending the request once again"), 
            #        status=401, mimetype="application/json")  
        
        else:
            ## creating a new user_id and an index in elasticsearch
            new_user_id = uuid.uuid4()
            #user_collection['users'].append(new_user_id)
            ir.create_el_index(new_user_id)

            return Response(response=json.dumps("New user created with user_id, ", new_user_id), 
                status=200, mimetype="application/json")'''