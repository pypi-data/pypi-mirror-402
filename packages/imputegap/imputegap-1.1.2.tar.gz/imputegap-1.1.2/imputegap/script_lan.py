from imputegap.recovery.manager import TimeSeries
from imputegap.recovery.contamination import GenGap
from imputegap.tools import utils

"""
# initialize the time series object
ts = TimeSeries()
print(f"\nMissingness patterns : {ts.patterns}")

# load and normalize the dataset
ts.load_series(utils.search_path("soccer"), normalizer=None, nbr_series=3, nbr_val=4000)
ts.shift(2, 5)

# contaminate the time series with MCAR pattern
ts_m = GenGap.overlap(ts.data, rate_series=0.25)
#ts_m = GenGap.gaussian(ts.data, rate_dataset=0.7, rate_series=0.25, offset=500,std_dev=0.25)
#ts_m = GenGap.aligned(ts.data, rate_dataset=0.7, rate_series=0.25, offset=500)
#ts_m = GenGap.mcar(ts.data, rate_dataset=1, rate_series=0.2, offset=500, block_size=100, seed=False)


# plot the contaminated time series
ts.plot(ts.data, ts_m, nbr_series=9, subplot=False, save_path="./imputegap_assets/contamination")
"""

from imputegap.recovery.manager import TimeSeries
from imputegap.tools import utils

# initialize the time series object
ts = TimeSeries()
print(f"\nImputeGAP datasets : {ts.datasets}")

for ds in utils.list_of_datasets():

    # load and normalize the dataset
    ts.load_series(utils.search_path(ds), normalizer=None)
    N, M = ts.data.shape

    if N > 10000:
        nbr_val=int(N * 0.15)
    else:
        nbr_val = N
    nbr_val_2 = nbr_val

    if ds == "airq":
        nbr_val_2 = 500
    elif ds == "bafu":
        nbr_val_2 = 2000
    elif ds == "meteo":
        nbr_val_2 = 1000
    elif ds == "solar":
        nbr_val_2 = 600
    elif ds == "motion":
        x = TimeSeries()
        x .load_series(utils.search_path(ds), normalizer=None)
        x.range(2000, 3000)
        nbr_val_2 = 3000
    elif ds == "chlorine":
        nbr_val_2 = 500
    elif ds == "stock-exchange":
        nbr_val_2 = 1000
    elif ds == "drift":
        nbr_val = 400
        nbr_val_2 = 50
    elif ds == "electricity":
        nbr_val = 1500
        nbr_val_2 = 100
    elif ds == "sport-activity":
        nbr_val_2 = 40
        ts.data = ts.data[:, [10, 30, 57]]
    elif ds == "temperature":
        nbr_val_2 = 400
    elif ds == "traffic":
        nbr_val_2 = 300
    elif ds == "forecast-economy":
        nbr_val = 200
        nbr_val_2 = 60
    elif ds == "eeg-alcohol":
        nbr_val_2 = 60
    elif ds == "meteo":
        nbr_val_2 = 1000
    elif ds == "soccer":
        nbr_val_2 = 6000
    elif ds == "climate":
        nbr_val = 1000
        nbr_val_2 = 300

    if N > 3000:
        N = 3000

    if ds == "motion":
        ts.plot(input_data=x.data, nbr_series=3, nbr_val=nbr_val_2, save_path="./imputegap_assets", legends=False, algorithm=ds, display=False, grid=False)
    else:
        ts.plot(input_data=ts.data, nbr_series=3, nbr_val=nbr_val_2, save_path="./imputegap_assets", legends=False, algorithm=ds, display=False, grid=False)
    ts.plot(input_data=ts.data, nbr_series=1, nbr_val=nbr_val, save_path="./imputegap_assets", legends=False, algorithm=ds+"_1", display=False, grid=False)