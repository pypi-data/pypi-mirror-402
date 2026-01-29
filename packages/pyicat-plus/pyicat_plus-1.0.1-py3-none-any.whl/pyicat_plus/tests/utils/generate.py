import random


def investigation_id():
    return icat_id()


def icat_id():
    return str(random.randint(1000000000, 9999999999))
