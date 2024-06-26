from flask import Flask, jsonify , request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB

users = db["Users"]

def UserExist(username):
    if users.count_documents({"Username":username}) == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status":301,
                "msg": "Invalid Username"

            }
            return jsonify(retJson)
    
        hashed_pw = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Tokens":6
        })
        

        retJson = {
            "status":200,
            "msg":"Successfully signed for the api"
        }
        return jsonify(retJson)

def verifyPw(username, password):
    if not UserExist(username):
        return False
    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw)==hashed_pw:
        return True
    else:
        return False
    
def countTokens(username):
    tokens = users.find({
        "Username":username

    })[0]["Tokens"]
    return tokens
class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username  = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson = {
                "status": "301",
                "msg": "Invalid Username"
            }
            return jsonify(retJson)
        
        correct_pw = verifyPw(username, password)

        if not correct_pw:
            retJson = {
                "satus": 302,
                "msg": "Invalid Password"
            }
        
        num_tokens = countTokens(username)

        if num_tokens <= 0:
            retJson= {
                "Status": 303,
                "msg": "You're out of tokens, Please refill!"

            }
            return jsonify(retJson)
        
        #claculating the edit distance
        
        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

#ratio is the number between 0 and 1 the closer to 1, the more similar text 1 and text 2 are
        ratio = text1.similarity(text2)

        retJson = {
            "status":200,
            "similarity": ratio,
            "msg": "Similarity score calculated successfully"
        }
        current_tokens = countTokens(username)

        users.update_one({
            "Username": username,

        },{
            "$set":{
                "Tokens":current_tokens-1
            }
        })
        return jsonify(retJson)
    
class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status":301,
                "msg": "Ivalid Username"
            }
            return jsonify(retJson)
        
        correct_pw = " abc123"

        if not password == correct_pw:
            retJson = {
                "status": 304,
                "msg": "Invalid Admin Pssword"
            }
            return jsonify(retJson)
        
        
        users.update_one({
            "Username": username
        },{
            "$set":{
                "Tokens":refill_amount
            }
        })

        retJson = {
            "status":200,
            "msg":"Refilled Successfully"
        }
        return jsonify(retJson)
    

api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__=="__main__":
    app.run(host='0.0.0.0')

