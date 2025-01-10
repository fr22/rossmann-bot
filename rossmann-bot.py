import requests
import json
import pandas as pd
from flask import Flask, request, Response
import os

#constants
TOKEN = '7406870034:AAEmY5GXMjT96_HltqlR8qwdAV_46cnpeCI'

#"chat" "id":5129065700

# info about the bot
#https://api.telegram.org/bot7406870034:AAEmY5GXMjT96_HltqlR8qwdAV_46cnpeCI/getMe

#get Updates

#https://api.telegram.org/bot7406870034:AAEmY5GXMjT96_HltqlR8qwdAV_46cnpeCI/getUpdates

#set Webhook
#https://api.telegram.org/bot7406870034:AAEmY5GXMjT96_HltqlR8qwdAV_46cnpeCI/setWebhook?url=https://81b96506a13724.lhr.life/

#send messages

#https://api.telegram.org/bot7406870034:AAEmY5GXMjT96_HltqlR8qwdAV_46cnpeCI/sendMessage?#chat_id=5129065700&text=Hi Francisco! I am doing good, tks.

def send_message(chat_id, text):
    #url =  'https://api.telegram.org/bot{}'.format(TOKEN)
    #url = url + 'sendMessage?chat_id={}'.format(chat_id)
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
    r = requests.post(url)
    print('Status Code {}'.format(r.status_code))

    return None
    


def load_dataset(store_id):
    
    #loading test dataset
    df10 = pd.read_csv('test.csv')
    #loading store dataset
    df_store_raw = pd.read_csv('store.csv')
    # merge test dataset + store
    df_test = pd.merge(df10, df_store_raw, how = 'left', on = 'Store')
    # choose store for prediction
    df_test = df_test[df_test[
        'Store'].isin( [store_id])]
    if not df_test.empty:
    
        #remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis = 1)
        # convert dataframe to json
        data = json.dumps(df_test.to_dict(orient = 'records'))
    else:
        data = 'error'

    return data
def predict(data):
    
    # API call
    #url = 'http://0.0.0.0:5000/rossmann/predict'
    #url = 'http://127.0.0.1:10000/rossmann/predict'
    url = 'https://rossmann-api-render.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data
    
    r = requests.post(url, data = data, headers = header)
    print('Status Code {}'.format(r.status_code))
    d1 = pd.DataFrame(r.json(), columns = r.json()[0].keys())

    return d1



# API initialize
def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    store_id = store_id.replace('/', '')

    try:
        store_id = int(store_id)
    except ValueError:
        
        store_id = 'error'
    
    return chat_id, store_id

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])

def index():
    
    if request.method == 'POST':
        
        message = request.get_json()
        chat_id, store_id = parse_message(message)
        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)
            if data != 'error':
                
                #prediction
                d1 = predict(data)
                #calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
                
                #send message
                msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks.'.format(
                            (d2[ 'store'].values[0]),
                            (d2[ 'prediction'].values[0])
                    )
                print(msg)
                send_message(chat_id, msg)
                return Response('Ok', status = 200) 
        
                
        else:
            send_message(chat_id, 'Store ID is Wrong')
            return Response('Ok', status = 200)
    else:
        return '<h1>Rossmann Telegram Bot</h1>'
    

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host = '0.0.0.0', port = port)
    