import logging
import pandas as pd
import pickle
import base64
import azure.functions as func
from .slidingsir import *

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
        plot(pop,df)
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        return func.HttpResponse(body=buf,mimetype='image/png')
    else:
        res = df[1].to_csv()
        return func.HttpResponse(res)
