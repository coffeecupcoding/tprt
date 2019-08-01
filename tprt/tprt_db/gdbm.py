
from tprt_db.greydb import greyDB
import dbm.gnu
import logging
import threading



class gdbmDB(greyDB):
    """
    This class uses dbm.gnu to save and restore a database as needed
    Keys and values are expected to be strings
    """

    def __init__(self, db_file):
        """Open or create the DB file, and create the write lock"""
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self._db =  dbm.gnu.open(db_file, 'cf', 0o660)
        self._lock = threading.Lock()
        logging.debug("opened gdbm file %s", db_file)

    def update(self, key, value):
        """Write a key/value pair, with locking"""
        self._lock.acquire()
        self._db[key] = value
        self._lock.release()
        logging.debug("inserted key %s with value %s into db", key, value)

    def get(self, key):
        """Look up a value in the database, return None if not found"""
        if key in self._db:
            return self._db[key]
        else:
            return None

    def delete(self,key):
        """
        Remove an existing key/value pair from the database
        Used on existing keys only, may raise an exception if the key
        is not found.  The caller should call save() after finishing work
        """
        self._lock.acquire()
        del self._db[key]
        self._lock.release()
        logging.debug("removed key %s from db", key)

    def save(self):
        """Write the database to disk"""
        logging.debug("sychronizing db")
        self._db.sync()
        
    def apply(self, func):
        """
        Loop over entries, passing keys and values to func(), which
        should take a key/value pair and return something or None
        'None' results from func() are filtered out
        """
        logging.debug("applying function %s to db", str(func))
        return [ y for y in [ func(x, self._db[x]) for x in self._db.keys() ] if y ]

