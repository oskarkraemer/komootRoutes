import requests
from requests.auth import HTTPBasicAuth

import json
import komoot
import os

login_url = "https://account.komoot.com/v1/signin"


def auth(email, password, client_id) -> bool:
	#Login to komoot with username and password
	s = requests.Session()
	cookies = {}

	if password == "!file":
		with open("pwd.txt", "r") as f:
			password = f.read().strip()

	res = requests.get(login_url)
	cookies = res.cookies.get_dict()

	headers = {
		"Content-Type": "application/json"
	}

	payload = json.dumps({
		"email": email,
		"password": password,
		"reason": "null"
	})

	r = s.post(login_url,
		headers=headers,
		data=payload,
		cookies=cookies,
	)

	url = "https://account.komoot.com/actions/transfer?type=signin"
	s.get(url)

	#Check if login was successful
	if not json.loads(r.text)["type"] == "logged_in":
		return False

	#Check if provided clientid is correct
	url = f"https://api.komoot.de/v007/users/{client_id}/tours/"

	response = s.get(url, auth=HTTPBasicAuth(email, password))
	
	if not response.status_code == 200:
		return False
	
	#Everything is fine / return session and cookeis
	return s, cookies



"""
Gets GPX-data from ALL tours of a user
PRIMARY FUNCTION
"""
def get_all_tours_gpx(email, password, client_id, planned = False, recorded = True):
	#Check if both planned and recorded are false
	if not planned and not recorded:
		return False

	#Authenticate
	auth_resonse = auth(email, password, client_id)
	if not auth_resonse:
		return False
	
	s, cookies = auth_resonse

	#Get tour information
	url = f"https://api.komoot.de/v007/users/{client_id}/tours/"

	response = s.get(url, auth=HTTPBasicAuth(email, password))
	if response.status_code != 200:
		print("Something went wrong...")
		print(response.text)
		print(response.status_code)
		
		return False

	data = response.json()

	tours = data["_embedded"]["tours"]

	# Filter tours
	return_tours = []
	for tour in tours:
		if tour['type'] == "tour_recorded" and recorded:
			return_tours.append(tour)
		elif tour['type'] == "tour_planned" and planned:
			return_tours.append(tour)
	

	#Get GPX data
	gpx_files = []
	for tour in return_tours:
		tour_id = tour['id']
		url = f"https://www.komoot.de/api/v007/tours/{tour_id}.gpx?hl=de"

		response = s.get(url, cookies=cookies)
		if response.status_code != 200:
			print("Something went wrong...")
			print(response.text)
			print(response.status_code)
			exit(1)

		data = response.text
		gpx_files.append(data)
	
	return gpx_files