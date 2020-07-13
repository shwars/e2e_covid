import logging
import pandas as pd
import pickle
import base64
import azure.functions as func
from ..shared.slidingsir import *
import matplotlib.pyplot as plt
import io

def main(req: func.HttpRequest, covblob: func.InputStream) -> func.HttpResponse:

    country = req.params.get('country') or 'Russia'
    output = req.params.get('output') or 'csv'

    logging.info('covidata function triggered with country={} and blob with len={}'.format(country,covblob.length))

    binary = covblob.read()
    # logging.info("binary is {}, len={}".format(binary[:15],len(binary)))
    binary = base64.decodebytes(binary)
    data = pickle.loads(binary) 
    
    pop,df = data[country]

    if output=="plot":
        plt.figure()
        CountryData.plot(pop,df)
        buf = io.BytesIO()
        plt.savefig(buf, format = 'jpg')
        buf.seek(0)
        return func.HttpResponse(body=buf.read(),mimetype='image/jpeg')
    else:
        res = df.to_csv()
        return func.HttpResponse(res)
