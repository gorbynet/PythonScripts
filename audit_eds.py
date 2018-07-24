import json
import sys
import os
from urllib.parse import unquote
import requests
import re
import time
from lxml import html
from fuzzywuzzy import fuzz
import csv

content_types = ['journal-article', 'book-chapter', 'case-studies']
# content_types['journal-article'] = 1

#	type/DOI/LDS/Source/Date/Found?
# type:case-studies	10.1108/eemcs-07-2016-0160	WorldCat	McGill	01/06/2017	1
dates = []
done_articles = {}
for type in content_types:
	done_articles[type] = {}
	done_articles[type]['EBSCO EDS'] = {}
	done_articles[type]['EBSCO EDS']['Emerald'] = {}

with open ('report_dump.txt', 'r', encoding='utf-8') as done_article_list:
	reader = csv.reader(done_article_list, dialect='excel-tab')
	row_count = 0
	for row in reader:
		row_count += 1
		types = re.search(r'type:(.+)', row[0])
		if types:
			type = types[1]
		doi = row[1]
		lds = row[2]
		source = row[3]
		date = row[4]
		if re.search(r'\d{2}/\d{2}/\d{4}', date):
			date_parts = re.search(r'(\d{2})/(\d{2})/(\d{4})', date)
			date = "-".join([date_parts[3],date_parts[2],date_parts[1]])
		if not date in dates:
			dates.append(date)
		found = int(row[5])
		if not type in done_articles:
			done_articles[type] = {}
		if not lds in done_articles[type]:
			done_articles[type][lds] = {}
		if not source in done_articles[type][lds]:
			done_articles[type][lds][source] = {}
		if not date in done_articles[type][lds][source]:
			done_articles[type][lds][source][date] = {}
		if not doi in done_articles[type][lds][source][date]:
			done_articles[type][lds][source][date][doi] = 0
		if found == 1:
			done_articles[type][lds][source][date][doi] = 1
		# print (row, done_articles[type][lds][source][date][doi])
	print("{} rows processed".format(row_count))
	# if '2018-03-01' in done_articles[type][lds][source]:
		# print("{} March articles found".format(len(done_articles['journal-article']['EBSCO EDS']['Emerald']['2018-03-01'])))
doi_count = 0
for type in done_articles:
	for lds in done_articles[type]:
		for source in done_articles[type][lds]:
			for date in done_articles[type][lds][source]:
				for doi in done_articles[type][lds][source][date]:
					doi_count += 1
print("{} DOIs found in report dump".format(doi_count))

search_terms_list = [
	"Editorial boards accounting journals gender diversity internationalisation Dhanani",
	"Deposition time effects structure corrosion resistance duplex MAO coatings AZ31B alloy Cui",
	"relevance global sector influence African sector portfolios Boamah",
	"Moderating role productivity diversified conglomerates performance case Malaysia Gyan",
	"Disclosure public-private partnership PPP voluntary information Musawa",
	"Foreword special section Arts Heritage Cultural Management Pombo",
	"Intuition mood investors financial markets Braga",
	"Senior consumers risk benefit trade-off functional foods Ravoniarison",
	"Food expenditure patterns preferences policy access Rwandan households Weatherspoon",
	"benchmarking use toolkit mass customization automobile industry Fettermann",
	"Benchmarking project management dimensions lapse century Case Panama Canal Palm Diera Island Mega Projects Sandhu",
	"Let stop trying sexy preparing managers big data-driven business era Carillo",
	"bibliographic study big data concepts trends challenges Mishra",
	"Corporate Governance Codes Eurasian Economic Union Countries Comparative Investigation Nizaeva",
	"effects organizational isomorphism innovation performance through knowledge search industrial cluster Zhang",
	"outside directors matter impact prestigious CEOs firm performance Zhang",
	"How emergent strategy influences institution qualitative study private firm China Zhao",
	"Current thinking cluster theory its translation economic geography strategic operations management reconciliation possible Manzini",
	"Analysis circuit implementation applications novel chaotic system Xiong",
	"Atlas Vulnerability Resilience Atlas Verwundbarkeit und ResilienzAtlas Vulnerability Resilience Atlas Verwundbarkeit und Resilienz Edited Fekete Hufschmidt TH Köln Universität Bonn 2016 173pp Pigeon",
	"integrative approach understand vulnerability resilience post-disaster Rey",
	"Forensic investigation 2011 Great East Japan Earthquake Tsunami disaster Nakasu",
	"Repurchase decision music products Taiwan physical versus online media Wu",
	"near-optimal deadlock control class generalized petri nets using reachability graph Hou",
	"Fast multipole cell-based domain integration method treatment volume potentials 3D elasticity problems Wang",
	"Application computational fluid dynamics predict hydrodynamic downpull high head gates Koken",
	"Explicit dynamic analysis sheet metal forming processes using linear prismatic hexahedral solid shell elements WANG",
	"Wave sensitivity analysis periodic arbitrarily complex composite structures Chronopoulos",
	"Fatigue crack growth prediction 7075 aluminum alloy based GMSVR model optimized artificial bee colony algorithm Yang",
	"hybrid SD-DEMATEL approach develop delay model construction projects Parchamijalal",
	"How much when innovate Anning-Dorson",
]

