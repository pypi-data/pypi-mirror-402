from imputegap.recovery.benchmark import Benchmark
from imputegap.tools import utils
from imputegap.recovery.imputation import Imputation
from imputegap.recovery.contamination import GenGap
from imputegap.recovery.manager import TimeSeries

my_algorithms = ["CDRec", "SoftImpute"]

my_opt = "default_params"

my_datasets = ["chlorine"]

my_patterns = ["mcar"]

range = [0.05, 0.1, 0.2, 0.8]

my_metrics = ["RMSE", "MAE", "CORRELATION"]

# launch the evaluation
bench = Benchmark()
bench.eval(algorithms=my_algorithms, datasets=my_datasets, patterns=my_patterns, x_axis=range, metrics=my_metrics, optimizer=my_opt, nbr_series=14, nbr_vals=100)