import os
from urllib.parse import quote_plus, unquote
import time
import requests
import sys
import re
import csv
import argparse

import sqlite3

db = sqlite3.connect('audit_results.sqlite3')
cursor = db.cursor()

parser = argparse.ArgumentParser(description='Audit LDS systems.')
parser.add_argument('--lds', default='all',
                   help='specify the LDS to audit')
parser.add_argument('--month', default='all',
                   help='specify which month (1-6) to audit')
parser.add_argument('--verbose', default='false',
					help='enable verbose reporting')
parser.add_argument('--tries', default=5,
					help='how many pauses (0.5s each) for phantomJS to render page, default 5')
parser.add_argument('--pause', default=0.5,
					help='Specify pause length, default is 0.5s')
parser.add_argument('--types', default='All',
					help='Specify a content type to check, default is all')
args = parser.parse_args()

tries = int(args.tries)

content_types = []
content_type_list = ['journal-article', 'book-chapter', 'case-studies']
if args.types in content_type_list:
	content_types.append(args.types)
else:
	if args.types != 'All':
		sys.stderr.write("{} not a recognised content type, reverting to default".format(args.types))
	content_types.extend(content_type_list)

import datetime as dt
from dateutil.relativedelta import relativedelta
check_date = dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d")

months = []

month_zero = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, 1)
for i in range(1,7):
	months.append(month_zero - relativedelta(months=i))

skip_sources = []
lds_urls = {}
lds_urls['Summon'] = [
	["QUT", "https://qut.summon.serialssolutions.com/api/search?ho=f&q="],
	["UWE", "http://uwe.summon.serialssolutions.com/api/search?ho=f&q="],
	["Herts", "http://herts.summon.serialssolutions.com/api/search?ho=f&q="],
	["Liberty", "http://liberty.summon.serialssolutions.com/api/search?ho=f&q="],
	["AmericanUniversity", "https://american.summon.serialssolutions.com/api/search?ho=f&q="],
	]
lds_urls['Primo'] = [
	["Durham", "http://discover.durham.ac.uk/primo_library/libweb/action/search.do?fn=search&ct=search&pcAvailabiltyMode=true&pcAvailClicked=true&initialSearch=true&mode=Basic&tab=default_tab&indx=1&dum=true&srt=rank&vid=44DUR_VU1&frbg=&vl%28freeText0%29="],
	["ILU", "https://iluplus.hosted.exlibrisgroup.com/primo-explore/search?tab=default_tab&pcAvailability=true&search_scope=institution_scope&vid=41ZBL&lang=en_US&offset=0&query=any,contains,"],
	["Western Sydney", "https://west-sydney-primo.hosted.exlibrisgroup.com/primo-explore/search?tab=default_tab&search_scope=default_scope&vid=UWS-ALMA&lang=en_US&offset=0&sortby=rank&pcAvailability=true&query=any,contains,"],
	["Manchester", "https://www.librarysearch.manchester.ac.uk/discovery/search?tab=Everything&search_scope=MyInst_and_CI&vid=44MAN_INST:MU_NUI&lang=en&offset=0&pcAvailability=true&query=any,contains,"],
	["Central Michigan", "https://cmich-primo.hosted.exlibrisgroup.com/primo-explore/search?tab=everything&search_scope=EVERYTHING&pcAvailability=true&sortby=rank&vid=01CMICH&query=any,contains,"],
]
lds_urls['WorldCat'] = [
	["ADU", "https://adu.on.worldcat.org/search?databaseList=4096,4098,4077,4079,4135,3684,2375,2572,2175,3284,2328,1875,1697,2268,3313,2267,3978,3879,2264,2263,2262,3197,1271,2261,283,2260,2281,3404,1842,2237,2259,3201,4015,1708,4017,3867&page=1&queryType=search&stickyFacetsChecked=false&queryString="],
	["McGill", "http://mcgill.worldcat.org/search?scope=0&q="],
	["Pepperdine", "http://pepperdine.worldcat.org/search?scope=0&q="],
	["Emporia", "https://emporiastate.on.worldcat.org/search?scope=&sortKey=BEST_MATCH&queryString="],
]

# art_title = "Bridging the gap between theory and practice in management accounting"
# query = "Bridging gap between theory practice management accounting Jansen"
# doi = '10.1108/AAAJ-10-2015-2261'

lds_list = []

if args.lds == 'all':
	for l in lds_urls:
		lds_list.append(l)
elif args.lds in lds_urls:
	lds_list.append(args.lds)
else:
	print("Unrecognised LDS: {}".format(args.lds))
	exit()

months_to_audit = {}
	
if args.month == 'all':
	for month in months:
		months_to_audit[dt.datetime.strftime(month, "%Y-%m-%d")] = 1
