# -*-coding:utf-8-*-

# [START app]
import logging

# [START imports]
from flask import Flask, render_template, request, json, jsonify
import urllib.request
import urllib.parse
import json
import requests
# [END imports]

# [START create_app]
app = Flask(__name__)
# [END create_app]


@app.route('/', methods=['POST','GET'])
def subway_webhook():
	""" Get json request from dialogflow and parse json.
		Then get subway information from subway api and then send them back json
	"""
	if request.method == 'GET':
		print('Somebody is reaching through webpage!')
		return 'This is for google assistant purpose only. Please go back.'
	
	# Get station name from dialogflow
	req = request.get_json(silent=True, force=True)
	intent = req['queryResult']['intent']['displayName']

	# Let's start parsing :)

	if intent == 'which transfer station':
		t = transfer_station(req)
	else:
		s = single_station(req)
		final = single_response_json_gen(s)
		return final.jsonify()

	

	
def subway_status_changer(string):
	# Change api string to neat sentence
	a = 0
	for i in string:
		if i == '[':
			a += 1
		elif i == ']':
			a += 1
	
	if a == 2:
		return_string = string[1] + '번째 전역 입니다.'
		return return_string


def single_subway_result_gen(result):
	
	firstline_id = result['realtimeArrivalList'][0]['subwayId']
	secondline_id = result['realtimeArrivalList'][0]['subwayId']

	firstline_number = id_to_number(firstline_id)
	secondline_number = id_to_number(secondline_id)

	firstline = result['realtimeArrivalList'][0]['trainLineNm']
	firstline_arrival_code = result['realtimeArrivalList'][0]['arvlCd']

	secondline_name = result['realtimeArrivalList'][1]['trainLineNm']
	secondline_arrival_code = result['realtimeArrivalList'][1]['trainLineNm']

	# Firstline message gen
	if firstline_arrival_code == '0':
		# Current station approaching
		fmessage = '당역 접근중'

	elif firstline_arrival_code == '1':
		# Current station arrived
		fmessage = '당역 도착'

	elif firstline_arrival_code == '2':
		# Current station departed
		fmessage = '당역 출발'

	elif firstline_arrival_code == '3':
		# Prev station departed
		fmessage = '전역 출발'

	elif firstline_arrival_code == '4':
		# Prev station approaching
		fmessage = '전역 접근중'

	elif firstline_arrival_code == '5':
		# Prev station arrived
		fmessage = '전역 도착'

	elif firstline_arrival_code == '99':
		# Now running
		firstArvlMsg = result['realtimeArrivalList'][0]['arvlMsg2']
		fmessage = subway_status_changer(firstArvlMsg)

	else:
		print("An error occured in subway webhook system.")	
		fmessage = '알수 없음 :('

	
	# Secondline message gen
	if secondline_arrival_code == '0':
		# Current station approaching
		smessage = '당역 접근중'

	elif secondline_arrival_code == '1':
		# Current station arrived
		smessage = '당역 도착'

	elif secondline_arrival_code == '2':
		# Current station departed
		smessage = '당역 출발'

	elif secondline_arrival_code == '3':
		# Prev station departed
		smessage = '전역 출발'

	elif secondline_arrival_code == '4':
		# Prev station approaching
		smessage = '전역 접근중'

	elif secondline_arrival_code == '5':
		# Prev station arrived
		smessage = '전역 도착'

	elif secondline_arrival_code == '99':
		# Now running
		secondArvlMsg = result['realtimeArrivalList'][1]['arvlMsg2']
		smessage = subway_status_changer(secondArvlMsg)

	else:
		print("An error occured in subway webhook system.")	
		smessage = '알수 없음 :('

	dictionary = {'result1': fmessage, 'result2': smessage}
	
	return dictionary


def id_to_number(sw_id):

	if sw_id[2] == '0':
		return sw_id[3]
	
	elif sw_id == '1063':
		return '경의중앙'

	elif sw_id == '1065':
		return '공항철도'

	elif sw_id == '1067':
		return '경춘'

	elif sw_id == '1071':
		return '수인'

	elif sw_id == '1075':
		return '분당'

	elif sw_id == '1077':
		return '신분당'

	else:
		return '???'


def single_station(dreq):
	# Which single station
	station_kor = dreq['queryResult']['parameters']['one-station-name']
	
	station_unicode = urllib.parse.urlencode({'': station_kor})[1:] #ggul tip
	baseurl = "http://swopenapi.seoul.go.kr/api/subway/sample/json/realtimeStationArrival/1/2/" + station_unicode
	subway_result = requests.get(baseurl).json()
	status = subway_result['errorMessage']['code']

	if status[0] == 'I':
		# INFO
		if status[5:] == '000':
			# Normal status
			messages = single_subway_result_gen(subway_result) # messages is a dictionary.
		
		elif status[5:] == '200':
			# No data
			messages = {'result1': 'No subways available', 'result2': 'sorry'}

		else:
			# API Key Error maybe, or anything else	
			print("Status INFO error : " + status)
			messages = {'result1': 'Status INFO error' + status, 'result2': 'Please contact the developer\nswimtw@naver.com'}

	else:
		# ERROR
		print("Something went wrong : " + status)
		messages = {'result1': 'ERROR Code' + status, 'result2': 'Please contact the developer\nswimtw@naver.com'}


def transfer_station(req):
	# Which transfer station
	pass


	
def single_response_json_gen(dictionary):
	
	json_string = {"fulfillmentText": "", "payload": {"google": {"expectUserResponse": False,"richResponse": {"items": [{"simpleResponse": {"textToSpeech": ""}}]}}}}


	text_a = dictionary['result1']
	text_b = dictionary['result2']

	text_combine = text_a + '\n\n' + text_b

	json_string['fulfillmentText'] = text_combine
	json_string['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'] = text_combine

	return json_string


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]




	 