import logging
import pandas as pd
import pickle
import azure.functions as func


def main(req: func.HttpRequest, covblob: func.InputStream) -> func.HttpResponse:

    country = req.params.get('country') or 'Russia'

    logging.info('covidata function triggered with country={} and blob with len={}'.format(country,covblob.length))

    binary = covblob.read()
    logging.info("binary is {}, len={}".format(binary[:15],len(binary)))
    data = pickle.loads(binary)
    
    df = data[country]

    res = df.to_csv()

    return func.HttpResponse(res,status=200)
