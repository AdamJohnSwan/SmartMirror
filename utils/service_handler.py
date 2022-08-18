from typing import Dict
from utils.settings import get_settings
from services.builder import Builder
from services.screen import Screen
from actions.clock import Clock
from actions.weather import Weather
from actions.calendar import Calendar
from actions.snooze import Snooze
from actions.alarm import Alarm
from actions.voice import Voice

class Service():
    def start_service():
        """
        Abstract function used by a service to start up it resources.
        """
        pass

    def stop_service():
        """
        Abstract function used by a service to stop and dispose it resources.
        """
        pass


class ServiceHandler():
    def __init__(self):
        self.services: Dict[str, Service] = {}

    def add_service(self, service_name: str, service: Service):
        """
        Add a service to the dictioanry of services.

        :param service_name: The name of the service that will be used when stopping or retrieving the service.
        :param service: A class that extends the Service abstract class.
        """
        if (self.services.get(service_name) != None):
            raise Exception(f"Service {service_name} has already been added.")
        self.services[service_name] = service
    
    def remove_service(self, service_name):
        """
        Stops and removes a service

        :param service_name: The name of the service.
        """
        if (self.services.get(service_name) == None):
            raise Exception(f"Service {service_name} does not exist.")
        self.services[service_name].stop_service()
        self.services.pop('service_name')
    
    def initiate_services(self):
        """
        Starts all the services in the handler.
        """
        for service_name in self.services:
            self.services[service_name].start_service()

    def stop_all_services(self):
        for service_name in self.services:
            self.services[service_name].stop_service()

    def get_service(self, service_name) -> Service:
        """
        Retrieves a service.

        :param service_name: The name of the service.
        """
        if (self.services.get(service_name) == None):
            raise Exception(f"Service {service_name} does not exist.")
        return self.services[service_name]



def create_service_handler(builder) -> ServiceHandler:
    service_handler = ServiceHandler()

    service_handler.add_service('builder', Builder(service_handler, builder))
    service_handler.add_service('screen', Screen(service_handler))
    service_handler.add_service('clock', Clock(service_handler))

    service_handler.add_service('weather', Weather(service_handler))
    service_handler.add_service('calendar', Calendar(service_handler))
    service_handler.add_service('alarm', Alarm(service_handler))
    service_handler.add_service('snooze', Snooze(service_handler))
    service_handler.add_service('voice', Voice(service_handler))
    
    service_handler.initiate_services()
    
    return service_handler