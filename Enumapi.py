import flask
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import mysql.connector
from mysql.connector import Error
import json as J
import hashlib
import os
import time

f = open("seshfile", "a")
f.close()

def connector():

	try:
		connection = mysql.connector.connect(host='your_db_server_here',
										 	database='database',
										 	user='user',
										 	password='something')
		if connection.is_connected():
			db_Info = connection.get_server_info()
			print("Connected to MySQL Server version ", db_Info)
			cursor = connection.cursor()
			cursor.execute("select database();")
			record = cursor.fetchone()
			print("You're connected to database: ", record)
			return connection

	except Error as e:
		print("Error while connecting to MySQL", e)


"""finally:
		if (connection.is_connected()):
			cursor.close()
			connection.close()
			print("MySQL connection is closed")"""




def auth(user_id, passwd):
	connection = connector()

	f = open("seshfile","rt")
	data = f.read()
	f.close()
	data = data.split()
	#if hashlib.sha256(str(passwd).encode('utf-8')).hexdigest() in data:
	if passwd in data:
		return "Already there"
	

	cursor = connection.cursor(dictionary=True)
	query = ("SELECT user_pass FROM mas_user WHERE user_id=%s")
	cursor.execute(query,(user_id,))
	for x in cursor:
		if hashlib.sha256(str(x["user_pass"]).encode('utf-8')).hexdigest() == passwd:
			#tinfo = hashlib.sha256((user_id + str(hashlib.sha256(str(x["user_pass"]).encode('utf-8')).hexdigest())).encode('utf-8')).hexdigest()
			tinfo = hashlib.sha256((user_id + passwd).encode('utf-8')).hexdigest()
			f = open("seshfile","a")
			f.write(tinfo + "\n")
			f.close()
			return "true"
		else:
			return "false"
	return cursor
	

def req_auth(token):
	f = open("seshfile","rt")
	data = f.read()
	f.close()
	data = data.split()
	if token in data:
		return 1
	else:
		return 0


def remove_token(token):
	f = open("seshfile","rt")
	data = f.read()
	f.close()
	data = data.split()
	data.remove(token)
	f = open("seshfile","w")
	for x in data:
		f.write(x + "\n")

def get_ques(token):
	connection = connector()

	cursor = connection.cursor(dictionary=True)
	query = ("SELECT msec_id, subsec_id, ques_id, subquestion_id, ques_desc, ques_ret_val FROM mas_ques_pool")
	query2 = ("SELECT ques_id, ans_index, ans_desc FROM mas_ans_pool")
	cursor.execute(query)
	cursor = cursor.fetchall()
	cursor2 = connection.cursor(dictionary=True)
	cursor2.execute(query2)
	cursor2 = cursor2.fetchall()
	questionnaire_id = time.time()
	section_list = [{"sec_id":0, "ques_list":[]}]
	types = [['ms','mm','t'],['l','r','n']]
	c = 0
	d = 0
	secs = []
	for x in cursor:
		print(x)
		if c == 0:
			section_list[0]["sec_id"] = x['subsec_id']
			secs.append(x['subsec_id'])
			secs.append(c)
			c += 1
		if x['subsec_id'] in secs:
			if d == 0 and x['subquestion_id'] == None:
				s = {}
				s['ques_id'] = x['ques_id']
				s['desc'] = x['ques_desc']
				s['return_type'] = x['ques_ret_val']
				if x['ques_ret_val'] in types[0]:
					s['options'] = get_options(x['ques_id'],cursor2)
					if x['ques_ret_val'] == 'ms':
						s['answer'] = s['options'][0]	
					elif x['ques_ret_val'] == 'mm':
						s['answer'] = []
					elif x['ques_ret_val'] == 't':
						s['answer'] = 'true'
				elif x['ques_ret_val'] in types[1]:
					if x['ques_ret_val'] == 'l':
						s['answer'] = 'This is a text answer'	
					elif x['ques_ret_val'] == 'r':
						s['answer'] = 3
					elif x['ques_ret_val'] == 'n':
						s['answer'] = 0
				else:
					if x['subquestion_id'] == None:
						d += 1
					s['answer'] = []
					s['fields'] = []
					print("In block 1")
					

				section_list[secs[secs.index(x['subsec_id'])+1]]["ques_list"].append(s)
				continue

			elif d == 1 and x['subquestion_id'] != None:
				print("In block 2")
				s['fields'].append(x['ques_desc'])
				s['answer'].append(0)
				continue

			elif d == 1 and x['subquestion_id'] == None:
				print("In block 3")
				d = 0
				continue

			section_list[secs[secs.index(x['subsec_id'])+1]]["ques_list"].append(s)


		else:
			section_list[0]["sec_id"] = x['subsec_id']
			secs.append(x['subsec_id'])
			secs.append(c)
			c += 1
			s = {'ques_id':x['ques_id'],
			'desc':x['ques_desc'],
			'return_type':x['ques_ret_val'],
			}
			section_list[secs.index(x['subsec_id'])+1]["ques_list"].append(s)


	data = {
"latitude": 0,   
"longitude": 0,
"questionnaire_id": time.time(),
"temp_id": 0, 
"survey_type" : "census",

"section_list": section_list}

	return data


