from urllib.parse import quote_plus, unquote
import time
import requests
import sys
import re

urls = {}
urls['Summon'] = [
	"https://qut.summon.serialssolutions.com/api/search?ho=f&q=",
	"http://uwe.summon.serialssolutions.com/api/search?ho=f&q=",
	"http://herts.summon.serialssolutions.com/api/search?ho=f&q=",
	"http://liberty.summon.serialssolutions.com/api/search?ho=f&q=",
	"https://american.summon.serialssolutions.com/api/search?ho=f&q=",
	]
urls['Primo'] = [
	"http://discover.durham.ac.uk/primo_library/libweb/action/search.do?fn=search&ct=search&initialSearch=true&mode=Basic&tab=default_tab&indx=1&dum=true&srt=rank&vid=44DUR_VU1&frbg=&vl%28freeText0%29=",
	"https://iluplus.hosted.exlibrisgroup.com/primo-explore/search?tab=default_tab&search_scope=institution_scope&vid=41ZBL&lang=en_US&offset=0&query=any,contains,",
	"https://west-sydney-primo.hosted.exlibrisgroup.com/primo-explore/search?tab=default_tab&search_scope=default_scope&vid=UWS-ALMA&lang=en_US&offset=0&sortby=rank&pcAvailability=true&query=any,contains,",
	"https://www.librarysearch.manchester.ac.uk/discovery/search?tab=Everything&search_scope=MyInst_and_CI&vid=44MAN_INST:MU_NUI&lang=en&offset=0&pcAvailability=true&query=any,contains,",
	"https://cmich-primo.hosted.exlibrisgroup.com/primo-explore/search?tab=everything&search_scope=EVERYTHING&pcAvailability=true&sortby=rank&vid=01CMICH&query=any,contains,",
]
urls['WorldCat'] = [
	"https://adu.on.worldcat.org/search?databaseList=4096,4098,4077,4079,4135,3684,2375,2572,2175,3284,2328,1875,1697,2268,3313,2267,3978,3879,2264,2263,2262,3197,1271,2261,283,2260,2281,3404,1842,2237,2259,3201,4015,1708,4017,3867&page=1&queryType=search&stickyFacetsChecked=false&queryString=",
	"http://mcgill.worldcat.org/search?scope=0&q=",
	"http://pepperdine.worldcat.org/search?scope=0&q=",
	"https://emporiastate.on.worldcat.org/search?scope=&sortKey=BEST_MATCH&queryString=",
]

art_title = "Bridging the gap between theory and practice in management accounting"
query = "Bridging gap between theory practice management accounting Jansen"
doi = '10.1108/AAAJ-10-2015-2261'

from selenium import webdriver

driver = webdriver.PhantomJS(executable_path="C:\\Users\\Mike\\AppData\\Roaming\\npm\\node_modules\\phantomjs-prebuilt\\lib\\phantom\\bin\\phantomjs")
driver.set_window_size(1024, 768)

s = requests.Session()

for lds in urls:
	print("Checking {}".format(lds))
	for url in urls[lds]:
		found = 0
		# print(url)
		# sys.stderr.write(url + quote_plus(query) + "\n")
		print(url + quote_plus(query))
		if not lds == 'Primo':
			r = s.get("".join([url, quote_plus(query)]))
			# for h in r.history:
				# print("Redirected: ", h.url)
			# for c in r.cookies:
				# print("Cookie: ", c)
			content = unquote(r.text)
			if re.search(doi, content):
				print("Requests: Article DOI found")
				found = 1
			elif re.search(art_title, content):
				print("Requests: Article title found")
				found = 1
			else:
				print("Requests: Article not found: ", r.status_code)
		if not found:
			driver.get("".join([url, quote_plus(query)]))
			for i in range(5):
				time.sleep(1)
				# driver.save_screenshot('screen.png')
				page_html = driver.find_element_by_tag_name('html').get_attribute('innerHTML')
				# with open ('response.html', 'w', encoding='utf-8') as html_file:
					# html_file.write(page_html)
				content = unquote(page_html)
				if re.search(doi, content):
					print("Driver: Article DOI found after pause {}".format(i+1))
					found = 1
					break
				elif re.search(art_title, content):
					print("Driver: Article title found after pause {}".format(i+1))
					found = 1
					break
				# else:
					# print("Driver: Article not found after pause {}".format(i+1))
		if not (found == 1):
			print("Article not found")
			sys.stderr.write(url + "\n")
		else:
			break
driver.close()
