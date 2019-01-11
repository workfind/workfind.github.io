#9 jan 2019

# Library declarations
import requests
from datetime import datetime, timedelta
import json
import io
import csv
import xml.etree.ElementTree as ET
import pandas as pd
import sys
import numpy as np
from scipy import stats

# Extract data from content
def get_currentweatherrss(aparam):
	a = {}

	acontent = aparam["response"]
	aparser = ET.XMLParser(encoding="utf-8")
	aroot = ET.fromstring(acontent,parser=aparser)
	acdata = ""
	for aitem in aroot.iter('item'):
		for atemp in aitem.findall('description'):
			acdata = atemp.text.encode('utf-8')
		if type(acdata) is not str:
			acdata = str(acdata)
		break

	acontent = acdata
	acontent = acontent[acontent.find("<table "):]
	acontent = acontent[:acontent.find("</table>")]
	acontent.strip()
	acontent = acontent+"</table>"

	aroot = ET.fromstring(acontent)

	a.update({'url':aparam["url"]})
	a.update({'date':aparam["date"]})
	a.update({'time':aparam["time"]})
	for aitem in aroot.iter('tr'):
		acount = 0
		akey = ""
		avalue = ""
		for atemp in aitem.findall('td'):
			if (acount == 0):
				akey = str("".join(atemp.itertext()).encode('utf-8').decode('utf-8'))
			if (acount != 0):
				avalue = int("".join(atemp.itertext()).encode('utf-8').decode('utf-8').split(" ")[0])
			acount = acount + 1
		a.update({akey:avalue})

	return a

# Reusable common function
def get_rowskeys(aparam):
	akeys = {}

	arows = aparam["rows"]

	for i in range(0,len(arows)):
		try:
			for akey in arows[i].keys():
				akeys.update({akey:akey})
		except Exception as e:
			print(""+str(e))

	return akeys

# Data analysis
def set_analyse(aparam):

	a = []

	arows = aparam["rows"]
	akeys = get_rowskeys({"rows":arows})

	aio = io.BytesIO()
	awriter = csv.writer(aio, quoting=csv.QUOTE_ALL)
	awriter.writerow(akeys.keys())

	for i in range(0,len(arows)):
		arow = []
		for akey in akeys:
			avalue = arows[i].get(akey,"")
			if avalue is None:
				avalue = ""
			arow.append(avalue)

		awriter.writerow(arow)

	astr = aio.getvalue()
	aio.close()
	astr = astr.rstrip()
	df = pd.read_csv(io.BytesIO(astr),encoding='utf-8',sep=',',quoting=csv.QUOTE_ALL)

	df.dropna()
	atemp = pd.DataFrame({'Normalised_Daytime':((df['time']>="06:15:00") & (df['time']<"18:15:00"))},index=list(range(0,len(df.index))))
	atemp["Normalised_Daytime"] = atemp["Normalised_Daytime"].astype('category')
	df = pd.concat([df,atemp],axis=1)

	df = df.drop(columns=['url', 'date', 'time'])

	adaytime = df[(df['Normalised_Daytime']==True)].astype('float')
	anondaytime = df[(df['Normalised_Daytime']!=True)].astype('float')
	print("\nRegional temperature average(mean - Daytime):\n{}\n".format(adaytime.describe(include=[np.number],exclude=['category'])))
	print("\nRegional temperature average(mean - Non-daytime):\n{}\n".format(anondaytime.describe(include=[np.number],exclude=['category'])))

	stats.describe(adaytime)
	stats.describe(anondaytime)

# Data snapshots presented in structured data form for data analysis
def get_formattedrows(aparam):

	a = []

	arows = aparam["rows"]
	akeys = get_rowskeys({"rows":arows})

	a = []
	for i in range(0,len(arows)):
		arow = {}
		try:
			for akey in akeys:
				avalue = arows[i].get(akey,"")
				if avalue is None:
					avalue = ""
				arow.update({akey:avalue})
		except Exception as e:
			print(""+str(e))

		if arow != {}:
			a = a+[arow]

	return a

# Fetch data by date
def get_start():

	if (len(sys.argv) < 2):
		print("Usage: {} 'YYYYmmdd'".format(sys.argv[0]))
		sys.exit()

	ayesterday = datetime.today() - timedelta(days=1)
	adatetime = ayesterday
	adatetime = datetime.strptime(sys.argv[1], '%Y%m%d')

	a = []
	amax = 24
	for i in range(0,amax):
		aurl = 'https://api.data.gov.hk/v1/historical-archive/get-file?url=http%3A%2F%2Frss.weather.gov.hk%2Frss%2FCurrentWeather.xml&time={}{:02}{:02}-{:02}15'.format(adatetime.year, adatetime.month, adatetime.day, i)
		r = requests.get(aurl)

		arow = []
		try:
			arow = get_currentweatherrss({"url":aurl, 'date':"{}".format(adatetime.strftime("%Y-%m-%d")),'time':"{:02}:15:00".format(i), "response":r.text})
		except Exception as e:
			print(str(e))
		a.append(arow)

	a = get_formattedrows({'rows':a})
	set_analyse({'rows':a})

