from imputegap.recovery.manager import TimeSeries
from imputegap.tools import utils

# initialize the time series object
ts = TimeSeries()
print(f"\nImputeGAP datasets : {ts.datasets}")

# load and normalize the dataset
ts.load_series(utils.search_path("eeg-alcohol"), normalizer=None)

# plot and print a subset of time series
ts.print(nbr_series=3, nbr_val=20)
ts.plot(input_data=ts.data)