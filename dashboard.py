#coding: utf-8

from dashboard_conf import *
from ui import *
from objc_util import *
from anchor import *
from unsync import unsync
import concurrent.futures as cf
import math, sys, json, requests, time, threading
from urllib.parse import urlsplit
from functools import partial
from types import SimpleNamespace as NS
from threadbare import threadbare

import carnet

class Dashboard(ui.View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        enable(self)
        self.active = True
        self.session = requests.Session()
        self.heating_now = None

        self.grid_view = GridView(
          frame=self.bounds,
          flex='WH',
          pack=GridView.CENTER)
        self.add_subview(self.grid_view)
        self.grid_view.dock.all()
        self.create_cards()

        refresh = self.refresh_indicator = ImageView(
          image=Image('iow:ios7_refresh_empty_256'),
          hidden=True)
        self.add_subview(self.refresh_indicator)
        refresh.dock.top_trailing()
        refresh.at.width == 20
        refresh.at.height == refresh.at.width
        self.token = None
        self.display_odometer = True
        self.odometer_values = None

        heating = self.heating_request_indicator = ImageView(
          image=Image('iow:social_rss_outline_256'),
          hidden=True)
        self.add_subview(self.heating_request_indicator)
        heating.dock.bottom_trailing()
        heating.align.width(refresh)
        heating.align.height(refresh)

    def create_cards(self):
        self.temperature = self.create_card('Lämpötila °C')
        self.forecast = self.create_card('Ennuste °C')
        self.odometer = self.create_card(
          'Matka km',
          action=self.toggle_odometer)
        self.range = self.create_card('Kantama KM')
        self.power_available = self.create_card('Latausjohto')
        self.charge_level = self.create_card('Varaus')
        self.doors = self.create_card('Lukitus')
        self.heating = self.create_card('Lämmitys', action=self.start_heating_by_click)

    def create_card(self, title, image=False, action=None):
        if not action:
            card = View()
        else:
            card = Button()
            card.action = action
        card.background_color = '#6b95ff'
        self.grid_view.add_subview(card)
        title_view = Label(
          name='title',
          text=title.upper(),
          text_color='white',
          font=('Futura', 10),
          number_of_lines=0)
        card.add_subview(title_view)
        title_view.dock.bottom_trailing()
        if image:
            content_view = ImageView(name='content', image=Image('iow:more_256'),
            hidden=True,
            number_of_lines=0,
            )
            share=.3
        else:
            content_view = Label(
              name='content',
              text='...',
              text_color='white',
              font=('Futura', 32),
              alignment=ALIGN_CENTER,
              hidden=True)
            share=.9
        card.add_subview(content_view)
        content_view.align.center_x(card)
        content_view.at.center_y == card.at.center_y * 1.25
        content_view.at.width == card.at.width * share
        '''
        placeholder = ImageView(
          name='placeholder',
          image=Image('iow:more_256'))
        card.add_subview(placeholder)
        C(placeholder).dock_center(share=.3)
        '''
        return card

    @on_main_thread
    def reveal(self, card, text=None, image=None, title=None):
        content = card['content']
        if text:
            content.text = text
        elif image:
            content.image = Image(image)
        if title:
            card['title'].text = title.upper()
        content.hidden = False
        card.background_color = '#6b95ff'
        #card['placeholder'].hidden = True

    icon_map = {
      'clear-day': 'iow:ios7_sunny_outline_256',
      'clear-night': 'iow:ios7_moon_outline_256',
      'rain': 'iow:ios7_rainy_outline_256',
      'snow': 'iow:ios7_rainy_256',
      'sleet': 'iow:ios7_rainy_outline_256',
      'wind': 'iow:ios7_rewind_outline_256',
      'fog': 'iow:drag_256',
      'cloudy': 'iow:ios7_cloud_outline_256',
      'partly-cloudy-day': 'iow:ios7_partlysunny_256',
      'partly-cloudy-night': 'iow:ios7_partlysunny_outline_256'
    }

    @threadbare
    def main(self):
        self.request_forecast()
        self.carnet_login()
        yield
        while self.active:
            self.refresh_indicator.hidden = False
            self.get_emanager_status()
            self.get_vehicle_status()
            self.refresh_indicator.hidden = True
            time.sleep(5)

    def request_forecast(self):
        try:
            key = darksky_conf['api_key']
            latitude = darksky_conf['latitude']
            longitude = darksky_conf['longitude']
            url = f'https://api.darksky.net/forecast/{key}/{latitude},{longitude}?units=si'
            result = requests.get(url)
            self.show_forecast(result.json())
        except Exception as e:
            print('Retrieving forecast')
            print(e)

    @on_main_thread
    def show_forecast(self, data):
        today = data['daily']['data'][0]
        low = round(today['temperatureLow'])
        high = round(today['temperatureHigh'])
        icon_name = today['icon']

        self.reveal(self.forecast, text=f'{low}/{high}')

        weather_icon = ImageView(
          name='icon', image=Image(self.icon_map.get(icon_name, 'iow:ios7_close_outline_256')),
          hidden=True)
        self.forecast.add_subview(weather_icon)
        weather_icon.dock.top_leading(share=.35)
        weather_icon.hidden = False

    def carnet_login(self):
        self.url, msg = carnet.CarNetLogin(
            self.session, 
            CARNET_USERNAME, CARNET_PASSWORD)
        if self.url == '':
            print('Failed to login', msg)

    @in_background
    def get_car_data(self):
        while self.active:
            self.refresh_indicator.hidden = False
            self.get_emanager_status()
            self.get_vehicle_status()
            self.refresh_indicator.hidden = True
            time.sleep(5)
            
    def will_close(self):
        self.active = False
        self.carnet_logout()
        
    @in_background
    def carnet_logout(self):
        command = '/-/logout/revoke'
        r = self.session.post(
            self.url + command, 
            headers=carnet.request_headers)

    def get_emanager_status(self):
        command = '/-/emanager/get-emanager'
        r = self.session.post(
            self.url + command, 
            headers=carnet.request_headers)
        data = r.json()
        status_data = data['EManager']['rbc']['status']
        climate_data = data['EManager']['rpc']['status']
        
        self.reveal(self.doors,
            'OK'
            if status_data['lockState'] == 'LOCKED'
            else 'AUKI')
        self.reveal(self.charge_level,
            str(status_data['batteryPercentage'])+'%')
        self.reveal(self.power_available, 
            'OK'
            if status_data['extPowerSupplyState'] == 'AVAILABLE'
            else 'IRTI')
        self.reveal(self.range,
            str(status_data['electricRange']))
            
        self.heating_now = not(
            climate_data['climatisationState'] == 'OFF')
        self.reveal(self.heating,     
            'PÄÄLLÄ' if self.heating_now
            else 'EI')
            
    def get_vehicle_status(self):        
        command = '/-/vehicle-info/get-vehicle-details'
        r = self.session.post(
            self.url + command, 
            headers=carnet.request_headers)
        data = r.json()
        vehicle_data = data['vehicleDetails']

        mileage = vehicle_data['distanceCovered'].replace('.', '')
        service_components = vehicle_data['serviceInspectionData'].split()
        service_in_days = service_components[0]
        service_in_km = service_components[3].replace('.', '')
        
        self.odometer_values = NS(
          mileage=mileage,
          service_in_km=service_in_km,
          service_in_days=service_in_days
        )

        self.reveal(
          self.odometer,
          f'{mileage}', title='Matka km')
        self.display_odometer = True

    def toggle_heating(self):
        self.heating_now = self.heating_now == False
        post_data = {
            'triggerAction': self.heating_now,
            'electricClima': True
        }
        command = '/-/emanager/trigger-climatisation'
        r = self.session.post(
            self.url + command, post_data,
            headers=carnet.request_headers)

    '''
    def stop_heating(self):
        post_data = {
            'triggerAction': False,
            'electricClima': True
        }
        command = '/-/emanager/trigger-climatisation'
        r = self.session.post(
            self.url + command, post_data,
            headers=carnet.request_headers)
    '''

    def start_heating_by_click(self, sender):
        if self.heating_now is None:
            return
        self.heating.background_color = 'red'
        #self.heating_request_indicator.hidden = False
        self.toggle_heating()
        #self.heating_request_indicator.hidden = True

    def toggle_odometer(self, sender):
        if self.odometer_values is None: return
        self.display_odometer = self.display_odometer == False
        ov = self.odometer_values
        if self.display_odometer:
            self.reveal(self.odometer,
            f'{ov.mileage}', title='Matka km')
        else:
            self.reveal(self.odometer, f'{ov.service_in_km}\n{ov.service_in_days}', title='Huolto km, pv')

    def connectivity_issue(self, exception):
        pass


v = Dashboard(background_color='black')
v.present('full_screen', hide_title_bar=True)

with cf.ThreadPoolExecutor() as e:
    futures = set()
    futures.add(e.submit(v.request_forecast))
    futures.add(e.submit(v.carnet_login))
    for f in cf.as_completed(futures):
        f.result()

v.get_car_data()

if len(sys.argv) == 2 and sys.argv[1] == 'warmup':
    v.call_soon(v.start_heating())
#v.start_loop()

