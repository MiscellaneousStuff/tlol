<div align="center">
    <a href="https://www.youtube.com/watch?v=Mz7NbIgJqsc"
       target="_blank">
       <img src="http://img.youtube.com/vi/Mz7NbIgJqsc/0.jpg"
            alt="League of Legends Deep Analysis - Setup and Extraction (Part 1)"
            width="240" height="180" border="10" />
    </a>
</div>

# TLoL

## About

League of Legends Season 11 replay analysis.
This repo is split into two main parts:

1. Patch 11.9 and Patch 11.10 single game analysis. This is referred to as `TLoL-Prototyping`
2. Patch 11.21 multi-early game analysis (Mainly focusing on Miss Fortune). This is referred to as `TLoL-Pilot`
3. Patch 12.2 multi-early game dataset built for reinforcement learning

## Usage

### TLoL-Prototyping

To use the included notebook, you need to decompress the relevant replay using
7-Zip. Be warned, each replay file is around 1GB because of the inefficient
way the replay files were generated. Then, load up the *.ipynb notebook file
using either Jupyter Notebook, Google Colab or another notebook application
and enter the name of the decompressed file.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MiscellaneousStuff/tlol/blob/main/tlol-replay_analysis.ipynb)

### TLoL-Pilot

The included notebook demonstrates how to download one of the datasets from
Google Drive and how to then parse the data for reinforcement learning. This
will include a basic ML agent in the future.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MiscellaneousStuff/tlol/blob/main/League_of_Legends_Patch_11_21_(Reinforcement_Learning).ipynb)

## Replay Files Info

### TLoL-Pilot (Patch 11.21 Replay Databases)

