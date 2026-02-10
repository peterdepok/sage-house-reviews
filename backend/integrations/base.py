from abc import ABC, abstractmethod

class PlacementPlatform(ABC):
    @abstractmethod
    def get_listing(self):
        pass

    @abstractmethod
    def update_listing(self, data):
        pass

    @abstractmethod
    def get_inquiries(self):
        pass

    @abstractmethod
    def respond_to_inquiry(self, inquiry_id, message):
        pass
