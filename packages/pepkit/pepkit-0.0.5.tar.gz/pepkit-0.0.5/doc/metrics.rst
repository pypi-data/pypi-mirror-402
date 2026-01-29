Metrics
=======

The :mod:`pepkit.metrics` package provides a consistent interface for evaluating **regression** and **classification** models.
It is designed to work well with numpy arrays and pandas DataFrames.

.. contents:: On this page
   :local:
   :depth: 2

At a glance
-----------

.. list-table::
   :widths: 25 75
   :header-rows: 0

   * - **Regression**
     - ``pearson_corr``, ``spearman_corr``, ``rmse``, ``mae``, ``r2``
   * - **Classification**
     - ``auc_score``, ``average_precision``, ``enrichment_factor``
   * - **Batch & DataFrame helpers**
     - ``compute_*_metrics`` and ``compute_metrics_from_dataframe``

Regression
----------

Regression metrics are useful for continuous targets (e.g., affinity values, quantitative properties).

.. code-block:: python

    import numpy as np
    from pepkit.metrics import _regression as reg

    y_true = np.array([5.5, 5.4, 5.2, 4.8, 4.2])
    y_pred = np.array([7.467, 7.303, 7.369, 7.633, 7.52])

    print("Pearson:", reg.pearson_corr(y_true, y_pred))
    print("Spearman:", reg.spearman_corr(y_true, y_pred))
    print("RMSE:", reg.rmse(y_true, y_pred))
    print("MAE:", reg.mae(y_true, y_pred))
    print("R2:", reg.r2(y_true, y_pred))

.. tip::

   - Use **Spearman** when you care about ranking more than absolute scale.
   - Use **RMSE** to penalize large errors more strongly than MAE.

Classification
--------------

Classification metrics are for binary/probabilistic predictions (e.g., binder vs non-binder).

.. code-block:: python

    import numpy as np
    from pepkit.metrics import _classification as clf

    y_true = np.array([1, 1, 1, 0, 0])
    y_pred = np.array([0.5, 0.0, 0.2, 1.0, 0.65])

    print("AUC:", clf.auc_score(y_true, y_pred))
    print("Average precision:", clf.average_precision(y_true, y_pred))
    print("Enrichment factor @ 20%:", clf.enrichment_factor(y_true, y_pred, top_percent=20))

.. note::

   **AUC vs AP:**

   - **ROC-AUC** is stable under class imbalance but can hide poor early precision.
   - **Average precision (AP)** is often more informative when positives are rare.

Batch / DataFrame workflows
---------------------------

If you have many datasets or want a single call that returns a dictionary of metrics:

.. code-block:: python

    import numpy as np
    import pandas as pd
    from pepkit.metrics._base import (
        compute_regression_metrics,
        compute_classification_metrics,
        compute_metrics_from_dataframe,
    )

    # Regression
    y_true = np.array([5.5, 5.4, 5.2, 4.8, 4.2])
    y_pred = np.array([7.467, 7.303, 7.369, 7.633, 7.52])
    print(compute_regression_metrics(y_true, y_pred))

    # Classification
    y_true_clf = np.array([1, 1, 0, 0, 1])
    y_pred_proba = np.array([0.7, 0.3, 0.2, 0.8, 0.6])
    print(compute_classification_metrics(y_true_clf, y_pred_proba))

    # DataFrame
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred})
    results = compute_metrics_from_dataframe(
        df,
        ground_truth_key="y_true",
        pred_key="y_pred",
        task="regression",
    )
    print(results)

See also
--------

- :doc:`chem` — generate features/properties before evaluation
- :doc:`api` — full API docs for :mod:`pepkit.metrics`