elif int(args.month) >= 1 and int(args.month) <= 6:
	month = dt.datetime.strftime(months[int(args.month) - 1], "%Y-%m-%d")
	months_to_audit[month] = 1
	
from selenium import webdriver

driver = webdriver.PhantomJS()
driver.set_window_size(1024, 768)

s = requests.Session()

def process_item(art_title, query, doi, lds, q_count, content_type):
	# done_articles[type][lds][source][date]
	responses = {}
	if not lds in responses:
		responses[lds] = {}
	if len(skip_sources) == len(lds_urls[lds]):
		return responses
	print("Checking {}\t{}\t{} ({})".format(lds, art_title, doi, q_count))
	for source_details in lds_urls[lds]:
		pi_url = source_details[1]
		pi_source = source_details[0]
		if pi_source in skip_sources:
			print("Skipping {}".format(pi_source))
			continue
		if not pi_source in responses[lds]:
			responses[lds][pi_source] = 0
		found = 0
		# print(url)
		# sys.stderr.write(url + quote_plus(query) + "\n")
		
		# Uncomment line to check source skipping is working OK
		# skip_sources.append(pi_source)
				
		if args.verbose == 'true': 
			print("\t{}".format(pi_source), end="", flush="true") # url + quote_plus(query))
			
		if not lds == 'Primo':
			try:
				r = s.get("".join([pi_url, quote_plus(query)]))
				# for h in r.history:
					# print("Redirected: ", h.url)
				# for c in r.cookies:
					# print("Cookie: ", c)
				content = unquote(r.text)
				if re.search(doi, content, re.IGNORECASE):
					# print("Requests: Article DOI found")
					found = 1
					responses[lds][pi_source] = 1
				elif re.search(art_title, content):
					# print("Requests: Article title found")
					found = 1
					responses[lds][pi_source] = 1
				# else:
					# print("Requests: Article not found: ", r.status_code)
				# if lds == 'Summon':
					# print(doi)
					# print(content)
					# exit()
			except ConnectionRefusedError:
				print("Connection refused, dropping source {}".format(pi_source))
				skip_sources.append(pi_source)
			
			except Exception as e:
				print("\nCouldn't get with Requests: {}".format(getattr(e, 'message', repr(e))))
				skip_sources.append(pi_source)
				# raise
				continue
				
		if not found and not lds == 'Summon':
			try:
				driver.get("".join([pi_url, quote_plus(query)]))
				for i in range(tries):
					if args.verbose == 'true': 
						print(".", end="", flush="true")
					# driver.save_screenshot('screen.png')
					page_html = driver.find_element_by_tag_name('html').get_attribute('innerHTML')
					# with open ('response.html', 'w', encoding='utf-8') as html_file:
						# html_file.write(page_html)
					content = unquote(page_html)
					if re.search(doi, content, re.IGNORECASE):
						# print("Driver: Article DOI found after pause {}".format(i+1))
						found = 1
						responses[lds][pi_source] = 1
						break
					elif re.search(art_title, content):
						# print("Driver: Article title found after pause {}".format(i+1))
						found = 1
						responses[lds][pi_source] = 1
						break
						
					time.sleep(int(args.pause))
					# else:
						# print("Driver: Article not found after pause {}".format(i+1))
				message="No"
				if found:
					message="Yes"
				if args.verbose == 'true':  
					print(message, end="", flush="true")
			except ConnectionRefusedError:
				print("Connection refused {}".format(pi_source))
				skip_sources.append(pi_source)
			# except URLError:
				# print("URL Error, dropping source {}".format(pi_source))
				# lds_urls[lds][pi_source].clear()
			except Exception as e:
				print("\n{}: Couldn't get with WebDriver: {}".format(pi_source, getattr(e, 'message', repr(e))))
				skip_sources.append(pi_source)
				# raise
				continue
		if args.verbose == 'true':  
			print("")
			
		cursor.execute('''select * from audit_results where doi = ? and service = ? and source = ? and pub_date = ?''', (doi, lds, pi_source, date))
		db_results = cursor.fetchall()
		if len(db_results) == 0:
			cursor.execute('''insert into audit_results (doi, pub_date, check_date, type, service, source, found) values (?, ?, ?, ?, ?, ?, ?)''', (doi, date, str(check_date), content_type, lds, pi_source, found,))
			db.commit()
		else:
			for doi_row in db_results:
				# print(doi_row)
				if doi_row[-1] == 0 and found == 1:
					# print("Updating row; found: {}".format(found))
					# print(check_date, doi, service, source)
					cursor.execute('''update audit_results set found = 1, check_date = ? where doi = ? and service = ? and source = ?''', (check_date, doi, lds, pi_source,))
					db.commit()
				else:
					# print("Updating audit date to {}".format(check_date))
					cursor.execute('''update audit_results set found = 0, check_date = ? where doi = ? and service = ? and source = ?''', (check_date, doi, lds, pi_source,))
					db.commit()
					
					
		if not (found == 1):
			d_v = 1
			# print("Article not found")
			# sys.stderr.write("".join([url, quote_plus(query)]) + "\n")
		else:
			break
	return responses
	
