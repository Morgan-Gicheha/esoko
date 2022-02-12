from cmath import e
from flask import Flask, jsonify, render_template, request,make_response
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests,json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import false
from sqlalchemy.sql import func
from flask_cors import CORS
from mpesa import *
import requests


app = Flask(__name__)
alvapi_key = "demo"
scheduler = BackgroundScheduler(daemon=True)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///alphavantage.db"
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:1234@localhost:5432/alphavantage"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
cors = CORS(app, resources={r"*": {"origins": "*"}})

ngrokURL = 'https://f0f5-41-80-113-253.ngrok.io/'

class Forex(db.Model):
    __tablename__ = 'forex'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(80), nullable=False)
    data = db.Column(db.JSON, unique=True)
    created_date  = db.Column(db.DateTime, nullable=False, server_default=func.now())

# mpesa db
class Mpesadb(db.Model):
    __tablename__ = 'mpesadb'
    id = db.Column(db.Integer, primary_key=True)
    MerchantRequestID = db.Column(db.String(), nullable=False)
    CheckoutRequestID = db.Column(db.String(), nullable=False)
    ResponseCode = db.Column(db.Integer)
    ResultDesc = db.Column(db.String(), nullable=True)
    


@app.before_first_request
def create_tables():
    db.create_all()
    print("Tables created")

@app.route("/")
def index():
   return "This is a private API"

@app.route("/json/forex")
def forex_api():
    #Get from DB
    # print("data is")
    # data_json=Forex.query.all()
    # # print("data is", data_json)
    # import ast
    # res =json.dumps([ast.literal_eval(d.data) for d in data_json])
    # # res =json.dumps([print("d is",d.data) for d in data_json])
    # return res
    r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=' + alvapi_key)

        #Store the data received
    data = r.text

        # find out the type of the data
    # print(type(data))

        #Convert from string to a dictionary using json.loads()
    data_json = json.loads(data)

    return data_json
 
def request_scheduler():
    try:
        # Make a GET Request to Alphavantage
        r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=' + alvapi_key)

        #Store the data received
        data = r.text

        # find out the type of the data
        # print(type(data))

        #Convert from string to a dictionary using json.loads()
        data_json = json.loads(data)

        #Find out type of data
        # print("From scheduler:",type(data_json))

        data = Forex(symbol="IBM", data=json.loads(json.dumps(data_json)))
        db.session.add(data)
        db.session.commit()
    except Exception as e:
        # return("Error in scheduler:")
        pass
    

@app.route("/stkpush" , methods=['POST', 'GET'])
def stkpush():
    print('HEEEEEEEEY')
    apiData = request.get_json(force=True)
    # print(apiData['phoneNumber'])
    # print(apiData['amount'])
    phoneNumber = apiData['phoneNumber']
    accountNumber = '25747'
    amount = apiData['amount']

    

    headers = {'Authorization': 'Bearer %s ' %authenticator()}
    body = {    
            "BusinessShortCode":BusinessShortCode,    
            "Password": genPassword(),    
            "Timestamp":getTimeStamp(),    
            "TransactionType": "CustomerPayBillOnline",    
            "Amount": amount,    
            "PartyA":phoneNumber,    
            "PartyB":"174379",    
            "PhoneNumber":phoneNumber,    
            "CallBackURL":f'{ngrokURL}/stkpush/checker',    
            "AccountReference":accountNumber,    
            "TransactionDesc":"Test"
}
    url = base_url + 'mpesa/stkpush/v1/processrequest'
   
    
    stkPushResponse = requests.post(url=url, json=body, headers=headers)
    try:
        print('::::::::: THIS IS IN stkpush B4 HTTP REQ :::::::::')
        if stkPushResponse.status_code == 200:
                print(f'::::::::: THIS IS IN stkpush AFTER HTTP REQ :::{stkPushResponse}::::::')
                MerchantRequestID = stkPushResponse.json()['MerchantRequestID']
                CheckoutRequestID = stkPushResponse.json()['CheckoutRequestID']
                ResponseCode = stkPushResponse.json()['ResponseCode']
                
                # 1. store the response in the database, i.e. the merchant request and the checkout request (make a new model for these)
                mpesadata = Mpesadb(MerchantRequestID = MerchantRequestID,CheckoutRequestID = CheckoutRequestID, ResponseCode =ResponseCode )
                db.session.add(mpesadata)
                db.session.commit()
                print('data has been saved in db')

    except Exception as e:
        print(f'error is {e}')
  
    return stkPushResponse.json()

@app.route("/stkpush/checker", methods=['GET', 'POST'])
def stk_push_checker():  
    
    # 2. Change the status code received in step 1
    print('::::::::: IN STKPUSH CHECKER :::::::::r')
    apiData = request.get_json(force=True)

    print(f'::::::::: THIS IS MY CHECKER RESPONSE :::::::::{apiData}')

    queriedRecord = Mpesadb.query.filter_by(CheckoutRequestID = apiData['Body']['stkCallback']['CheckoutRequestID'], MerchantRequestID = apiData['Body']['stkCallback']['MerchantRequestID']).first()

    # print(queriedRecord)
    queriedRecord.ResponseCode = apiData['Body']['stkCallback']['ResultCode']
    queriedRecord.ResultDesc = apiData['Body']['stkCallback']['ResultDesc']
    db.session.add(queriedRecord)
    db.session.commit()

    return queriedRecord

# for safaricom
@app.route("/stkpush/processor", methods=['GET', 'POST'])
def stk_push_processor():
    # 3. Check what the user has done. The client shall do a loop every 5 seconds with the checkout request and the merchant request.
    print(':::::::::  ENTERING PROCESSOR :::::::::')
    apiData = request.get_json(force=True)
    processorQueriedRecord = Mpesadb.query.filter_by(CheckoutRequestID = apiData['CheckoutRequestID'], MerchantRequestID = apiData['MerchantRequestID']).first()
    print('processor',processorQueriedRecord.ResultDesc)


    if processorQueriedRecord:
        # resp = make_resonse(jsonify(dict({'':processorQueriedRecord.mid, '':processorQueriedRecord.cr, })),200()
        resp =  jsonify(dict({'MerchantRequestID':processorQueriedRecord.MerchantRequestID, 'ResultDesc':processorQueriedRecord.ResultDesc}))
        x = make_response(resp,200)
        return x
       
    else:
        return {'error':'error'}
    

def request_scheduler():
    # try:
    #     # Make a GET Request to Alphavantage
    #     r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=' + alvapi_key)

    #     # Store the data received
    #     data = r.text

    #     # find out the type of the data
    #     print(type(data))

    #     # Convert from string to a dictionary using json.loads()
    #     data_json = json.loads(data)

    #     # Find out type of data
    #     print("From scheduler:", type(data_json))

    #     data = Forex(symbol="IBM", data=json.loads(json.dumps(data_json)))
    #     db.session.add(data)
    #     db.session.commit()
    # # except Exception as e:
    #     print("Error in scheduler:", e)
    return "hi"

# Create the scheduler job
scheduler.add_job(request_scheduler, 'interval', minutes=0.25)

# start the scheduler
scheduler.start()

  

if __name__ == "__main__":
    app.run()
