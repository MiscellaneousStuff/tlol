# TLoL

## About

League of Legends Season 11 replay analysis.

## Usage

To use the included notebook, you need to decompress the relevant replay using
7-Zip. Be warned, each replay file is around 1GB because of the inefficient
way the replay files were generated. Then, load up the *.ipynb notebook file
using either Jupyter Notebook, Google Colab or another notebook application
and enter the name of the decompressed file.

## Replay File Info

### Patch 11.21 Replay Database

This database contains 191 early game surrenders with every single game
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

Compressed Filename:   `early_surrenders.7z`

Decompressed Filename: `early_surrenders.db`

This database is roughly 455MB (and 6GB uncompressed)
and is stored on Google Drive instead of this repository.
[Google Drive Link](https://drive.google.com/file/d/1wcOPYvQ3j3vnoA3TN_fk_n5LI6CJ_GU3/view?usp=sharing)

1000 game miss fortune database:

[Google Drive Link](https://drive.google.com/file/d/1wSRmOP0kzYniPn9FBHAl8AvfIR6QkA66/view?usp=sharing)

### Patch 11.10 Replay

Enter `EUW1-5270795542.rofl.json` after compressing the replay file
into the notebook to analyse this replay.

Compressed Filename:   `EUW1-5270795542.rofl.7z`

Decompressed Filename: `EUW1-5270795542.rofl.json`

### Patch 11.9 Replay

Enter `EUW1-5237530168.rofl.json` after compressing the replay file
into the notebook to analyse this replay.

Compressed Filename:   `EUW1-5237530168.rofl.json.7z`

Decompressed Filename: `EUW1-5237530168.rofl.json`