For a full explanation for how these datasets were generated, refer
to the following [blog post](https://miscellaneousstuff.github.io/project/2021/11/19/tlol-part-6-dataset-generation.html)
for very in-depth information.

If you would like to create your own dataset, refer to the following
[GitHub repo](https://github.com/MiscellaneousStuff/tlol-py).

#### 191-EarlyFF Dataset

This database contains 191 early game surrenders (3.5 minute surrenders)
with every single game
object within the game recorded 4 times a second (4 observations a
second). The actions of each champion can also be inferred as the
observations per second is high enough and because the ID's of
the spells are contained so they can be associated with players.
A much larger dataset will be released in the future which should
hopefully allow the development of a human-level League of Legends
deep learning agent. Obviously this will favour supervised learning
methods but it could also be used as a springboard for offline
reinforcement learning techniques as well.

This table shows the top 10 champion occurrences within the dataset.

| Champion     | No. |
| ------------ | --- |
| Nami         | 116 |
| Miss Fortune | 103 |
| Lucian       | 61  |
| Khazix       | 36  |
| Viego        | 35  |
| Lux          | 34  |
| Jhin         | 32  |
| Yone         | 30  |
| Camille      | 29  |
| Graves       | 29  |

Compressed Filename:   `191-EarlyFF.7z`

Decompressed Filename: `early_surrenders.db`

This database is roughly 455MB (and 6GB uncompressed)
and is stored on Google Drive instead of this repository.

`NOTE: Roughly half of the size of the database are indexes.`

[Google Drive Link](https://drive.google.com/file/d/1wcOPYvQ3j3vnoA3TN_fk_n5LI6CJ_GU3/view?usp=sharing)

#### MFLongevity Datasets

These databases contain 987, 728 and 773 games respectively, for a total of 2488 early games.
Both databases contain early game replays
(first 5 minutes of each game) with every single
game object within the game recorded 4 times a second (4 observations
a second). Just as above, actions can be inferred by checking object
names and net_ids (Network ID, Riot uses this to uniquely identify
a game object within a League of Legends game hosted on their server).

Together, this dataset has around 2,985,600 frames for Miss Fortune and several
million for many other champions as well. The
dataset was curated from a larger dataset by picking the games
where the Miss Fortune player lived the longest. This feature had
the best correlation with winning (64.4% win rate for this dataset).
As the dataset overall has a 64.4% win rate in roughly Diamond II,
this ensures the quality of the gameplay is as high as possible
without creating a more complicated system to determine the
quality of the gameplay.

<!--
The `1k-MFLongevity` is better suited to actually creating a deep learning
bot as it contains roughly 1,185,600 frames for Miss Fortune. The
dataset was curated from a larger dataset by picking the games
where the Miss Fortune player lived the longest. This feature had
the best correlation with winning (64.4% win rate for this dataset).
As the dataset overall has a 64.4% win rate in roughly Diamond II,
this ensures the quality of the gameplay is as high as possible
without creating a more complicated system to determine the
quality of the gameplay.
-->

Compressed Filename(s):   `1k-MFLongevity.7z`, `750-MFLongevity.7z`, `800-MFLongevity.7z`

Decompressed Filename(s): For each file in archive => `EUW1-{game_id}.db`

The databases are roughly 2.04GB, 1.54GB and 1.63GB (25.3GB, 19.2GB and 20.5GB uncompressed, respectively)
and is stored on Google Drive instead of this repository.

`NOTE: These databases are 7-zip archives with a separate
SQLite database for each replay. None of the databases
contain indexes.`

[1k-MFLongevity - Google Drive Link](https://drive.google.com/file/d/1wSRmOP0kzYniPn9FBHAl8AvfIR6QkA66/view?usp=sharing)

[750-MFLongevity - Google Drive Link](https://drive.google.com/file/d/1Isaz3kd2SOmcdr4hrtiucM5pmXFK6YL6/view?usp=sharing)

[800-MFLongevity - Google Drive Link](https://drive.google.com/file/d/1SFKdVKpLS9Dg_v2kzZaZL_s5MJ5t4UZ1/view?usp=sharing)

#### Jinx Datasets

This dataset is comprised of 833 early games of Jinx players from
Challenger EUW from patch 12.2. Each replay has undergone a complex
procedure to transform it into a format which is suitable for bulk
analysis or directly training a reinforcement learning agent to
play League of Legends (or at least for the first 5 minutes).

In total this dataset contains almost 1,000,000 frames, which is
comparable to ImageNet. This should be enough to at least
experiment with basic Imitation Learning algorithms such as
Behavioural Cloning, or perhaps
other algorithms such as Generative Adversarial Imitation
Learning (GAIL).

The uncompressed archive is 889.8MB and the uncompressed folder
is 7.7GB. This should be a manageable dataset for most researchers
to experiment with.

Compressed Filename(s):   `jinx_833_ml_db.zip`

Decompressed Filename(s): `full_db/`, For Each file in archive => `EUW1-{game_id}_jinx_100.pkl`

[833-JinxML - Google Drive Link](https://drive.google.com/file/d/1TixmBz2B00kTOPLivkSbfsyDbf1-qNvt/view?usp=sharing)

The table below contains useful metadata for this dataset:

| Characteristic     | Value |
| ------------ | --- |
| Error Correction | 833 / 1,395 Successfully Converted (40.29% error rate) |
| Size         | 7.7GB |
| Conversion Time | 90 minutes |
| Frames       | Almost 1,000,000  |

### TLoL-Prototyping

#### Patch 11.10 Replay

Enter `EUW1-5270795542.rofl.json` after decompressing the replay file
into the notebook to analyse this replay.

Compressed Filename:   `EUW1-5270795542.rofl.7z`

Decompressed Filename: `EUW1-5270795542.rofl.json`

#### Patch 11.9 Replay

Enter `EUW1-5237530168.rofl.json` after decompressing the replay file
into the notebook to analyse this replay.

Compressed Filename:   `EUW1-5237530168.rofl.json.7z`

Decompressed Filename: `EUW1-5237530168.rofl.json`
