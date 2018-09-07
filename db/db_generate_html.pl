use strict;

	
my $run_time = localtime;

my $dir = '../db_reports';
opendir(DIR, $dir) or die $!;
my %reports;
my %reportnames;

while (my $file = readdir(DIR)) {
	# print "Processing $file\n";
	next unless $file =~ m/\.txt/;
	print "Processing $file\n";
	my ($name) = $file =~ m/\d{4}-\d{2}-\d{2}_(.+?)\.txt/;
	$name =~ s/_/ /g;
	print "$name\n";
	$reports{$file} = $name;
	$reportnames{$name} = $file;
	
}

our @report_keys = (
	'Total',
	'Total by type',
	'EBSCO EDS',
	'Primo',
	'Summon',
	'WorldCat'
	); #sort(keys(%reports));

&generate_report_html;

sub generate_report_html {
my $reports_html;
my $report_template = <<EOTEM;
		<div class="row">
			<h3>__REPORT_NAME__</h3>
		</div>
		<div class="row">
			<div class="col-sm">
				<p><img width="100%" src="../db/images/__IMAGE_FILENAME__"/></p>
			</div>
			<div class="col-sm"><h3>Data</h3><iframe seamless='seamless' frameBorder='0' width="100%" src ="../db_reports/__DATA_FILENAME__"></iframe></div>
		</div>
		<hr>
EOTEM
my $html_template = <<EOHTML;
<html>
	<head>
		<title>LDS Audit: Content Discovery dashboard</title>
		<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
		<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/css/bootstrap.min.css" integrity="sha384-/Y6pD6FV/Vv2HJnA6t+vslU6fwYXjCFtcEpHbNJ0lyAFsXTsjBbfaDjzALeQsN6M" crossorigin="anonymous">
	</head>
	<body>
	<div class="container">
		<h1>Library Discovery Service audit</h1>
		<p>Last run: $run_time</p>

__REPORTS__
	</div>
	<script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.11.0/umd/popper.min.js" integrity="sha384-b/U6ypiBEHpOf/4+1nzFpr53nxSS+GLCkfwBdFNTxtclqqenISfwAzpKaMNFNmj4" crossorigin="anonymous"></script>
	<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/js/bootstrap.min.js" integrity="sha384-h0AbiXch4ZDo7tp9hKZ4TsHbi047NrKGLO3SEJAg45jXxnGIfYzk4Si90RDIqNm1" crossorigin="anonymous"></script>
	</body>
</html>
EOHTML
	foreach my $name (@report_keys) {
		my $report = $reportnames{$name};
		$reports_html .= $report_template;
		$reports_html =~ s/__REPORT_NAME__/$reports{$report}/;
		$reports_html =~ s/__DATA_FILENAME__/$report/;
		$report =~ s/txt$/png/;
		$reports_html =~ s/__IMAGE_FILENAME__/$report/;
	}
	my $d = $run_time;
	$html_template =~ s/__REPORTS__/$reports_html/;
	$html_template =~ s/__LAST_RUN__/$d/;
	open (my $html_fh, ">", "../db_html/dashboard.html") or die $!;
	print $html_fh $html_template;
	close $html_fh;
}


