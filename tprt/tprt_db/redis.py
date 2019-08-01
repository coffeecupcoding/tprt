
from tprt_db.greydb import greyDB
import logging
import re
import redis



class redisDB(greyDB):
    """
    This class fronts a redis database for greylist entries
    It may work for other uses as well
    Keys and values are expected to be strings
    """

    # This currently assumes that redis does sufficient locking

    def __init__(self, url):
        """Open a connection to a specified redis instance"""
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        sanitized_url = re.sub('/:.*@','/:password@',url)
        self._db = redis.Redis.from_url(url)
        logging.info('opened redis connection via url %s', sanitized_url)

    def update(self, key, value):
        """Write a key/value pair to the redis instance"""
        result = self._db.set(key, value)
        if result:
            logging.debug("inserted key %s with value %s into database",
                key, value )
        else:
            logging.warning("failed to insert key %s with value %s "
               "into database", key, value )

    def get(self, key):
        """Look up a value in the database, return None if not found"""
        return self._db.get(key)

    def delete(self,key):
        """
        Remove an existing key/value pair from the database
        Used on existing keys only, may raise an exception if the key
        is not found.  The caller should call save() after finishing work
        """
        self._db.delete(key)
        logging.debug("removed key %s from db", key)

    def save(self):
        """Force the redis server to save to disk"""
        logging.debug("sychronizing db")
        self._db.save()
        
    def apply(self, func):
        """
        Loop over entries, passing keys and values to func(), which
        should take a key/value pair and return something or None
        'None' results from func() are filtered out
        """
        logging.debug("applying function %s to db", str(func))
        return [ y for y in [ func(x, self._db.get(x)) for x in self._db.scan_iter() ] if y ]