content_type = ''
search_terms = {}		

print("Auditing LDS:")
for l in lds_list:
	print("\t{}".format(l))
print("\tMonths:")
for m in months_to_audit:
	print("\t\t{}".format(m))
print("\t\tContent Types:")
for c in content_types:
	print("\t\t\t{}".format(c))

for root, dirs, files in os.walk(os.path.join('..', 'doclists')):
	print("Processing directory: {}".format(root))
	file_count = 0
	
	for file in files:
		# if file_count == 3:
			# break
		if re.search(r'_id', file):
			continue
		# if not file.startswith('2018'):
			# continue
		file_elements = re.search(r'(\d{4}-\d{2}-\d{2})_([^_.]+)', file)
		file_date = file_elements[1]
		if not file_date in months_to_audit:
			continue
			
		content_type = file_elements[2]
		
		if not content_type in content_types:
			continue
		if not file_date in search_terms:
			search_terms[file_date] = {}
			search_terms[file_date]['dois'] = []
			search_terms[file_date]['terms'] = []
			search_terms[file_date]['titles'] = []
						
		if re.search(r'_doi', file):
			print ("Processing {}".format(file))
			dates = []
			done_articles = {}

			file_count +=  1
			with open(os.path.join(root, file), 'r', encoding='utf-8') as title_list:
				row_count = 0
				temp_term = ''
				for row in csv.reader(title_list):
					if len(row) == 1:
						search_terms[file_date]['dois'].append(row[0])
					else:
						print(row, len(row))
			for date in search_terms:
				print("{} {} found in list for {}".format(len(search_terms[date]['dois']), content_type, date))
				
				
				# print("Date:{}\tDOIs:{}\tTerms:{}\tTitles:{}".format(date, len(search_terms[date]['dois']), len(search_terms[date]['terms']), len(search_terms[date]['titles'])))
				
				if len(search_terms[date]['dois']) == 0:
					continue
					
				for lds in lds_list:
					checked_arts_count = 0
					audit_results = {}
					audit_dates = {}
					cursor.execute('''select distinct doi, sum(found), check_date from audit_results where service = ? and pub_date = ? and type = ? group by doi''', (lds, date, content_type))
					checked_arts = cursor.fetchall()
					print("{} {} found in db for {} / {}".format(len(checked_arts), content_type, lds, date))
					found_count = 0
					for row in checked_arts:
						if row[1] > 0:
							found_count += 1
						audit_results[row[0]] = row[1]
						audit_dates[row[0]] = row[2]
					print("\t{} of those have been found".format(found_count))

					if args.verbose == 'true': 
						print("Date:{}\ti:{}".format(date, i))

					# don't re-check anything within 7 days of last audit
					boundary_date = dt.datetime.now() - relativedelta(weeks = 1)
					if args.verbose == 'true':
						print("Not checking anything that's been audited on or after {}".format(dt.datetime.strftime(boundary_date, "%Y-%m-%d")))
					for i in range (0, len(search_terms[date]['dois'])):
						query = search_terms[date]['terms'][i]
						doi = search_terms[date]['dois'][i]
						art_title = search_terms[date]['titles'][i]
						
						if doi in audit_results and audit_results[doi] > 0:
							continue
						if doi in audit_dates and dt.datetime.strptime(audit_dates[doi], "%Y-%m-%d") >= boundary_date:
							if args.verbose == 'true':
								print("{} last checked within a week: {}".format(doi, audit_dates[doi]))
							continue
						elif doi in audit_dates:
							if args.verbose == 'true':
								print("{} last checked on {}".format(doi, audit_dates[doi]))
						else:
							if args.verbose == 'true':
								print("{} not checked before".format(doi))
							
							
						check_results = process_item(art_title, query, doi, lds, i, content_type)
						# print("{}\n\t{}".format(doi, check_results[lds]))
						if len(check_results[lds]) > 0:
							checked_arts_count += 1

					print("\t{} articles checked".format(checked_arts_count))
					
			search_terms.clear()
			

		elif not re.search(r'_doi|_id', file):
			with open(os.path.join(root, file), 'r', encoding='utf-8') as title_list:
				print ("Processing {}".format(file))
				row_count = 0
				temp_term = ''
				for row in csv.reader(title_list):
					row_count += 1
					if row_count % 4 == 1:
						temp_term = row[0]
						search_terms[file_date]['titles'].append(temp_term)
					if not row_count % 4 == 0:
						continue
					if len(row) == 1:
						term = row[0]
					else:
						term = temp_term
					search_terms[file_date]['terms'].append(term)


driver.close()
