###########################################################################
###########################################################################
# Author: Yaron Khazai 2021
# Version: 20210625.1
###########################################################################
###########################################################################
import packages.requests as requests 
import json
from datetime import datetime
import time
import packages.yaml as yaml
from pprint import pprint

config=[]

def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

def get_machine_offset():
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    return offset / 60 / 60 * -1

def log(message,level = 5):
    global config
    if level<config['general']['logLevel']:
        pprint ("%s : %s"%( datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),message))

def lambda_handler(event, context):
    global config
    config = read_yaml('./config/config.yaml')
    log("config was loaded: %s "%(config),9)
    processed_date = datetime.today().strftime('%Y-%m-%d')
   
    s = requests.Session()
    s.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'})
    login_data = {'username': config["glucologweb"]['username'], 'password': config["glucologweb"]['password'], "timeZoneOffset": config["glucologweb"]["timeZoneOffset"]}
    glucologwebLoginURL=config["glucologweb"]["loginURL"]
    log("trying to call %s with %s data"%(glucologwebLoginURL,json.dumps(login_data)),9)
    res=s.post(glucologwebLoginURL, login_data,headers={'Referer': 'https://www.glucologweb.com/login?lang=en'})
    if (res.status_code != 200 or res.url=='https://www.glucologweb.com/login-error') :
        log ("cannot Login got status code : " + str(res.status_code),1)
        log ("redirected to : " + res.url,1)
        return
    glucologwebDataURL=config["glucologweb"]["dataURL"] + processed_date + '/false'
    r2 = s.get(glucologwebDataURL,headers={'Referer': 'https://www.glucologweb.com/home'})
    if (r2.status_code != 200):
        log ("cannot retrive data got status code : " + str(r2.status_code),1)
        return
    payload = json.loads(r2.content)
    if (len(payload["entryPoints"][0])<=0):
        log ("No Data retrived from Glucologweb",4)
        quit()

    pay_load_size = len(payload["entryPoints"][0]) - int(config["general"]["numOfReadingToSync"])
    
    payload["entryPoints"][0] = payload["entryPoints"][0][pay_load_size:]
    direction_values = [0.19, 0.14, 0.08, -0.08, -0.14, -0.19, -999]
    direction_name = ["DoubleUp", "SingleUp", "FortyFiveUp", "Flat", "FortyFiveDown", "SingleDown", "DoubleDown"]
    last_y = None
    last_x = None
    my_delta = 0.00

    cnt = 0
    entries=[]
    for my_value in payload["entryPoints"][0]:
        entry = {"type": "svg", "device": "gmns-bridge", "direction": "Flat", "filtered": 0, "unfiltered": 0, "noise": 0, "rssi": 100, "utcOffset": 0}
        my_y = float(my_value["y"])
        date_time_str = processed_date + ' ' + my_value["x"] + ':00'
        date_time_obj = datetime.strptime(date_time_str+' +0000', '%Y-%m-%d %H:%M:%S %z')
        unix_time = str(int(date_time_obj.timestamp())) + '000'
        entry["date"] = int(unix_time)
        entry["dateString"] = date_time_str + " +00:00"
        if config["glucologweb"]["units"] == "mmol/l":
            entry["sgv"] = int(round(my_y*18, 0))
        else:
            entry["sgv"] = int(round(my_y, 0))
        if last_y:
            my_delta = my_y - last_y
            entry["delta"] = round(my_delta*18, 3)
            idx = 0
            for i in direction_values:
                if my_delta >= i:
                    entry["direction"] = direction_name[idx]
                    break
                idx += 1
        last_y = my_value["y"]
        last_x = my_value["x"]

        entries.append(entry)
        cnt += 1

    #entries_json = json.dumps(entries)
    if (entries):
        nightscoutURL= config["nightscout"]["URL"] + "/api/v1/entries?token=" + config["nightscout"]["token"]
        log ("trying to call %s with %s"%(nightscoutURL,json.dumps(entries)),9)
        x = requests.post(  nightscoutURL, json=entries)
        if x.status_code != 200  :
            log ("error calling  nightscout got http response : %s" %( str(x.status_code)),1)
            return {
                    'statusCode': x.status_code,
                    'body': json.dumps('Data was not loaded! ')
            }
        else:
            return {
                    'statusCode': 200,
                    'body': json.dumps('Hello from gmns-Bridge last entry got : %s UTC'% (last_x))
            }
    else:
        log ("No Data retrived from Glucologweb",4)

if __name__ == "__main__":
    print (lambda_handler(None , None))
