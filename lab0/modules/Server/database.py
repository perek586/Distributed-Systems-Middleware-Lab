# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 24 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Implementation of a simple database class."""

import random


class Database(object):

    """Class containing a database implementation."""

    def __init__(self, db_file):
        self.db_file = db_file
        self.rand = random.Random()
        self.rand.seed()
        self.db_entries = []
        entry = ""
        with open(db_file, "r") as f:
            for line in f.readlines():
                if line == "%\n":
                    self.db_entries.append(entry)
                    entry = ""
                    continue
                entry += line



    def read(self):
        """Read a random location in the database."""
        return self.db_entries[self.rand.randint(0, len(self.db_entries) - 1)]

    def write(self, fortune):
        """Write a new fortune to the database."""
        self.db_entries.append(fortune)
        with open(self.db_file, "a") as f:
            f.write(fortune + "\n%\n")

if __name__ == "__main__":
    with open("fortunelocal.db", "w") as f:
        f.write("")

    db = Database('fortunelocal.db')
    db.write("Hello World!")
    db = Database('fortunelocal.db')
    print(db.read())
