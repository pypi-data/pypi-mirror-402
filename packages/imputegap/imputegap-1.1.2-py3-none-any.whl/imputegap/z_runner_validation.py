import numpy as np

from imputegap.recovery.imputation import Imputation
from imputegap.recovery.manager import TimeSeries
from imputegap.tools import utils

val = "imputation"

#datasets = ["airq_m200.txt", "airq"]
#datasets = ["airq_m70.txt", "airq"]
datasets = ["climate_m70.txt", "climate"]
#datasets = ["chlorine_m200.txt", "chlorine"]


def compare_matrices(A, B, atol=1e-3, rtol=0.0, equal_nan=True, verbose=True, max_show=20):
    """
    Compare two NumPy arrays with tolerance.
      - Element-wise: np.isclose (treats NaN==NaN if equal_nan=True)
      - Totality: True only if all elements are within tolerance (and NaN pairs are allowed if equal_nan=True)
    """
    A = np.asarray(A)
    B = np.asarray(B)
    if A.shape != B.shape:
        raise ValueError(f"Shape mismatch: A{A.shape} vs B{B.shape}")

    eq_elem = np.isclose(A, B, atol=atol, rtol=rtol, equal_nan=equal_nan)
    all_eq = bool(np.all(eq_elem))  # same notion as np.allclose with equal_nan

    if verbose:
        print(f"All elements equal within tol? {all_eq} (atol={atol}, rtol={rtol}, equal_nan={equal_nan})")

        if not all_eq:
            # Indices that failed the tolerance check
            diffs_idx = np.argwhere(~eq_elem)
            n = len(diffs_idx)
            print(f"Number of differing positions: {n}")

            # For reporting, compute deltas only on those positions (avoid NaN math by skipping if either is NaN)
            shown = 0
            for (i, j) in diffs_idx:
                a, b = A[i, j], B[i, j]
                if np.isnan(a) or np.isnan(b):
                    print(f"  ({i}, {j}): A={a} B={b}  [mismatch due to NaN handling]")
                else:
                    delta = abs(a - b)
                    thresh = atol + rtol * abs(b)
                    print(f"  ({i}, {j}): A={a} B={b} |Δ|={delta:.6f} > tol={thresh:.6f}")
                shown += 1
                if shown >= max_show and n > max_show:
                    print(f"  ... and {n - max_show} more differences not shown")
                    break

    return all_eq, eq_elem

# =====================================================================================================================

if val == "imputation": # 0.283584878923833
    # initialize the time series object
    ts_imputebench = TimeSeries()
    ts_imputegap = TimeSeries()

    # load and normalize the dataset
    ts_imputebench.load_series(utils.search_path(datasets[0]))
    ts_imputegap.load_series(utils.search_path(datasets[1]))

    print(f"{ts_imputebench.data.shape = }")
    print(f"{ts_imputegap.data.shape = }")

    # contaminate the time series
    #ts_m = ts.Contamination.mcar(ts.data)

    # impute the contaminated series
    imputer = Imputation.MachineLearning.MissForest(ts_imputebench.data)
    imputer.impute()

    # compute and print the imputation metrics
    imputer.score(ts_imputegap.data, imputer.recov_data)
    ts_imputebench.print_results(imputer.metrics)

    # plot the recovered time series
    ts_imputebench.plot(input_data=ts_imputegap.data, incomp_data=ts_imputebench.data, recov_data=imputer.recov_data, nbr_series=9, subplot=True, algorithm=imputer.algorithm, save_path="./imputegap_assets/imputation")

elif val == "contamination": # 0.283584878923833
    # initialize the time series object
    ts_imputegap = TimeSeries()
    ts_imputebench = TimeSeries()


    # load and normalize the dataset
    ts_imputebench.load_series(utils.search_path("airq_m200.txt"))
    ts_imputegap.load_series(utils.search_path("airq"))

    print(f"{ts_imputegap.data.shape = }")

    # contaminate the time series
    ts_m = ts_imputegap.Contamination.aligned(ts_imputegap.data, offset=0.05, rate_series=0.2, rate_dataset=0.02)

    # impute the contaminated series
    imputer = Imputation.DeepLearning.BRITS(ts_m)
    imputer.impute()

    # compute and print the imputation metrics
    imputer.score(ts_imputegap.data, imputer.recov_data)
    ts_imputegap.print_results(imputer.metrics)

    # plot the recovered time series
    ts_imputegap.plot(input_data=ts_imputegap.data, incomp_data=ts_m, recov_data=imputer.recov_data,
                        nbr_series=9, subplot=True, algorithm=imputer.algorithm,
                        save_path="./imputegap_assets/imputation")

    all_equal, elementwise_equal = compare_matrices(ts_imputebench.data, ts_m, atol=1e-3, rtol=0.0)

elif val=="logic":

    ts_imputegap = TimeSeries()
    ts_cont = TimeSeries()
    ts_rev = TimeSeries()

    ts_imputegap.load_series(utils.search_path("test-logic.txt"))

    ts_m = ts_imputegap.Contamination.aligned(ts_imputegap.data, offset=0.1, rate_series=0.4, rate_dataset=0.5)
    ts_cont.data = ts_m

    ts_imputegap.print(nbr_val=1000, nbr_series=2000)
    ts_cont.print(nbr_val=1000, nbr_series=2000)

    imputer = Imputation.Statistics.KNNImpute(ts_m)
    imputer.impute()
    # compute and print the imputation metrics
    imputer.score(ts_imputegap.data, imputer.recov_data)
    ts_imputegap.print_results(imputer.metrics)

    ts_rev.data = imputer.recov_data
    ts_rev.print()


    ts_rev.plot(input_data=ts_imputegap.data, incomp_data=ts_cont.data, recov_data=ts_rev.data, nbr_series=9, subplot=True, algorithm=imputer.algorithm, save_path="./imputegap_assets/imputation")

elif val=="lib":

    ts_lib = TimeSeries()

    ts_lib.import_matrix([[7, 2, 3], [4, np.nan, 6], [10, 5, 9]])
    ts_lib.print()

    imputer = Imputation.MachineLearning.MICE(ts_lib.data)
    imputer.impute()
    # compute and print the imputation metrics

    ts_rev = TimeSeries()
    ts_rev.data = imputer.recov_data
    ts_rev.print()

    # output : array([[1. , 2. , 4. ],
    #        [3. , 4. , 3. ],
    #        [5.5, 6. , 5. ],
    #        [8. , 8. , 7. ]])