import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class ChenetClient:
    """
    The main entry point for ChenetDB.
    Wraps the standard PyMongo client to add graph capabilities.
    """
    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        self.connection_string = connection_string
        self._mongo = MongoClient(connection_string)
        self._logger = logging.getLogger("ChenetDB")
        
    def ping(self) -> str:
        """Verifies connection to the backend."""
        try:
            self._mongo.admin.command('ping')
            return "Pong! Connected to MongoDB successfully."
        except ConnectionFailure:
            return "Error: Could not connect to MongoDB."

    def create_graph(self, db_name: str, graph_name: str):
        """
        Placeholder for graph creation logic.
        """
        db = self._mongo[db_name]
        # In the future, this will create the 3 collections
        return f"Graph '{graph_name}' context initialized in DB '{db_name}'"