s = requests.Session()
r = s.get('http://search.ebscohost.com/login.aspx?authtype=uid')
for c in r.cookies:
	print("Cookie: {}".format(c))
tree = html.fromstring(r.content)

viewstate = tree.xpath('//input[@name="__VIEWSTATE"]/@value')[0]
validation = tree.xpath('//input[@name="__EVENTVALIDATION"]/@value')[0]

form_data = {
	'__VIEWSTATE': viewstate, 
	'__EVENTVALIDATION': validation, 
	'user': 'edsemerald', 
	'password': 'A!S@D3F$', 
	'FormSubmit': 'true', 
	'loginUI:btnLogin': 'Login', 
	'authtype': 'uid'}
r = s.post('http://search.ebscohost.com/login.aspx?authtype=uid', data=form_data)

for c in r.cookies:
	print("Cookie: {}".format(c))
tree = html.fromstring(r.content)
form_urls = tree.xpath('//a[@class="profileBodyBold"]/@href')
viewstate = tree.xpath('//input[@name="__VIEWSTATE"]/@value')[0]
validation = tree.xpath('//input[@name="__EVENTVALIDATION"]/@value')[0]
previous_page = tree.xpath('//input[@name="__PREVIOUSPAGE"]/@value')[0]

# for u in form_urls:
	# print(u)
	
js_params = re.findall(r'"(.*?)",\s',form_urls[1])

# for p in js_params:
	# print(p)

form_data = {
	'__VIEWSTATE': viewstate, 
	'__EVENTVALIDATION': validation, 
	'__PREVIOUSPAGE': previous_page, 
	'eventTarget': js_params[0],
	'eventArgument': ''
}

form_action = js_params[3]
r = s.post('http://search.ebscohost.com/Community.aspx' + form_action)

tree = html.fromstring(r.content)
js = tree.xpath('//script[not(@src)]/text()')[0]

redirect = re.search(r'replace\(\'([^\']+)', js)
params = re.search(r'eds/search/basic?(.+)', redirect[1])
url_params = params[1]
url = 'http://eds.a.ebscohost.com/eds/search/advanced' + url_params
r = s.get(url)
tree = html.fromstring(r.content)
field_names = tree.xpath('//input[@type="hidden"]/@name')
field_values = []
form_data = {}
for name in field_names:
	form_data[name] = tree.xpath('//input[@name="' + name + '"]/@value')[0]

