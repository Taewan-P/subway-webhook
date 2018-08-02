# -*-coding:utf-8-*-

# [START app]
import logging

# [START imports]
from flask import Flask, render_template, request, json, jsonify
from requests_toolbelt.adapters import appengine
from google.appengine.api import urlfetch
from google.appengine import runtime
from concurrent.futures import TimeoutError
from collections import OrderedDict
from urlparse import urlparse
from urllib2 import urlopen
import urllib
import json
import requests
import sys

# [END imports]

reload(sys)
sys.setdefaultencoding('utf-8')
appengine.monkeypatch()

# [START create_app]
app = Flask(__name__)
# [END create_app]


@app.route('/', methods=['POST','GET'])
def subway_main():
    """ Get json request from dialogflow and parse json.
        Then get subway information from subway api and then send them back json
    """
    if request.method == 'GET':
        logging.warning('Somebody is reaching through webpage!')
        return 'This page is not web-reachable. Please go back.'
    
    # Get station name from dialogflow
    req = request.get_json(silent=True, force=True)
    logging.warning(req)
    station_name = req['queryResult']['parameters']['station-name']
    station_unicode = urllib.urlencode({'': station_name})[1:]
    
    subway_response = subway_parser(station_unicode, 12)

    if subway_response == None:
        # return 'subway api server error.'
        fmessages = list()
        a = str(unicode("현재 서울 지하철 서버에 일시적으로 접속할 수 없습니다."))
        b = str(unicode("이것은 서울 지하철 서버의 일시적인 문제로, 잠시후에 다시 시도해 주세요."))
        fmessages.append(a)
        fmessages.append(b)
        final_result = response_json_gen(fmessages)
        final_json = json.dumps(final_result)
        
        return final_json.encode('utf-8')

    logging.warning(str(subway_response))
    try:
        status = subway_response['errorMessage']['code']
    except (KeyError), e:
        status = subway_response['code']


    # Error status analysis
    if status[0] == 'I':
        # INFO
        messages = list()
        if status[5:] == '000':
            # Normal status
            pass
        
        elif status[5:] == '200':
            # No data
            a = str(unicode('지하철이 없습니다. 역 이름을 다시 확인해 보세요.'))
            messages.append(a)
            final_result = response_json_gen(messages)
            final_json = json.dumps(final_result)
        
            return final_json.encode('utf-8')

        else:
            # API Key Error maybe, or anything else 
            logging.warning("Status INFO error : " + status)
            a = str(unicode('Status INFO 에러가 발생했습니다. 관리자한테 문의해 주세요.'))
            b = str(unicode('개발자 정보는 구글 어시스턴트 홈페이지 앱 정보에서 보실 수 있습니다.'))
            messages.append(a)
            messages.append(b)

            final_result = response_json_gen(messages)
            final_json = json.dumps(final_result)
        
            return final_json.encode('utf-8')

    else:
        # ERROR
        logging.warning("Something went wrong : " + status)
        a = str(unicode('서버 상태 오류!!! 관리자한테 문의해 주세요.'))
        b = str(unicode('개발자 정보는 구글 어시스턴트 홈페이지 앱 정보에서 보실 수 있습니다.'))
        messages.append(a)
        messages.append(b)

        final_result = response_json_gen(messages)
        final_json = json.dumps(final_result)
        
        return final_json.encode('utf-8')

    # 1. Remove duplicated line num
    subway_ids = [subway_response['realtimeArrivalList'][i]['subwayId'] for i in range(len(subway_response['realtimeArrivalList']))]
    subway_line = list(OrderedDict.fromkeys(subway_ids)) # This shows how many lines there are in the called station.
    
    logging.warning(subway_line)
    subway_line.sort()
    logging.warning(subway_line)

    # 2. Main Algorithm
    subway_result_list = parse_two_lines(subway_response, subway_line)
    
    # 3. Result generate
    for result_json in subway_result_list:
        messages.append(message_converter(result_json))
    
    fmessages = list()
    for k in range(len(messages)/2):
        astring = messages[2*k] + '\n\n' + messages[2*k+1]
        fmessages.append(astring)
    
    final_result = response_json_gen(fmessages)
    final_json = json.dumps(final_result)

    return final_json.encode('utf-8')


def subway_parser(sname,num):
    """ This is a subway parser from subway api.
        This can parse 'num' number of information of the following 'sname' station.
        If api server is down, then it returns None.
    """
    logging.warning("subway-name : " + sname)
    url = "http://swopenapi.seoul.go.kr/api/subway/<INSERT API KEY>/json/realtimeStationArrival/1/" + str(num) + "/" + sname

    try:
        subway_request = requests.get(url, timeout=10).json()
        logging.warning(str(subway_request))
    except (ValueError, TimeoutError), e:
        logging.warning("Seoul subway server error 503")
        return None
    
    return subway_request
    