# Data format from feed
def get_sample():
	afeed = 'view-source:https://api.data.gov.hk/v1/historical-archive/get-file?url=http%3A%2F%2Frss.weather.gov.hk%2Frss%2FCurrentWeather.xml&time=20190109-0015'
	s=u"""
<?xml version="1.0" encoding="utf-8"?><?xml-stylesheet href="current.xsl" type="text/xsl" ?><rss version="2.0">
  <channel>
    <title>Current Weather</title>
    <link>
    http://www.weather.gov.hk/wxinfo/currwx/current.htm</link>
    <description>Current Weather</description>
    <language>en-us</language>
    <copyright>The content available in this file, including but
    not limited to all text, graphics, drawings, diagrams,
    photographs and compilation of data or other materials are
    protected by copyright. The Government of the Hong Kong Special
    Administrative Region is the owner of all copyright works
    contained in this website.</copyright>
    <image>
      <title>Current Weather</title>
      <link>http://www.weather.gov.hk/wxinfo/currwx/current.htm</link>
	  <url>http://rss.weather.gov.hk/img/HKOlogo.gif</url>
      <width>144</width>
      <height>28</height>
    </image>
    <item>
       <author>hkowm@hko.gov.hk</author>
	  <guid isPermaLink="false">
      http://rss.weather.gov.hk/rss/CurrentWeather/20190109000200</guid>
<pubDate>Tue, 08 Jan 2019 16:02:00 GMT</pubDate>      <title>Bulletin updated at 00:02 HKT 09/01/2019</title>
      <category>R</category>
      <link>
      http://www.weather.gov.hk/wxinfo/currwx/current.htm</link>
        <description>
        <![CDATA[
         <img src="http://rss.weather.gov.hk/img/pic60.png" style="vertical-align: middle;">        <p>At 
        midnight 
               at the Hong Kong Observatory :<br/>
        Air temperature : 17 degrees Celsius<br/>
        Relative Humidity : 91 per cent<br/>
		 										    																											<p></p>
                The air temperatures at other places were:
                <br/>
                <font size="-1">
    <table border="0" cellspacing="0" cellpadding="0">
    <tr><td><font size="-1">Hong Kong Observatory</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">King's Park</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Wong Chuk Hang</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Ta Kwu Ling</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Lau Fau Shan</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tai Po</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Sha Tin</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tuen Mun</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tseung Kwan O</font></td><td width="100" align="right"><font size="-1">16 degrees ;</font></td></tr>
    <tr><td><font size="-1">Sai Kung</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Cheung Chau</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Chek Lap Kok</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tsing Yi</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Shek Kong</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tsuen Wan Ho Koon</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tsuen Wan Shing Mun Valley</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Hong Kong Park</font></td><td width="100" align="right"><font size="-1">16 degrees ;</font></td></tr>
    <tr><td><font size="-1">Shau Kei Wan</font></td><td width="100" align="right"><font size="-1">16 degrees ;</font></td></tr>
    <tr><td><font size="-1">Kowloon City</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Happy Valley</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Stanley</font></td><td width="100" align="right"><font size="-1">16 degrees ;</font></td></tr>
    <tr><td><font size="-1">Kwun Tong</font></td><td width="100" align="right"><font size="-1">16 degrees ;</font></td></tr>
    <tr><td><font size="-1">Sham Shui Po</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Kai Tak Runway Park</font></td><td width="100" align="right"><font size="-1">17 degrees ;</font></td></tr>
    <tr><td><font size="-1">Yuen Long Park</font></td><td width="100" align="right"><font size="-1">18 degrees ;</font></td></tr>
    <tr><td><font size="-1">Tai Mei Tuk</font></td><td width="100" align="right"><font size="-1">17 degrees .</font></td></tr>
    </table></font></p>
Between 10:45 and 11:45 p.m., the rainfall recorded in various regions were:<br/><br/>    <table border="0" cellspacing="0" cellpadding="0">
                <tr><td>Eastern District</td><td width="100" align="right">0 to 1&nbsp;mm;</td></tr>
            <tr><td>Sai Kung</td><td width="100" align="right">0 to 1&nbsp;mm.</td></tr>
        </table><br/>
        ]]>
        </description>
    </item>
  </channel>
</rss>
"""
	return s

# Kickstart main routine
get_start()