def process_items(search_terms):
	global url_params
	global content_type
	global done_articles
	article_counts = {}
	article_counts['count'] = 0
	article_counts['finds'] = 0
	article_counts['links'] = 0
	for date in search_terms:
		if len(search_terms[date]['dois']) != len(search_terms[date]['terms']):
			print("Don't have same numbers of DOIs ({}) and terms ({})".format(len(search_terms[date]['dois']), len(search_terms[date]['terms'])))
		for i in range(0,len(search_terms[date]['dois'])):
		# for term in search_terms:
			term = search_terms[date]['terms'][i]
			doi = search_terms[date]['dois'][i]
			art_done = 0
			article_counts['count'] += 1
			for source in done_articles[content_type]['EBSCO EDS']:
				if art_done:
					continue
				if date in done_articles[content_type]['EBSCO EDS'][source]:
					# print("{} found in done_articles".format(date))
					if doi in done_articles[content_type]['EBSCO EDS'][source][date]:
						# print("{} found in done_articles".format(doi))
						if done_articles[content_type]['EBSCO EDS'][source][date][doi] == 1:
							# print("Already found this one before: {}, {}".format(doi, term))
							art_done = 1
							article_counts['finds'] += 1
			if art_done:
				continue
			# print("Haven't found this one before: {}, {}".format(doi, term))
			words = term.split()
			if len(words) > 8:
				# print("Term too long: {}".format(term))
				term = ""
				for i in range(0, 5):
					term = term + " {}".format(words[i])
				term = term + " {}".format(words[-1])
				# print("Term now: {}".format(term))
			print("Searching for {}                                ".format(term), end='\r')
			form_data['GuidedSearchFormData.Index'] = 1
			form_data['GuidedSearchFormData[1].SearchTerm'] = term
			form_data['GuidedSearchFormData[1].DbTag'] = '' # 'TX'
			url = 'http://eds.a.ebscohost.com/eds/search/PerformSearch' + url_params# + '&bquery=(TX({}))'.format(term.replace(' ', '+AND+'))
			# print(url)
			r = s.post(url, data=form_data)
			found = 0
			tree = html.fromstring(r.content)
			title = tree.xpath('//head/title/text()')
			# print("\tTitle: {}".format(title))
			if not re.search(r'Basic search', title[0]):
				results = tree.xpath('//div[@class="result-list-record"]/h3/a')
				links = tree.xpath('//div[@class="result-list-record"]/div[@class="display-info"]/div[@class="record-formats-wrapper externalLinks"]/span[@class="custom-link"]/a/@href')
				
				while len(links) < len(results):
					print("Links: {}, Results: {}",format(len(links), len(results)))
					links.append('')
				for name in field_names:
					form_data[name] = tree.xpath('//input[@name="' + name + '"]/@value')[0]
					# print(name, tree.xpath('//input[@name="' + name + '"]/@value')[0])
				if '__sid' in form_data and '__vid' in form_data:
					url_params = "?sid={}&vid={}".format(form_data['__sid'], form_data['__vid'])
				accession_numbers = tree.xpath('//div[@class="result-list-record"]/em/@data-hoverpreviewjson') #@data-hoverPreviewJson
				if len(accession_numbers) == 0:
					records = tree.xpath('//div[@class="result-list-record"]')
					# for record in records:
						# print(record)
						# for child in record.iter():
							# print("\t", child)
							# for k in child.keys():
								# print("\t\t", k)
					accession_numbers = tree.xpath('//div[@class="result-list-record"]/div[@class="display-info"]/span[@class="record-additional"]/span[@class="item add-to-folder"]/a[@class="folder-toggle item-not-in-folder"]/@data-folder')
					# print("New accession numbers:", accession_numbers)
					
				for i in range (len(results)): #res in results:
				
					if i > (len(accession_numbers) - 1):
					# if len(accession_numbers) < len(results):
						print("Got fewer accession numbers ({}) than results ({})".format(len(accession_numbers), len(results)))
						print(results, accession_numbers)
						# with open('response.html' , 'w', encoding='utf-8') as response_file:
							# response_file.write((r.text))
						break
					
					aninfo = json.loads(accession_numbers[i])
					if aninfo['db'] == 'edsemr' or aninfo['db'] == 'edb' or aninfo['db'] == 'edo':
						conv_doi = aninfo['db'] + '.' + doi.replace('/', '.').replace('-', '.')
						link = ['']
						temp_link = unquote(unquote(unquote(links[i])))
						eds_link = ''
						if re.search(r'&su=(.+)', temp_link):
							eds_link = re.search(r'&su=(.+)', temp_link)[1]
						# print(eds_link)
						if (re.search(r'10\.[^&]+',eds_link)):
							link = re.search(r'10\.[^&]+',eds_link)
						if not 'term' in aninfo:
							aninfo['term'] = aninfo['uiTerm']
						if conv_doi == aninfo['term']:
							# print(conv_doi, aninfo['term'])
							found = 1
							article_counts['finds'] += 1
							if not date in done_articles[content_type]['EBSCO EDS']['Emerald']:
								done_articles[content_type]['EBSCO EDS']['Emerald'][date] = {}
							done_articles[content_type]['EBSCO EDS']['Emerald'][date][doi] = 1
							# break
						else:
							result_title = results[i].text_content()
							fuzz_ratio = fuzz.token_set_ratio(term, result_title)
							if fuzz_ratio >= 75:
										
								found = 1
								article_counts['finds'] += 1
								# sys.stderr.write("type:{}\t{}\t{}\t{}\t{}\t1\n".format(content_type, doi, 'EBSCO EDS', 'Emerald', date))
								if not date in done_articles[content_type]['EBSCO EDS']['Emerald']:
									done_articles[content_type]['EBSCO EDS']['Emerald'][date] = {}
								done_articles[content_type]['EBSCO EDS']['Emerald'][date][doi] = 1
								# print("\t\tResult: {} ({})\n\t\tDOI   : {}".format(result_title, fuzz_ratio, link[0], unquote(unquote(unquote(links[i]))))) # \n\t\tURL   : {}
								# break
							else:
								# print("Under ratio: {} / {}".format(result_title, fuzz_ratio))
								# with open('response.html' , 'w', encoding='utf-8') as response_file:
									# response_file.write((r.text))
								dummy_var = 1
						
						if found == 1:
							if len(link[0]) > 0:
								# print("Link found: {}".format(link[0]))
								article_counts['links'] += 1
							else:
								if 'term' in aninfo:
									# print(aninfo['term'])
									# with open('response.html' , 'w', encoding='utf-8') as response_file:
										# response_file.write((r.text))
									an_link = "http://search.ebscohost.com/login.aspx?direct=true&db={}&site=eds-live&AN={}".format(aninfo['db'], aninfo['term'])
									sys.stderr.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(term, doi, result_title, aninfo['term'], eds_link, an_link))
									# exit()
								else:
									print("No term found in aninfo")
								# print(accession_numbers)
								# if len(accession_numbers) < i:
								filename = doi.replace('.', '-').replace('/', '-') + '.html'
								with open(filename, 'w', encoding='utf-8') as response_file:
									response_file.write((r.text))
							break
					else:
						# print("False positive found, wrong database: {}".format( aninfo['db']))
						dummy_var = 1
			else:
				print("Search failed\n")
				
			if not found:
				# print("Couldn't find {} ({})".format(term, doi))
				# with open('response.html' , 'w', encoding='utf-8') as response_file:
					# response_file.write((r.text))
				# sys.stderr.write("type:{}\t{}\t{}\t{}\t{}\t0\n".format(content_type, doi, 'EBSCO EDS', 'Emerald', date))
				if not date in done_articles[content_type]['EBSCO EDS']['Emerald']:
					done_articles[content_type]['EBSCO EDS']['Emerald'][date] = {}
				done_articles[content_type]['EBSCO EDS']['Emerald'][date][doi] = 0
				
				
			time.sleep(0.5)
	return article_counts
	
