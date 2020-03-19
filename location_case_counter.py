import json
from geopy import distance
import csv

from data_setup import get_health_map_covid_data, yesterday, abbrev_us_state

if __name__ == "__main__":
	us_covid, us_cases, state_cases, states, csse_data, csse_us_count = get_health_map_covid_data()
	print(json.dumps(state_cases, indent=4))

	print("{} US Locations".format(len(us_covid)))
	print("{} HealthMap US Cases - {}".format(us_cases, yesterday))
	print("{} JHU US Cases - {}".format(us_cases, yesterday))

	with open('data/snflist_cases.csv', 'w', newline='') as csvfile_writer:
		fieldnames = ['CCN','SNF NAME','ADDRESS','CITY','STATE','ZIP CODE','PHONE NUMBER', 'LAT', 'LONG', 'ALTITUDE',
		              '5_MILE_RADIUS', '15_MILE_RADIUS', '50_MILE_RADIUS', '100_MILE_RADIUS', 'STATE_CASES']
		writer = csv.writer(csvfile_writer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerow(fieldnames)

		with open('./data/snflist_lat_long.csv', newline='') as csvfile:
			# outside_hubei
			reader = csv.reader(csvfile)

			for r in reader:
				name = r[1]
				street = r[2]
				city = r[3]
				state = r[4]
				zip = r[5]
				lat = r[7]
				long = r[8]
				full_state = abbrev_us_state[state]

				five_miles = 0
				fifteen_miles = 0
				fifty_miles = 0
				state_any = 0
				hundred_miles = 0
				for s in us_covid:
					cases = int(s.get('cases', 0))
					case_lat = s.get('latitude')
					case_long = s.get('longitude')
					state = s.get('province')

					miles_distance = distance.distance((case_lat, case_long), (lat, long)).miles
					if miles_distance <= 5:
						five_miles += cases
					if miles_distance <= 15:
						fifteen_miles += cases
					if miles_distance <= 50:
						fifty_miles += cases
					if miles_distance <= 100:
						hundred_miles += cases
					if state == full_state:
						state_any += cases

				row = list(r)
				row.append(five_miles)
				row.append(fifteen_miles)
				row.append(fifty_miles)
				row.append(hundred_miles)
				row.append(state_any)
				writer.writerow(row)
				csvfile_writer.flush()
				print(r)

