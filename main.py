# -*-coding:utf-8-*-

# [START app]
import logging

# [START imports]
from flask import Flask, render_template, request, json, jsonify
from requests_toolbelt.adapters import appengine
from google.appengine.api import urlfetch
from google.appengine import runtime
from concurrent.futures import TimeoutError
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

##### Main #####

@app.route('/', methods=['POST','GET'])
def subway_webhook():
	""" Get json request from dialogflow and parse json.
		Then get subway information from subway api and then send them back json
	"""
	if request.method == 'GET':
		logging.warning('Somebody is reaching through webpage!')
		return 'This is for google assistant purpose only. Please go back.'
	
	# Get station name from dialogflow
	req = request.get_json(silent=True, force=True)
	logging.warning(req)

	intent = req['queryResult']['intent']['displayName']

	# Let's start parsing :)

	if intent == 'which transfer station':
		t = transfer_station(req)
	else:
		s = single_station(req)
		final_dict = single_response_json_gen(s)
		final_json = json.dumps(final_dict)
		
		return final_json.encode('utf-8')

################

########## Public methods ##########

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
		return return_string

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

def train_string_combiner(a,b,korean):
	""" This is a simple method to make arrival message string combine easier.
	"""
	return a + ' ' + b + ' ' + str(unicode(korean)) + ' \n'

####################################

########## Single station methods ##########

def single_station(dreq):
	""" This method is for single station call.
		Dialogflow Intent : Which single station.
		When the client wants the station info that has no transfer lines, 
		then the webhook call will be done in this method.
	"""
	station_kor = dreq['queryResult']['parameters']['one-station-name']
	logging.warning(station_kor)
	station_unicode = urllib.urlencode({'': station_kor})[1:] #ggul tip
	logging.warning(str(station_unicode))
	baseurl = "http://swopenapi.seoul.go.kr/api/subway/<인증키 들어가는곳ㅎ>/json/realtimeStationArrival/1/2/" + station_unicode
	
	try:
		subway_result = requests.get(baseurl, timeout=6).json()
		logging.warning(str(subway_result))
		status = subway_result['errorMessage']['code']
		if status[0] == 'I':
			# INFO
			if status[5:] == '000':
				# Normal status
				messages = single_subway_result_gen(subway_result) # messages is a dictionary.
			
			elif status[5:] == '200':
				# No data
				a = str(unicode('지하철이 없습니다.'))
				messages = {'result1': a, 'result2': ''}

			else:
				# API Key Error maybe, or anything else	
				logging.warning("Status INFO error : " + status)
				a = str(unicode('Status INFO 에러가 발생했습니다. 관리자한테 문의해 주세요.'))
				b = str(unicode('개발자 정보는 구글 어시스턴트 홈페이지 앱 정보에서 보실 수 있습니다.'))
				messages = {'result1': a, 'result2': b}

		else:
			# ERROR
			logging.warning("Something went wrong : " + status)
			a = str(unicode('서버 상태 오류!!! 관리자한테 문의해 주세요.'))
			b = str(unicode('개발자 정보는 구글 어시스턴트 홈페이지 앱 정보에서 보실 수 있습니다.'))
			messages = {'result1': a, 'result2': b}

	except (ValueError, TypeError, KeyError, TimeoutError, runtime.DeadlineExceededError, requests.exceptions.Timeout), e:
		a = str(unicode('지금 서울 지하철 서버가 맛이 갔습니다. 다시 시도해 주세요.'))
		logging.warning('Error code : ' + str(e))
		messages = {'result1': a, 'result2': ''}


	return messages