content_type = ''
search_terms = {}		
for root, dirs, files in os.walk('doclists'):
	print("Processing directory: {}".format(root))
	file_count = 0
	
	for file in files:
		if re.search(r'_id', file):
			continue
		if not file.startswith('2018'):
			continue
		file_elements = re.search(r'(\d{4}-\d{2}-\d{2})_([^_.]+)', file)
		file_date = file_elements[1]
		content_type = file_elements[2]
		# print(file, file_date, content_type)
		if not content_type in content_types:
			continue
		if not file_date in search_terms:
			search_terms[file_date] = {}
			search_terms[file_date]['dois'] = []
			search_terms[file_date]['terms'] = []
		if re.search(r'_doi', file):
			with open(os.path.join(root, file), 'r', encoding='utf-8') as title_list:
				print ("Processing {}".format(file))
				row_count = 0
				temp_term = ''
				for row in csv.reader(title_list):
					if len(row) == 1:
						search_terms[file_date]['dois'].append(row[0])
					else:
						print(row, len(row))
			article_counts = process_items(search_terms)
			search_terms.clear()
			print('')
			print("\t{} articles checked\n\t{} articles found\n\t{} links found".format(article_counts['count'], article_counts['finds'], article_counts['links']))

		elif not re.search(r'_doi|_id', file):
			with open(os.path.join(root, file), 'r', encoding='utf-8') as title_list:
				print ("Processing {}".format(file))
				row_count = 0
				temp_term = ''
				for row in csv.reader(title_list):
					row_count += 1
					if row_count % 4 == 1:
						temp_term = row[0]
					if not row_count % 4 == 0:
						continue
					if len(row) == 1:
						term = row[0]
					else:
						term = temp_term
					search_terms[file_date]['terms'].append(term)

with open ('report_dump.txt' , 'w', encoding='utf-8') as report_dump:
	for type in done_articles:
		for lds in done_articles[type]:
			for source in done_articles[type][lds]:
				for date in done_articles[type][lds][source]:
					for doi in done_articles[type][lds][source][date]:
						report_dump.write("\t".join(["type:" + type, doi, lds, source, date, str(done_articles[type][lds][source][date][doi])]) + "\n")