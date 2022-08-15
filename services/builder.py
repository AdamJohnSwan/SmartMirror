from utils.service_handler import Service
from utils.service_handler import ServiceHandler

class Builder(Service):
    def __init__(self, service_handler:ServiceHandler, builder):
       self.builder = builder
       self.service_handler = service_handler
       
    def get_object(self, object_name: str):
      self.builder.get_object(object_name)
