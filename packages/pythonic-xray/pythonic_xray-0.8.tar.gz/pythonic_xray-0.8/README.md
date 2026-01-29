<div align="center">
<img src="./xray_logo.jpeg" width="60%"></img>

<br>
<b>Simple Python Code Analyzer. With no dependencies!</b>
</div>




<br><br>

Contents:
* [Installation](#installation)
* [How to Run](#how-to-run)
* [Options for console run](#options-for-console-run)
* [Examples for console run](#examples-for-console-run)
* [Options for python call of `analyse_code`](#options-for-python-call-of-analyse_code)
* [Example Output (short version)](#example-output-short-version)

<br><br>

---
### Installation

<!--
Just make a conda env with matplotlib:
```bash
conda create -n xray python pip -y
conda activate xray
pip install matplotlib
```
([See here for help with anaconda](https://github.com/xXAI-botXx/Project-Helper#anaconda))
-->


```bash
pip install pythonic-xray
```

<br><br>

---
### How to Run

<br>

You can run it directly from your console:
```bash
python -m pythonic_xray
```
or:
```bash
pythonic-xray
```

Or in your python code:
```python
from pythonic_xray import analyse_code

analysis_str = analyse_code(
                    path_to_file_or_dir=".", 
                    code_strs=None, 
                    name="My Awesome Project", 
                    save_path="./", 
                    should_print=True, 
                    should_save=True,
                    short_analysis=True
                )
```




<br><br>

---
### Options for console run

<br>

| Option        | Type | Default                | Description                                                         |
| ------------- | ---- | ---------------------- | ------------------------------------------------------------------- |
| `--path`      | str  | `.`                    | Path to a Python file or folder containing Python files to analyze. |
| `--name`      | str  | `"My Awesome Project"` | Name of your project (used in saved results).                       |
| `--verbose`   | flag | `False`                 | If included, prints the analysis results in the console.            |
| `--save`      | flag | `False`                 | If included, saves the analysis results to a file.                  |
| `--save_path` | str  | `"./"`                 | Folder path where analysis results will be saved.                   |
| `--short` | flag  | `False`                 | If included, a shorter version will be created.                   |


<br><br>

---
### Examples for console run

<br>

1. **Quick inspection of a local project (no files written)**<br>
    Use this when you just want a fast overview of the current repository.
    ```bash
    pythonic-xray --verbose
    ```
2. **Analyze a full project and store the results for later review**<br>
    This is useful when analyzing larger repositories or when you want to share results.
    ```bash
    pythonic-xray --path ./src --save --save_path ./analysis_results
    ```
3. **Analyze a single module you are actively working on**<br>
    Focus on one file while developing or debugging a specific component.
    ```bash
    pythonic-xray --path ./models/tsmixer.py --name "TSMixer Module" --verbose
    ```
4. **Short summary for CI, reports, or quick comparisons**<br>
    Generate a compact analysis that is easy to scan or archive.
    ```bash
    pythonic-xray --path . --save --short
    ```
5. **Full analysis with custom project name** (recommended)<br>
    Generate a compact analysis that is easy to scan or archive.
    ```bash
    pythonic-xray --path . --name "Recommendation System v2" --verbose --save --save_path ./
    ```

<br><br>

---
### Options for python call of `analyse_code`

<br>

**Parameters**

| Parameter             | Type        | Default                | Description                                                                              |
| --------------------- | ----------- | ---------------------- | ---------------------------------------------------------------------------------------- |
| `path_to_file_or_dir` | `str`       | `None`                 | Path to a single file or folder containing Python files (`.py`) or notebooks (`.ipynb`). |
| `code_strs`           | `list[str]` | `None`                 | List of Python code strings to analyze.                                                  |
| `name`                | `str`       | `"My Awesome Project"` | Name used in the output analysis.                                                        |
| `save_path`           | `str`       | `"./"`                 | Path where the analysis text file `code_analysis.txt` will be saved.                     |
| `should_print`        | `bool`      | `True`                 | If `True`, prints the analysis to the console.                                           |
| `should_save`         | `bool`      | `True`                 | If `True`, saves the analysis to `code_analysis.txt`.                                    |
| `short_analysis`      | `bool`      | `True`                 | If `True`, outputs a shorter summary of the analysis.                                    |

<br><br>

**Returns**<br>
This function does return the analysis text as str. Results are printed and/or saved into a code_analysis.txt depending on `should_print` and `should_save`.



<br><br>

---
### Example Output (short version)

<br><br>

```


_________________________________________
    >>> Analysis of My AI Guide <<<    

 Analysed 465 files (10 .py + 137 .ipynb)
 Failed to analyse 4 files because of errors.

 Analysed 0 given code strings.
 Failed to analyse 0 given code strings because of errors.


-------------------------------------
--------  Analysis of Calls  --------
-------------------------------------
There are 11276 calls.

820x print
416x len
223x range
125x np.random
99x plt.show
97x int
96x super
90x plt.subplots
87x np.arange
87x nlp
86x os.path
84x type
76x plt.figure
68x np.array
67x pd.DataFrame
66x enumerate
61x round
61x pd.read_csv
60x layers.LeakyReLU
58x dict
58x model
58x log
54x plt.scatter
52x nn.Conv2d
51x open
51x model.add
50x layers.BatchNormalization
48x layers.Conv2D
47x isinstance
43x scaler.fit_transform
42x list
42x torch.nn
42x loss.item
41x nn.Linear
40x ValueError
39x np.reshape
37x plt.title
36x layers.Conv2DTranspose
36x hook_func
35x os.makedirs
35x model.parameters
34x ax.plot
34x AgglomerativeClustering
33x torch.utils
33x dt.now
33x torch.tensor
31x plt.xlabel
31x plt.ylabel
31x loss.backward
30x Dense
29x torch.cuda
...

-------------------------------------
-------  Analysis of Imports  -------
-------------------------------------
- torchvision.models.detection.backbone_utils.resnet_fpn_backbone (1)
- h5py (1)
- importlib (1)
- tkinter (1)
- nni.retiarii.model_wrapper (1)
- diagrams.onprem.inmemory.Redis (1)
- torchvision.models.detection.faster_rcnn.TwoMLPHead (1)
- torchvision.models.detection.mask_rcnn.MaskRCNNHeads (1)
- tensorflow.keras.layers.Convolution2D (1)
- nltk.tag.brill_trainer (1)
- tensorflow.keras.Sequential (1)
- nni.retiarii.evaluator.FunctionalEvaluator (1)
- dask.distributed.LocalCluster (1)
- _api.WeightsEnum (1)
- cProfile (1)
- sklearn.neural_network.MLPClassifier (1)
- torchvision.models.detection.MaskRCNN (1)
- numba.float64 (1)
- mlxtend.frequent_patterns.apriori (1)
- sklearn.manifold.MDS (1)
- ast (1)
- nni.retiarii.nn.pytorch (1)
- math.cos (1)
- celluloid.Camera (1)
- typing.List (1)
- pprint (1)
- nltk.bigrams (1)
- sklearn.tree.export_text (1)
- ipywidgets.Layout (1)
- ray.tune (1)
- datetime.timezone (1)
- _utils._ovewrite_named_param (1)
- torch.nn.TransformerEncoder (1)
- helper.Helper (1)
- sklearn.base.TransformerMixin (1)
- folium.Marker (1)
- collections (1)
- sklearn.manifold.Isomap (1)
- hashlib.sha256 (1)
- torch_geometric.datasets.TUDataset (1)
- urllib (1)
- sklearn.linear_model.RidgeCV (1)
- folium.plugins.TimestampedGeoJson (1)
- sklearn.feature_extraction.text.CountVectorizer (1)
- diagrams.onprem.analytics.Spark (1)
- rl.core.Processor (1)
- dask_ml.model_selection.HyperbandSearchCV (1)
- sklearn.datasets.make_classification (1)
- mlxtend.preprocessing.TransactionEncoder (1)
- nni.retiarii.experiment.pytorch.RetiariiExeConfig (1)
- segmentation_models_pytorch (1)
- ...

-------------------------------------
-----  Analysis of Definitions  -----
-------------------------------------
- Defined Functions (596):
    - PlusX (1)
    - __getitem__ (9)
    - add5 (1)
    - analyse_calls (1)
    - analyze_python_code (1)
    - axpy (1)
    - build_optimizer (1)
    - calculate_train_duration (2)
    - collate_fn (1)
    - compile (2)
    - compute_next_q_value (1)
    - configure_optimizers (1)
    - cross_validate (1)
    - cv2_to_pil (1)
    - dist_sim_revert (1)
    - encode_cat (1)
    - enrich_result (1)
    - filter_labels (1)
    - func_fit (1)
    - generate (1)
    - get_all_indexes_of_cluster (1)
    - get_depth (2)
    - get_peaks (1)
    - get_used_depth (2)
    - handle_nulls (1)
    - has_down_peak (1)
    - isLarger10 (1)
    - job_description_sum_similarity (1)
    - load_kaggle_dataset (2)
    - merge_analysis_results (1)
    - metrics (3)
    - monte_carlo_pi (2)
    - monte_carlo_pi_parallel (1)
    - objective_umap (1)
    - pad_masks (1)
    - preprocessing (3)
    - process_observation (1)
    - request_gpt3 (1)
    - resnet101 (1)
    - run_local (1)
    - setup (1)
    - top (1)
    - training (1)
    - update_size (1)
    - valid (1)
    - visualize_results (1)
    - visualize_stack_plot (1)
    - warm_up_and_cool_down_lr (1)
    - wide_resnet101_2 (1)
    - wide_resnet50_2 (1)
    - ...

- Defined Classes (90):
    - CharCount (1)
    - analyse_code (1)
    - analyse_definitions (1)
    - axpy (1)
    - build_network (1)
    - calc_accuracy (1)
    - calc_pixel_accuracy (1)
    - change_bit_depth_with_scaling (2)
    - collate_without_mask_fn (1)
    - compile (2)
    - create_bins (1)
    - draw_dendrogram (1)
    - dropdown_c2_eventhandler (1)
    - evaluation (1)
    - extract_width_height (1)
    - f (2)
    - filter_labels (1)
    - forward (41)
    - generate_fibonacci_distributed (1)
    - generate_square_subsequent_mask (1)
    - get_and_clear_messages (1)
    - get_cur_date_time_as_str (3)
    - get_dataset (1)
    - get_frequency (1)
    - get_informations (1)
    - get_mean (1)
    - get_model (1)
    - get_newest_file (1)
    - get_random_elem (1)
    - get_season (1)
    - get_similar_job_posts_experiment (1)
    - initializeData (1)
    - job_description_similarity_counter (1)
    - kMap (1)
    - main (2)
    - merge_analysis_results (1)
    - plotTimeSeriesResultsInOne (1)
    - proposal_console (1)
    - regular_function (1)
    - save_as_pickle (1)
    - select (4)
    - smoothing_2 (1)
    - stocks_data (1)
    - sum_array (1)
    - test_loop_fn (2)
    - update_cat (1)
    - update_size (1)
    - verify_data (1)
    - visualize_results (1)
    - warm_up_and_cool_down_lr (1)
    - ...

- Lambda Functions: 155

- Returns: 480

- Yields: 6

- `global` Keywords: 7

- `nonlocal` Keywords: 0

-------------------------------------
-----  Analysis of Structures  ------
-------------------------------------
- Defined loops (555):
    - For-Loops: 525
    - While-Loops: 30

- Break's: 49

- Continue's: 22

- If-Statements: 1119

- Try-Blocks: 45

- With-Blocks: 127

-------------------------------------
-----  Analysis of Operations  ------
-------------------------------------
- Operations (1639):
    - Add's: 1081
    - Sub's: 263
    - Mult's: 497
    - Div's: 222
    - Mod's: 56
    - Floor Div's: 66
    - Pow's: 84

- Bool Operations (1474):
    - And's: 154
    - Or's: 64
    - Equals's: 546
    - Not Equals's: 95
    - Is's: 33
    - Is not's: 39
    - In's: 128
    - Not In's: 16

         >>> END of Analysis <<<
_________________________________________

```

