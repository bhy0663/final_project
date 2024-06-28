import requests, pandas, json, os, ast
from sqlalchemy import create_engine, Table, MetaData, func, select
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import select
from datetime import datetime

app = Flask(__name__)

db = SQLAlchemy()

data_Array = []

delay_table_count = 0

updatetime = ''

engine = create_engine('mssql+pyodbc://(local)/TRA?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server')

app_id = '111316132-0520f44a-8935-4397'
app_key ='fffa8c6c-3491-4bf9-959f-0893c99d940c'

auth_url="https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
url = "https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/LiveTrainDelay?$format=JSON"

class Auth():

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_header(self):
        content_type = 'application/x-www-form-urlencoded'
        grant_type = 'client_credentials'

        return{
            'content-type' : content_type,
            'grant_type' : grant_type,
            'client_id' : self.app_id,
            'client_secret' : self.app_key
        }

class data():

    def __init__(self, app_id, app_key, auth_response):
        self.app_id = app_id
        self.app_key = app_key
        self.auth_response = auth_response

    def get_data_header(self):
        auth_JSON = json.loads(self.auth_response.text)
        access_token = auth_JSON.get('access_token')

        return{
            'authorization': 'Bearer ' + access_token,
            'Accept-Encoding': 'gzip'
        }

def get_table_row_count(engine, table_name):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    table = Table(table_name, metadata, autoload_with=engine)
    
    query = select(func.count()).select_from(table)
    
    with engine.connect() as connection:
        result = connection.execute(query)
        count = result.scalar()
    return count

def startt():
    
    global data_Array 
    global delay_table_count
    global updatetime 
    
    try:
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    except:
        a = Auth(app_id, app_key)
        auth_response = requests.post(auth_url, a.get_auth_header())
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    
    dataget = json.loads(data_response.text)

    df = pandas.DataFrame(dataget)

    if(os.path.exists('test001.csv')):os.remove('test001.csv')

    df.to_csv('test001.csv' , index = 'false' , encoding = 'utf-8-sig')

    dfr = pandas.read_csv('test001.csv')

    dfr.to_sql('DelayTable',con=engine,if_exists='replace',index=False)

    querty_delay = 'SELECT * FROM DelayTable'

    df_Delay_read = pandas.read_sql(querty_delay,con=engine)

    delay_table_count = get_table_row_count(engine, 'DelayTable')


    data_Array = [[0 for _ in range(3)] for _ in range(delay_table_count)]

    for i in range(delay_table_count):
        data_Array[i][0] = int(df_Delay_read['TrainNo'][i])

        stationname = json.dumps(df_Delay_read['StationName'][i])
        stationname = json.loads(stationname)
        stationname = ast.literal_eval(stationname)['Zh_tw']

        data_Array[i][1] = stationname
        data_Array[i][2] = int(df_Delay_read['DelayTime'][i])

    updatetime = df_Delay_read['UpdateTime'][0]

    updatetime = datetime.strptime(updatetime, '%Y-%m-%dT%H:%M:%S%z')
    
    print(updatetime)


if __name__ == '__main__':
    try:
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    except:
        a = Auth(app_id, app_key)
        auth_response = requests.post(auth_url, a.get_auth_header())
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    
    dataget = json.loads(data_response.text)
    df = pandas.DataFrame(dataget)

    if(os.path.exists('test001.csv')):os.remove('test001.csv')
    
    df.to_csv('test001.csv' , index = 'false' , encoding = 'utf-8-sig')
    
    dfr = pandas.read_csv('test001.csv')
    
    dfr.to_sql('DelayTable',con=engine,if_exists='replace',index=False)

    querty_delay = 'SELECT * FROM DelayTable'

    df_Delay_read = pandas.read_sql(querty_delay,con=engine)

    delay_table_count = get_table_row_count(engine, 'DelayTable')

    TrainNo_array = []
    Delay_time_array = []

    data_Array = [[0 for _ in range(3)] for _ in range(delay_table_count)]

    for i in range(delay_table_count):
        data_Array[i][0] = int(df_Delay_read['TrainNo'][i])

        stationname = json.dumps(df_Delay_read['StationName'][i])
        stationname = json.loads(stationname)
        stationname = ast.literal_eval(stationname)['Zh_tw']

        data_Array[i][1] = stationname
        data_Array[i][2] = int(df_Delay_read['DelayTime'][i])

    updatetime = df_Delay_read['UpdateTime'][0]

    updatetime = datetime.strptime(updatetime, '%Y-%m-%dT%H:%M:%S%z')

    @app.route('/')
    def index():        
        return render_template('main.html',data_Array = data_Array,count = json.dumps(delay_table_count),updatetime = updatetime)
    
    @app.route('/restart')
    def restart():
        startt()
        
        print(updatetime)
        return redirect(url_for('index'))

    app.run()