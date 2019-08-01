
class greyDB:
    """
    This class is a superclass of all database access implementations that
    support the methods needed to be used as a greylisting database
    """
    def __init__(self, db_file):
        """Open or create the DB file, and create the write lock"""
        raise NotImplementedError

    def update(self, key, value):
        """Write a key/value pair, with locking"""
        raise NotImplementedError

    def get(self, key):
        """Look up a value in the database, return None if not found"""
        raise NotImplementedError

    def delete(self,key):
        """
        Remove an existing key/value pair from the database
        Used on existing keys only, may raise an exception if the key
        is not found.  The caller should call save() after finishing work
        """
        raise NotImplementedError

    def save(self):
        """Write the database to disk"""
        raise NotImplementedError
        
    def apply(self, func):
        """
        Loop over entries, passing keys and values to func(), which
        should take a key/value pair and return something or None
        'None' results from func() are filtered out
        """
        raise NotImplementedError

