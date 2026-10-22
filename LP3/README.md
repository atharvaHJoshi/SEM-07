# LP-III Practicals — DAA and Machine Learning

Semester 7 (2026-27 BE Sem-I) practicals for **Laboratory Practice III
(410246)**. This folder contains complete, executed Jupyter notebooks for the
two theory subjects in this lab:

| Group | Subject | Code |
|---|---|---|
| A | Design and Analysis of Algorithms | 410241 |
| B | Machine Learning | 410242 |

> **Blockchain Technology (410243, Group C) is intentionally not included.**
> Only the DAA and ML practicals were requested.

Every notebook contains the aim, problem statement, theory, a complete Python
implementation, saved outputs and plots, observations, complexity analysis where
relevant, a conclusion, and viva questions. Each notebook also contains a
**Detailed output explanation** code cell after the results that reads the
computed variables and prints a structured, self-contained interpretation: key
values, what they mean, how to read the plots/tables, and the practical
takeaway.

## Detailed output reports

The detailed-output code cell in every practical is deliberately executable
rather than a static Markdown summary. It prints:

- the important numbers from that practical (timings, scores, selected items,
  confusion-matrix counts, cluster profiles, and so on);
- a plain-language explanation of what each number means;
- the complexity or modelling interpretation that follows from the result;
- caveats such as noisy timings, sampling variation, or correlation not
  implying causation.

Because the report reads the notebook's own variables, it stays consistent if
the practical is re-executed with different data or hyperparameters.

## Practical index

### Group A — Design and Analysis of Algorithms

| # | Practical | Notebook | Mini-project option |
|---|---|---|---|
| 1 | Fibonacci numbers: recursive and iterative | [`DAA/Practical1_Fibonacci.ipynb`](DAA/Practical1_Fibonacci.ipynb) | — |
| 2 | Huffman encoding using a greedy strategy | [`DAA/Practical2_Huffman_Coding.ipynb`](DAA/Practical2_Huffman_Coding.ipynb) | — |
| 3 | 0/1 Knapsack using dynamic programming and branch & bound | [`DAA/Practical3_01_Knapsack.ipynb`](DAA/Practical3_01_Knapsack.ipynb) | — |
| 4 | N-Queens using backtracking | [`DAA/Practical4_N_Queens.ipynb`](DAA/Practical4_N_Queens.ipynb) | — |
| 5 | Quick sort: deterministic vs randomised | [`DAA/Practical5_QuickSort.ipynb`](DAA/Practical5_QuickSort.ipynb) | — |
| 6 | Naive vs Rabin-Karp string matching | [`DAA/Practical6_MiniProject_String_Matching.ipynb`](DAA/Practical6_MiniProject_String_Matching.ipynb) | **C** |

### Group B — Machine Learning

| # | Practical | Notebook | Mini-project option |
|---|---|---|---|
| 1 | Uber fare prediction with Linear Regression and Random Forest | [`ML/Practical1_Uber_Fare_Prediction.ipynb`](ML/Practical1_Uber_Fare_Prediction.ipynb) | — |
| 2 | Email spam classification with KNN and SVM | [`ML/Practical2_Email_Spam_Classification.ipynb`](ML/Practical2_Email_Spam_Classification.ipynb) | — |
| 3 | Bank customer churn with a neural network | [`ML/Practical3_Bank_Churn_Neural_Network.ipynb`](ML/Practical3_Bank_Churn_Neural_Network.ipynb) | — |
| 4 | Gradient descent for a local minimum | [`ML/Practical4_Gradient_Descent.ipynb`](ML/Practical4_Gradient_Descent.ipynb) | — |
| 5 | K-Means and hierarchical clustering on sales data | [`ML/Practical5_KMeans_Clustering.ipynb`](ML/Practical5_KMeans_Clustering.ipynb) | — |
| 6 | Titanic survival prediction | [`ML/Practical6_MiniProject_Titanic.ipynb`](ML/Practical6_MiniProject_Titanic.ipynb) | **B** |

## Datasets

The ML notebooks use the real Kaggle datasets listed in the lab manual. They are
stored as gzipped CSV files in [`ML/data/`](ML/data/) so the notebooks run
offline without downloading anything:

| File | Kaggle dataset | Used in |
|---|---|---|
| `uber.csv.gz` | [Uber Fares Dataset](https://www.kaggle.com/datasets/yasserh/uber-fares-dataset) | ML 1 |
| `emails.csv.gz` | [Email Spam Classification Dataset](https://www.kaggle.com/datasets/balaka18/email-spam-classification-dataset-csv) | ML 2 |
| `Churn_Modelling.csv.gz` | [Churn Modelling Dataset](https://www.kaggle.com/datasets/shrutimechlearn/churn-modelling) | ML 3 |
| `sales_data_sample.csv.gz` | [Sample Sales Data](https://www.kaggle.com/datasets/kyanyoga/sample-sales-data) | ML 5 |
| `titanic.csv.gz` | [Titanic Competition Dataset](https://www.kaggle.com/competitions/titanic/data) | ML 6 |

`sales_data_sample.csv.gz` is read with `latin-1` encoding because some customer
names are not valid UTF-8. The DAA practicals do not need external data.

The source lab manual is [`3. Signed BE Comp Sem-I LP-III Lab Manual 2026-27.pdf`](3.%20Signed%20BE%20Comp%20Sem-I%20LP-III%20Lab%20Manual%202026-27.pdf).

## Environment

The notebooks were executed with Python 3.14 and the package versions in
[`requirements.txt`](requirements.txt). To recreate the environment:

```bash
cd LP3
python3 -m venv ../.venv
source ../.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --user --name lp3-venv \
  --display-name "Python (LP3)"
```

To open the notebooks:

```bash
jupyter lab
# or
jupyter notebook
```

Start Jupyter from this `LP3/` folder. The ML notebooks look for `data/` first
and fall back to `ML/data/`, so they work both from `LP3/` and from `LP3/ML/`.

## Re-running all notebooks

The `.ipynb` files already contain their executed outputs. To regenerate and
re-execute every notebook from the jupytext sources in [`_src/`](_src/):

```bash
./run_all.sh          # DAA + ML
./run_all.sh daa      # only DAA
./run_all.sh ml       # only ML
```

If the virtual environment is somewhere else, set `VENV`:

```bash
VENV=/path/to/venv ./run_all.sh
```

To execute one notebook manually:

```bash
cd LP3/ML
../../.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=lp3-venv \
  --ExecutePreprocessor.timeout=900 \
  Practical6_MiniProject_Titanic.ipynb
```

The editable jupytext sources are in [`_src/DAA/`](_src/DAA/) and
[`_src/ML/`](_src/ML/). Each notebook is generated from its matching `.py` file
with `jupytext --to ipynb`.

## Notes

- Random seeds are fixed so the results are reproducible.
- ML Practical 3 uses scikit-learn's `MLPClassifier` rather than Keras/TensorFlow,
  because TensorFlow was not available for Python 3.14 in this environment. It
  is still a feed-forward neural network trained with back-propagation and Adam,
  and the notebook compares a baseline network with an improved class-weighted
  network.
- The executed notebooks are the deliverables. The `_src/` files are kept so the
  notebooks can be edited and regenerated without hand-editing JSON.
