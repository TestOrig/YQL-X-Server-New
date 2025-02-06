import os
import sqlite3
from ..ModuleClasses import YQL
from ...utils import gen_woeid_for_name, get_gen_name_for_woeid

module_dir = os.path.dirname(__file__)

class LocalSQLiteYQL(YQL):
    possible_db_paths = [
        # current working dir
        "yql.db",
        # module dir
        os.path.join(module_dir, "yql.db"),
    ]
    def __init__(self):
        for path in self.possible_db_paths:
            if os.path.exists(path):
                self.db_path = path
                self.db_conn = sqlite3.connect(self.db_path)
                self.cursor = self.db_conn.cursor()
                break
        else:
            raise FileNotFoundError("No SQLite database found")
    
    def get_woeid_from_name(self, name, lang):
        pass