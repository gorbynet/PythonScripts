import csv
import os
import numpy as np
import matplotlib.pyplot as plt



os.chdir(os.path.join("..", 'db_reports'))
file_count = 0
line_params = ['ro-', 'k+-', 'bd-', 'gx-', 'y^-']
for filename in os.listdir(os.curdir):
	if filename.endswith(".txt"):
		with open (filename, 'r', encoding='utf-8') as raw_data:
			graph_name = filename[11:-4].replace("_", " ")
			graph_image_name = filename[:-4].replace(" ", "_")
			row_count = 0
			file_count += 1
			reader = csv.reader(raw_data, dialect='excel-tab')
			dates = [] # np.array([]).astype(np.float)
			row_name = ''
			data_name = ''
			for row in reader:
				data = []
				row_count += 1
				# print("\t".join([str(row_count), str(len(row)) ]))
				if row_count == 1:
					row_name = row[0]
					for i in range(1,len(row)):
						dates.append(row[i])
						# np.append(dates, row[i])
				else:
					data_name = row[0]
					for i in range(1,len(row)):
						data.append(row[i])
						# np.append(data, row[i])
					print('\t'.join([filename, str(file_count), str(row_count), row_name, data_name]))
					# s1mask = np.isfinite(data)
					# [s1mask]
					plt.plot(data, line_params[(row_count - 2)], label=data_name)
			x = np.arange(0,len(dates))
			plt.xticks(x, dates)
			plt.legend()
			plt.title(graph_name + ": % coverage")
			plt.xlabel("Months since publication")
			plt.ylabel("Percent coverage")
			plt.ylim(0,105)
			plt.yticks(range(0,110,10))
			plt.draw()
			fig = plt.gcf()
			if not os.path.exists(os.path.join("..", "db", "images")):
				if not os.path.exists(os.path.join("..", "db")):
					os.mkdir(os.path.join("..", "db"))
				os.mkdir(os.path.join("..", "db", "images"))
			fig.savefig(os.path.join("..", "db", "images", graph_image_name + '.png'), bbox_border='tight')
			plt.clf()
exit(0)	
