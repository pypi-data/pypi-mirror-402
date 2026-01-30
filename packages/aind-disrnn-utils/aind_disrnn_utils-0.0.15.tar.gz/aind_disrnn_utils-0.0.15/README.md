# aind_disrnn_utils

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python->=3.11-blue?logo=python)

# Usage
## Creating a dataset
- Obtain a list of NWB files you wish to fit the model to
```python
import aind_dynamic_foraging_multisession_analysis.multisession_load as ms_load
import aind_disrnn_utils as dl

nwbs, df_trials = ms_load.make_multisession_trials_df(nwb_files)
dataset = dl.create_disrnn_dataset(df_trials)
```

- You don't need to use `make_multisession_trials_df`, but the trials data frame does need to have a column "ses_idx" that splits trials into sessions. 

## Predefined datasets
This Code Ocean Capsule can be used for loading a list of sessions and saving the result as a dataframe: [Code Ocean Capsule](https://codeocean.allenneuraldynamics.org/capsule/4447096/tree)

The resulting data assets can be used like:
```python
import pandas as pd
import aind_disrnn_utils.data_loader as dl
df = pd.read_csv('/data/disrnn_dataset_774212/disrnn_dataset.csv')
dataset = dl.create_disrrn_dataset(df)
```
Dataset name| mouse id | # trials | # sessions | data asset ID | Task |
|-|-|-:|-:|-|- |
disrnn_dataset_774212 | 774212 | 16184 | 31 | ad5ec889-f4e0-45a2-802c-f843266d3cce | Uncoupled Without Baiting
disrnn_dataset_779531 | 779531 | 7272 | 12 | 64fa1cb4-8af8-4d96-a965-3454d59439f6 | Uncoupled Without Baiting
disrnn_dataset_781173 | 781173 | 8132 | 15 | 9788eb8d-ea88-4c60-bacc-1a23efd2f5e1 | Uncoupled Without Baiting
disrnn_dataset_781162 | 781162  | 6417 | 12 | 8eaa487e-e78c-4635-b24b-eabe680a55ae | Uncoupled Without Baiting
disrnn_dataset_778077 | 778077 | 8336 | 15 | 76fc65d3-eec4-4578-a20d-499193fc920e | Uncoupled Without Baiting


The datasets can be combined to fit easily:
```python
import pandas as pd
import aind_disrnn_utils.data_loader as dl

mice = [77412, 779531, 781173, 781162, 778077]
dfs = []
for mouse in mice:
    dfs.append(pd.read_csv('/data/disrnn_dataset_{}/disrnn_dataset.csv'.format(mouse)))
df = pd.concat(dfs)
dataset = dl.create_disrrn_dataset(df)

```

## Saving results

After fitting the network, you can add the latent states and predictions back into the dataframe of trials:
```python
df_trials = dl.add_model_results(df_trials, network_states.__array__(), yhat, ignore_policy=ignore_policy)
```

# Installation
To install the software from PyPi
```bash
pip install aind-disrnn-utils
```
To use the software, in the root directory, run
```bash
pip install -e .
```

To develop the code, run
```bash
pip install -e . --group dev
```
Note: --group flag is available only in pip versions >=25.1

Alternatively, if using `uv`, run
```bash
uv sync
```

## Level of Support
 - Occasional updates: We are planning on occasional updating this tool with no fixed schedule. Community involvement is encouraged through both issues and pull requests.