def single_subway_result_gen(result):
	""" This method generates messages to send to dialogflow back.
		Before changing it to json response, we need to change the subway api result more readable.
		This method generates neat readable messages.
	"""

	firstline_id = result['realtimeArrivalList'][0]['subwayId']
	secondline_id = result['realtimeArrivalList'][0]['subwayId']

	firstline_number = id_to_line(firstline_id)
	secondline_number = id_to_line(secondline_id)

	firstline = result['realtimeArrivalList'][0]['trainLineNm']
	firstline_arrival_code = result['realtimeArrivalList'][0]['arvlCd']

	secondline = result['realtimeArrivalList'][1]['trainLineNm']
	secondline_arrival_code = result['realtimeArrivalList'][1]['arvlCd']
	train = str(unicode('열차는 '))

	# Firstline message gen
	if firstline_arrival_code == '0':
		# Current station approaching
		fmessage =  train_string_combiner(firstline_number, firstline, train) + str(unicode('당역 접근중입니다.'))

	elif firstline_arrival_code == '1':
		# Current station arrived
		fmessage = train_string_combiner(firstline_number, firstline, train) + str(unicode('당역에 도착했습니다.'))

	elif firstline_arrival_code == '2':
		# Current station departed
		fmessage = train_string_combiner(firstline_number, firstline, train) + str(unicode('당역을 출발했습니다.'))

	elif firstline_arrival_code == '3':
		# Prev station departed
		fmessage = train_string_combiner(firstline_number, firstline, train) + str(unicode('전역을 출발했습니다.'))

	elif firstline_arrival_code == '4':
		# Prev station approaching
		fmessage = train_string_combiner(firstline_number, firstline, train) + str(unicode('전역 접근중입니다.'))

	elif firstline_arrival_code == '5':
		# Prev station arrived
		fmessage = train_string_combiner(firstline_number, firstline, train) + str(unicode('전역에 도착했습니다.'))

	elif firstline_arrival_code == '99':
		# Now running
		firstArvlMsg = result['realtimeArrivalList'][0]['arvlMsg2']
		fmessage = train_string_combiner(firstline_number, firstline, train) + subway_status_changer(firstArvlMsg)

	else:
		logging.warning("An error occured in subway webhook system.(CODE:firstline)")	
		logging.warning("Error arrival code is " + firstline_arrival_code)
		fmessage = str(unicode('알수 없음 :('))

	
	# Secondline message gen
	if secondline_arrival_code == '0':
		# Current station approaching
		smessage = train_string_combiner(secondline_number, secondline, train) + str(unicode('당역 접근중입니다.'))

	elif secondline_arrival_code == '1':
		# Current station arrived
		smessage = train_string_combiner(secondline_number, secondline, train) + str(unicode('당역에 도착했습니다.'))

	elif secondline_arrival_code == '2':
		# Current station departed
		smessage = train_string_combiner(secondline_number, secondline, train) + str(unicode('당역을 출발했습니다.'))

	elif secondline_arrival_code == '3':
		# Prev station departed
		smessage = train_string_combiner(secondline_number, secondline, train) + str(unicode('전역을 출발했습니다.'))

	elif secondline_arrival_code == '4':
		# Prev station approaching
		smessage = train_string_combiner(secondline_number, secondline, train) + str(unicode('전역 접근중입니다.'))

	elif secondline_arrival_code == '5':
		# Prev station arrived
		smessage = train_string_combiner(secondline_number, secondline, train) + str(unicode('전역에 도착했습니다.'))

	elif secondline_arrival_code == '99':
		# Now running
		secondArvlMsg = result['realtimeArrivalList'][1]['arvlMsg2']
		smessage = train_string_combiner(secondline_number, secondline, train) + subway_status_changer(secondArvlMsg)

	else:
		logging.warning("An error occured in subway webhook system.(CODE:secondline)")
		logging.warning("Arrival code is " + secondline_arrival_code)	
		smessage = str(unicode('알수 없음 :('))
	
	smessage = str(unicode('그리고\n')) + smessage
	dictionary = {'result1': fmessage, 'result2': smessage}
	
	return dictionary

def single_response_json_gen(dictionary):
	""" This is a method that makes json string for dialogflow.
		This method can be developed more such as rich responses...
		Hope I study nodejs for this haha:)
	"""
	json_string = {"fulfillmentText": "", "payload": {"google": {"expectUserResponse": False,"richResponse": {"items": [{"simpleResponse": {"textToSpeech": ""}}]}}}}


	text_a = dictionary['result1']
	text_b = dictionary['result2']

	text_combine = text_a + '\n\n' + text_b

	json_string['fulfillmentText'] = text_combine
	json_string['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'] = text_combine

	return json_string

############################################

########## Transfer station methods ##########

def transfer_station(dreq):
	# Which transfer station
	stations = dreq['queryResult']['parameters'] # Dictionary of (two, three, four) stations
	pass






@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

# [END app]