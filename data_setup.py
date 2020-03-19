import csv
import requests
import time
import sys
import json
from geopy.geocoders import Nominatim
from datetime import date, timedelta

millis = int(round(time.time() * 1000))
yesterday = date.today() - timedelta(days=1)

# https://gist.github.com/rogerallen/1583593
us_state_abbrev = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District Of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Northern Mariana Islands':'MP',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Palau': 'PW',
    'Pennsylvania': 'PA',
    'Puerto Rico': 'PR',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virgin Islands': 'VI',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
}

# thank you to @kinghelix and @trevormarburger for this idea
abbrev_us_state = dict(map(reversed, us_state_abbrev.items()))

def get_csse_covid_data():
	us_data = dict()
	global yesterday
	# 03-18-2020
	us_count = 0
	yesterday_date = yesterday.strftime("%0m-%0d-%Y")
	url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{}.csv'.format(yesterday_date)
	with requests.Session() as s:
		download = s.get(url)

		decoded_content = download.content.decode('utf-8')

		cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')
		my_list = list(cr)
		for row in my_list:
			country = row.get('Country/Region')
			state = row.get('Province/State')
			confirmed = row.get('Confirmed', 0)
			if country == 'US':
				us_data[state] = row
				us_count += int(confirmed)
	return us_data, us_count


def get_health_map_covid_data():
	global millis
	covid_data_req = requests.get('https://www.healthmap.org/covid-19/ncov2019.unique-locations.json?nocache={}'.
	                              format(millis))

	if covid_data_req.status_code == 200:
		outside_hubei = covid_data_req.json().get('outside_Hubei', list())
	else:
		print('failed to get latest covid data')
		sys.exit(1)

	if len(outside_hubei) == 0:
		print('failed to get latest covid data')
		sys.exit(1)

	csse_data, csse_us_count = get_csse_covid_data()

	us_covid = [loc for loc in outside_hubei if loc.get('country') == "United States"]
	us_cases = 0
	states = dict()
	state_cases = dict()
	states['Other'] = list()
	for us in us_covid:
		us_cases += us.get('cases', 0)
		state = us.get('province')
		if len(state) > 0:
			if state not in states:
				states[state] = list()
			states[state].append(us)
		else:
			states['Other'].append(state)

	for state in states.keys():
		state_count = 0
		for loc in states[state]:
			state_count += loc.get('cases', 0)
		state_cases[state] = state_count

	return us_covid, us_cases, state_cases, states, csse_data, csse_us_count


cache = dict()


def get_location(street, city, state, zip):
	address = '{} {}, {} {}'.format(street, city, state, zip)
	address_alt = '{}, {} {}'.format(city, state, zip)
	print(address)
	geolocator = Nominatim(user_agent="covid_snf_scraper_{}".format(zip))
	try:
		time.sleep(1.5)
		location = cache.get(address)
		if not location:
			location = geolocator.geocode(address)
			cache[address] = location
		if location:
			return location
		else:
			location = cache.get(address_alt)
			if not location:
				location = geolocator.geocode(address_alt)
				cache[address] = location
			return location
	except Exception as ex:
		print(ex)
		time.sleep(10)
		return get_location(address, city, state, zip)


def update_snf_data():
	row_n = 0
	with open('data/snflist_lat_long.csv', 'a', newline='') as csvfile_writer:
		fieldnames = ['CCN','SNF NAME','ADDRESS','CITY','STATE','ZIP CODE','PHONE NUMBER', 'LAT', 'LONG', 'ALTITUDE']
		writer = csv.DictWriter(csvfile_writer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)
		with open('./data/snflist.csv', newline='') as csvfile:
			# outside_hubei
			reader = csv.DictReader(csvfile)

			for r in reader:
				row_n += 1
				# CCN,SNF NAME,ADDRESS,CITY,STATE,ZIP CODE,PHONE NUMBER
				address = r.get('ADDRESS')
				city = r.get('CITY')
				state = r.get('STATE')
				zip = r.get('ZIP CODE')
				location = get_location(address, city, state, zip)
				if location:
					r['LAT'] = location.latitude
					r['LONG'] = location.longitude
					r['ALTITUDE'] = location.altitude
				else:
					print('bad location {}'.format(r))
					continue
				writer.writerow(r)
				if row_n % 10 == 0:
					csvfile_writer.flush()


if __name__ == "__main__":
	print(millis)

	update_snf_data()
