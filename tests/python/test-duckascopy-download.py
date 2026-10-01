############################################################################################
### Test per il download dei dati da Dukascopy utilizzando la libreria dukascopy-python. ###
############################################################################################


from datetime import datetime, timedelta
import dukascopy_python
from dukascopy_python.instruments import INSTRUMENT_FX_MAJORS_GBP_USD

start = datetime(2025, 1, 1)
end = datetime(2025, 2, 1)
instrument = INSTRUMENT_FX_MAJORS_GBP_USD
interval = dukascopy_python.INTERVAL_HOUR_1
offer_side = dukascopy_python.OFFER_SIDE_BID

df = dukascopy_python.fetch(
    instrument,
    interval,
    offer_side,
    start,
    end,
)

df.to_json("output.json")