def parse_two_lines(sjson, slist):
    k = 0
    subway_message_list = list()
    for i in slist:
        # Normal case
        train_name_list = list()
        for j in range(len(sjson['realtimeArrivalList'])):
            if i == sjson['realtimeArrivalList'][j]['subwayId']:
                if k == 2:
                    k = 0
                    break
                
                elif k == 1:
                    a = sjson['realtimeArrivalList'][j]['updnLine']
                    if a in train_name_list:
                        continue
                    else:
                        subway_message_list.append(sjson['realtimeArrivalList'][j])
                        k += 1

                else: # k = 0
                    train_name_list.append(sjson['realtimeArrivalList'][j]['updnLine'])
                    subway_message_list.append(sjson['realtimeArrivalList'][j])
                    k += 1

    logging.warning(subway_message_list)           
    return subway_message_list

            
def id_to_line(sw_id):
    """ This method changes the subway code to Korean.
        The subway code comes from the seoul subway api json
    """

    if sw_id[2] == '0':
        return sw_id[3] + str(unicode('호선'))
    
    elif sw_id == '1063':
        return str(unicode('경의중앙선'))

    elif sw_id == '1065':
        return str(unicode('공항철도'))

    elif sw_id == '1067':
        return str(unicode('경춘선'))

    elif sw_id == '1071':
        return str(unicode('수인선'))

    elif sw_id == '1075':
        return str(unicode('분당선'))

    elif sw_id == '1077':
        return str(unicode('신분당선'))

    else:
        return str(unicode('업데이트되지 않은 노선'))
    

def message_converter(sjson):
    line_number = sjson['subwayId']
    
    line_nm = id_to_line(line_number)
    line_info = sjson['trainLineNm']    
    
    arvlcd = sjson['arvlCd']

    train = str(unicode('열차는 '))
    if arvlcd == '0':
        # Current station approaching
        message =  train_string_combiner(line_nm, line_info, train) + str(unicode('당역 접근중입니다.'))

    elif arvlcd == '1':
        # Current station arrived
        message = train_string_combiner(line_nm, line_info, train) + str(unicode('당역에 도착했습니다.'))

    elif arvlcd == '2':
        # Current station departed
        message = train_string_combiner(line_nm, line_info, train) + str(unicode('당역을 출발했습니다.'))

    elif arvlcd == '3':
        # Prev station departed
        message = train_string_combiner(line_nm, line_info, train) + str(unicode('전역을 출발했습니다.'))

    elif arvlcd == '4':
        # Prev station approaching
        message = train_string_combiner(line_nm, line_info, train) + str(unicode('전역 접근중입니다.'))

    elif arvlcd == '5':
        # Prev station arrived
        message = train_string_combiner(line_nm, line_info, train) + str(unicode('전역에 도착했습니다.'))
        
    elif arvlcd == '99':
        # Now running
        arvlmsg = sjson['arvlMsg2']
        # logging.warning('type :line_nm, line_info, train')
        # logging.warning(type(line_nm))
        # logging.warning(type(line_info))
        # logging.warning(type(train))
        # logging.warning(type(arvlmsg))
        # logging.warning(arvlmsg)
        # logging.warning(type(train_string_combiner(line_nm, line_info, train)))
        # logging.warning(type(subway_status_changer(arvlmsg)))
        message = train_string_combiner(line_nm, line_info, train) + subway_status_changer(arvlmsg)

    else:
        logging.warning("An error occured in subway webhook system.(CODE:arvlCd)")  
        logging.warning("Error arrival code is " + arvlcd)
        message = str(unicode('알수 없음 :('))

    return message


def train_string_combiner(a,b,korean):
    """ This is a simple method to make arrival message string combine easier.
    """
    return a + ' ' + b + ' ' + str(unicode(korean)) + ' \n'


def subway_status_changer(string):
    """ This method changes seoul subway message into neat speakable sentences.
        This is used in both single_station() and transfer_station().
    """

    a = 0
    for i in string:
        if i == '[':
            a += 1
        elif i == ']':
            a += 1

    if a == 2:
        return_string = string[1] + str(unicode('번째 전역 입니다.'))
    else:
        return_string = string + str(unicode(' 도착합니다.'))
    
    return return_string



def response_json_gen(mlist):
    a = list()
    for m in mlist:
        b = {"simpleResponse": {"textToSpeech": ""}}
        b['simpleResponse']['textToSpeech'] = m
        a.append(b)
    
    json_string = {"payload": {"google": {"expectUserResponse": False,"richResponse": {"items": a}}}}

    return json_string


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

# [END app]