def get_options(ques_id, cursor):
	
	options = []

	for x in cursor:
		if ques_id == x['ques_id']:
			options.append(x['ans_desc'])

	return options



def save_ans(json,user_id):
	connection = connector()

	cursor = connection.cursor(dictionary=True)
	

	tran_survey = """INSERT INTO `enum_uat`.`tran_survey` (`master_code`,`area_code`,`user_id`,`survey_id`,`survey_dt`,`survey_type`,`temp_id`,`s_long`,`s_lat`,`imei`,`create_id`, `create_dt`) VALUES (%s, %s, %s, %s, CURDATE(), %s, %s, %s, %s, %s, %s, CURDATE())"""
	tran_survey_dynamic = """INSERT INTO `enum_uat`.`tran_survey_dynamic` (`survey_id`,`ques_id`,`ans_key_val`,`create_id`,`create_dt`) VALUES (%s, %s, %s, %s, CURDATE())"""
	tran_survey_temp = """INSERT INTO `enum_uat`.`tran_survey_temp` (`survey_id`,`temp_id`,`ques_id`,`ans_key_val`,`create_id`,`create_dt`) VALUES (%s, %s, %s, %s, %s, CURDATE())"""
	tran_user = """INSERT INTO `enum_uat`.`tran_user` (`master_code`,`area_code`,`survey_id`,`user_id`) VALUES (%s, %s, %s, %s)"""
	

	master_code = 'Y'
	area_code = '0'
	survey_id = time.time()
	survey_type = json['survey_type']
	temp_id = json['temp_id']
	s_long = json["longitude"]
	s_lat = json["latitude"]
	imei = 0
	create_id = 1

	ques = []
	for i in json["section_list"]:
		for j in i["ques_list"]:
			#print("ques_id = " + str(j["ques_id"]))
			#print("ans_key_val = " + str(j["answer"]))
			xys = str(type(j['answer']))[str(type(j['answer'])).index("'")+1:str(type(j['answer'])).index("'")+2]
			print(xys)
			#print(str(type(j['answer']))[str(type(j['answer'])).index("'"):str(type(j['answer'])).index("'")+2])
			ques.append([j["ques_id"],j["answer"],xys])

	cursor.execute(tran_survey,(master_code,area_code,user_id,str(time.time()),survey_type,temp_id,s_long,s_lat,imei,create_id))
	tran_survey_dynamic_v = []
	tran_survey_temp_v = []
	
	if temp_id == 0:
		for x in ques:
			if x[2] == 's' or x[2] == 'i':
				print(survey_id, x[0], x[1], create_id)
				tran_survey_dynamic_v.append((survey_id, x[0], x[1], create_id))
			else: 
				for i in x[1]:
					print(survey_id, x[0], i, create_id)
					tran_survey_dynamic_v.append((survey_id, x[0], i, create_id))
		print(tran_survey_dynamic_v)
		cursor.executemany(tran_survey_dynamic, tran_survey_dynamic_v)
	else:
		for x in ques:
			if x[2] == 's' or x[2] == 'i':
				print(survey_id, x[0], x[1], create_id)
				tran_survey_temp_v.append((survey_id, temp_id, x[0], x[1], create_id))
		print(tran_survey_temp_v)
		cursor.executemany(tran_survey_temp, tran_survey_temp_v)

	cursor.execute(tran_user, (master_code, area_code, survey_id, user_id))

	connection.commit()






	
			
			







app = Flask(__name__)
api = Api(app)


class login(Resource):

	def post(self):
		user_id = request.headers.get("user_id")
		user_pass = request.headers.get("user_pass")
		resp = flask.Response("")
		resp.headers['response'] = str(auth(user_id, user_pass))
		return resp
		
class question(Resource):

	def get(self):
		user_id = request.headers["user_id"]
		token = request.headers["auth"]
		if 1:
			return get_ques(token)
		else:
			return "false"

	def post(self):
		if 1:
			return get_ques(token)
		else:
			return "false"

class logout(Resource):

	def get(self):
	
		token = request.headers["auth"]
		if req_auth(token):
			resp = flask.Response("true")
			resp.headers['response'] = "true"
			remove_token(token)
			return resp
		else:
			return "false"


class answer(Resource):

	def get(self):
		user_id = request.headers["user_id"]
		token = request.headers["auth"]
		json = request.get_json()
		save_ans(json, user_id)
		print("")

		if 1:
			resp = flask.Response('')
			resp.headers['response'] = str(req_auth(token))
			return resp
		else:
			return "false"

class template(Resource):

	def get(self):
		user_id = request.headers["user_id"]
		token = request.headers["auth"]
		token = hashlib.sha256((user_id + passwd).encode('utf-8')).hexdigest()
		json = request.get_json()
		user_pass = json["user_pass"]
		if req_auth(token):
			return get_ques(token)
		else:
			return "false"



api.add_resource(login, '/login')
api.add_resource(question, '/question')
api.add_resource(logout, '/logout')
api.add_resource(answer, '/answer')

if __name__ == '__main__':

	app.run(host='0.0.0.0',debug=True)
