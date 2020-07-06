import datetime
import logging

import azure.functions as func

from .slidingsir import *


def main(mytimer: func.TimerRequest, outblob: func.Out[bytes]) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Daily fetch happened at %s', utc_timestamp)

    cd = CountryData()
    cd.fetch()
    data = cd.get_country_data(callback=lambda x: logging.info("Computing params for %s", x))
    b = pickle.dumps(data)
    
    outblob.set(b)
