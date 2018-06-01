# -*-coding:utf-8-*-

# [START app]
import logging

# [START imports]
from flask import Flask, render_template, request, json, jsonify
from requests_toolbelt.adapters import appengine
from google.appengine.api import urlfetch
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
		final_dict = single_response_json_gen(s)
		final_json = json.dumps(final_dict)
		
		return final_json.encode('utf-8')

	
def subway_status_changer(string):
	# Change api string to neat sentence
	a = 0
	for i in string:
		if i == '[':
			a += 1
		elif i == ']':
			a += 1
	
	if a == 2:
		return_string = string[1] + str(unicode('번째 전역 입니다.'))
		return return_string


def single_subway_result_gen(result):
	
	firstline_id = result['realtimeArrivalList'][0]['subwayId']
	secondline_id = result['realtimeArrivalList'][0]['subwayId']

	firstline_number = id_to_line(firstline_id)
	secondline_number = id_to_line(secondline_id)

	firstline = result['realtimeArrivalList'][0]['trainLineNm']
	firstline_arrival_code = result['realtimeArrivalList'][0]['arvlCd']

	secondline = result['realtimeArrivalList'][1]['trainLineNm']
	secondline_arrival_code = result['realtimeArrivalList'][1]['arvlCd']

	# Firstline message gen
	if firstline_arrival_code == '0':
		# Current station approaching
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('당역 접근중입니다.'))

	elif firstline_arrival_code == '1':
		# Current station arrived
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('당역에 도착했습니다.'))

	elif firstline_arrival_code == '2':
		# Current station departed
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('당역을 출발했습니다.'))

	elif firstline_arrival_code == '3':
		# Prev station departed
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('전역을 출발했습니다.'))

	elif firstline_arrival_code == '4':
		# Prev station approaching
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('전역 접근중입니다.'))

	elif firstline_arrival_code == '5':
		# Prev station arrived
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('전역에 도착했습니다.'))

	elif firstline_arrival_code == '99':
		# Now running
		firstArvlMsg = result['realtimeArrivalList'][0]['arvlMsg2']
		fmessage = firstline_number + ' ' + firstline + ' ' + str(unicode('열차는 ')) +  '\n' + subway_status_changer(firstArvlMsg)

	else:
		print("An error occured in subway webhook system.(CODE:firstline)")	
		print("Arrival code is " + firstline_arrival_code)
		fmessage = str(unicode('알수 없음 :('))

	
	# Secondline message gen
	if secondline_arrival_code == '0':
		# Current station approaching
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('당역 접근중입니다.'))

	elif secondline_arrival_code == '1':
		# Current station arrived
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('당역에 도착했습니다.'))

	elif secondline_arrival_code == '2':
		# Current station departed
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('당역을 출발했습니다.'))

	elif secondline_arrival_code == '3':
		# Prev station departed
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('전역을 출발했습니다.'))

	elif secondline_arrival_code == '4':
		# Prev station approaching
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('전역 접근중입니다.'))

	elif secondline_arrival_code == '5':
		# Prev station arrived
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + str(unicode('전역에 도착했습니다.'))

	elif secondline_arrival_code == '99':
		# Now running
		secondArvlMsg = result['realtimeArrivalList'][1]['arvlMsg2']
		smessage = secondline_number + ' ' + secondline + ' ' + str(unicode('열차는 ')) +  '\n' + subway_status_changer(secondArvlMsg)

	else:
		print("An error occured in subway webhook system.(CODE:secondline)")
		print("Arrival code is " + secondline_arrival_code)	
		smessage = str(unicode('알수 없음 :('))

	dictionary = {'result1': fmessage, 'result2': smessage}
	
	return dictionary


def id_to_line(sw_id):

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


def single_station(dreq):
	# Which single station
	station_kor = str(unicode(dreq['queryResult']['parameters']['one-station-name']))
	
	station_unicode = urllib.urlencode({'': station_kor})[1:] #ggul tip
	baseurl = "http://swopenapi.seoul.go.kr/api/subway/sample/json/realtimeStationArrival/1/2/" + station_unicode
	subway_result = urlfetch.fetch(baseurl).content
	subway_result = json.loads(subway_result)
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

	return messages


def transfer_station(req):
	# Which transfer station
	pass



def single_response_json_gen(dictionary):
	
	json_string = {"fulfillmentText": "", "payload": {"google": {"expectUserResponse": False,"richResponse": {"items": [{"simpleResponse": {"textToSpeech": ""}}]}}}}


	text_a = dictionary['result1']
	text_b = dictionary['result2']

	text_combine = text_a + '\n\n' + str(unicode('그리고\n')) + text_b

	json_string['fulfillmentText'] = text_combine
	json_string['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'] = text_combine

	return json_string


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

# [END app]