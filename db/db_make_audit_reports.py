import os
import sqlite3
import datetime as dt
from dateutil.relativedelta import relativedelta

# import re

month_zero = dt.datetime(dt.datetime.now().year, dt.datetime.now().month, 1)
check_date = dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d")
months = []
print("Today's date: {}".format(str(check_date)))
print("Report dates:")
for i in range(1,7):
	target_month = dt.datetime.strftime(month_zero - relativedelta(months=i), "%Y-%m-%d")
	print(target_month)
	months.append(target_month)
	
db = sqlite3.connect('audit_results.sqlite3')
cursor = db.cursor()

total_by_type_counts = {}
total_by_service_counts = {}
type_by_service_counts = {}
	
with open ("db_audit.txt", 'w', encoding='utf-8') as report:
	cursor.execute('''SELECT pub_date, count(distinct doi) as arts_checked from audit_results group by pub_date order by pub_date''')
	pub_count = cursor.fetchall()
	report.write("{}\t{}\t{}\t{}\t{}\t{}\n".format('Date', 'Type', 'Service', 'Total', 'Found', 'Ratio'))
	for date_row in pub_count:
		
		# Total stats per month
		cursor.execute('''SELECT count(distinct doi) as arts_found from audit_results where pub_date = ? and found = 1''', (date_row[0],))
		for found_row in cursor:
			report.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(date_row[0], "Total", "All", date_row[1], found_row[0], "{:.2f}".format(found_row[0] / date_row[1])))
		
		# Service by month
		cursor.execute('''SELECT service, count(distinct doi) as arts_found from audit_results where pub_date = ? group by service''', (date_row[0],))
		services = cursor.fetchall()
		for service_row in services:
			cursor.execute('''SELECT count(distinct doi) as arts_found from audit_results where pub_date = ? and service = ? and found = 1 group by service''', (date_row[0], service_row[0],))
			for count_row in cursor:
				report.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(date_row[0], "Total", service_row[0], date_row[1], count_row[0], "{:.2f}".format(count_row[0] / date_row[1]))) # , row[2]
		
				if not service_row[0] in total_by_service_counts:
					total_by_service_counts[service_row[0]] = {}
					
				if service_row[1] > 0:
					total_by_service_counts[service_row[0]][date_row[0]] = "{:.2f}".format(100 * count_row[0] / date_row[1])
					
		# Type and service by month
		cursor.execute('''SELECT type, count(distinct doi) as arts_found from audit_results where pub_date = ? group by type''', (date_row[0],))
		types = cursor.fetchall()
		for type_row in types:
			# overall counts for type
			cursor.execute('''SELECT count(distinct doi) as arts_found from audit_results where pub_date = ? and type = ? and found = 1''', (date_row[0], type_row[0],))
			for type_found_row in cursor:
				report.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(date_row[0], type_row[0], "All", type_row[1], type_found_row[0], "{:.2f}".format(type_found_row[0] / type_row[1]))) # , row[2]

				if not type_row[0] in total_by_type_counts:
					total_by_type_counts[type_row[0]] = {}
					
				if type_row[1] > 0:
					total_by_type_counts[type_row[0]][date_row[0]] = "{:.2f}".format(100 * type_found_row[0] / type_row[1])

			# counts for type by service
			cursor.execute('''SELECT service, count(distinct doi) as arts_found from audit_results where pub_date = ? and type = ? and found = 1 group by service''', (date_row[0], type_row[0],))
			for type_service_row in cursor:
				report.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(date_row[0], type_row[0], type_service_row[0], type_row[1], type_service_row[1], "{:.2f}".format(type_service_row[1] / type_row[1]))) # , row[2]

				if not type_service_row[0] in type_by_service_counts:
					type_by_service_counts[type_service_row[0]] = {}
				if not type_row[0] in type_by_service_counts[type_service_row[0]]:
					type_by_service_counts[type_service_row[0]][type_row[0]] = {}
					
				if type_row[1] > 0:
					type_by_service_counts[type_service_row[0]][type_row[0]][date_row[0]] = "{:.2f}".format(100 * type_service_row[1] / type_row[1])
					
report_dir = os.path.join("..", "db_reports")
if not os.path.exists(report_dir):
	os.mkdir(report_dir)
	
if not os.path.exists(os.path.join(report_dir, "archive")):
	os.mkdir(os.path.join(report_dir, "archive"))

for root, dirs, files in os.walk(report_dir):
	for file in files:
		if os.path.exists(os.path.join(root, 'archive', file)):
			os.remove(os.path.join(root, 'archive', file))
		os.rename(os.path.join(root, file), os.path.join(root, 'archive', file))
	break
with open (os.path.join(report_dir, check_date +  "_Total_by_type.txt"), 'w', encoding='utf-8') as report:
	report.write("\t".join(["Type", "\t".join([str(x) for x in range(1,7)])]) + "\n")
	for content_type in total_by_type_counts:
		report.write(content_type)
		for month in months:
			if month in total_by_type_counts[content_type]:
				report.write("\t{}".format(total_by_type_counts[content_type][month]))
			else:
				report.write("\tNaN")
		report.write("\n")
		
with open (os.path.join(report_dir, check_date +  "_Total.txt"), 'w', encoding='utf-8') as report:
	report.write("\t".join(["Service", "\t".join([str(x) for x in range(1,7)])]) + "\n")
	for content_service in total_by_service_counts:
		report.write(content_service)
		for month in months:
			if month in total_by_service_counts[content_service]:
				report.write("\t{}".format(total_by_service_counts[content_service][month]))
			else:
				report.write("\tNaN")
		report.write("\n")
		
		
for service in type_by_service_counts:
	service_name = service.replace(" ", "_")
	with open (os.path.join(report_dir, "{}_{}.txt".format(check_date, service_name)), 'w', encoding='utf-8') as report:
		report.write("\t".join(["Type", "\t".join([str(x) for x in range(1,7)])]) + "\n")
		for content_type in type_by_service_counts[service]:
			report.write(content_type)
			for month in months:
				if month in type_by_service_counts[service][content_type]:
					report.write("\t{}".format(type_by_service_counts[service][content_type][month]))
				elif month in total_by_type_counts[content_type]:
					report.write("\t{}".format("{:.2f}".format(0)))
				
				else:
					report.write("\tNaN")
			report.write("\n")

		
	# Type by service reports
# for my $service (sort(keys(%services))) {
	# $os = join("\t", "Type", @month_nums) . "\n";
	# for my $type (sort(keys(%types))) {
		# $os .= $type_labels{$type};
		# for my $start_date (reverse(@dates)) {
			# $type_by_service{$start_date}{$service}{$type}
			# $os .= "\t" . sprintf("%.2f", 100 * $type_by_service{$start_date}{$service}{$type});
			# sprintf("%.2f", $proportion_found)
		# }
		# $os .= "\n";
	# }
	# $service =~ s/[^\w]/_/gs;
	# open (my $fh, ">:utf8", "reports/" . $run_time->ymd . "_" . $service . ".txt") or die $!;
	# print $fh $os;
	# close $fh;
	
	# print $os;
	# print "\n";
# }


