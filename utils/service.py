class Service():
    def start_service(self):
        """
        Abstract function used by a service to start up it resources.
        """
        pass

    def stop_service(self):
        """
        Abstract function used by a service to stop and dispose it resources.
        """
        pass