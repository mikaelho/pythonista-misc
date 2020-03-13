#coding: utf-8

import requests, bs4
import notification

r = requests.get('http://www.tilannehuone.fi/halytys.php')

soup = bs4.BeautifulSoup(r.content.decode('utf-8','ignore'), 'html.parser')

table = soup.findChild('table', {'class': 'halytyslista'})

alerts = []
active_alert = None

class Alert:
    
    def __init__(self, kunta, aika, lyhyt_kuvaus):
        self.kunta = kunta
        self.aika = aika
        self.lyhyt_kuvaus = lyhyt_kuvaus
        self.kuvaus = ''
        
    def add_detail(self, kuvaus):
        self.kuvaus += kuvaus + '\n'

for tr in table.find_all('tr'):

    if 'halytys' in tr.get('class', []):
        kunta = tr.findChild('td', {'class': 'kunta'})
        if kunta.text.strip() in ('Espoo','Helsinki','Vantaa','Kirkkonummi'):
            aika = tr.findChild('td', {'class': 'pvm'})
            lyhyt_kuvaus = aika.find_next('td').text
            active_alert = Alert(kunta.text, aika.text, lyhyt_kuvaus)
            alerts.append(active_alert)
        else:
            active_alert = None
    elif active_alert is not None:
        tarkemmat = tr.findChildren('td')
        for tarkempi_kuvaus in tarkemmat:
            for osa in tarkempi_kuvaus.strings:
                if osa != '':
                    kuvaus = osa.replace('<br/>','\n')
                    active_alert.add_detail(kuvaus)
            for link in tarkempi_kuvaus.findChildren('a'):
                href = link['href']
                if href.startswith('tehtava.php'):
                    active_alert.add_detail('http://www.tilannehuone.fi/'+href)
    else:
        active_alert = None
        
for alert in alerts[::-1]:
    print('-'*20)
    print(alert.kunta, alert.aika)
    print(alert.lyhyt_kuvaus)
    print()
    if alert.kuvaus != '':
        print(alert.kuvaus)
        print()
