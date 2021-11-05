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

This database contains 72 early game surrenders with every single game
object within the game recorded 4 times a second (4 observations a
second). The actions of each champion can also be inferred as the
observations per second is high enough and because the ID's of
the spells are contained so they can be associated with players.
A much larger dataset will be released in the future which should
hopefully allow the development of a human-level League of Legends
deep learning agent. Obviously this will favour supervised learning
methods but it could also be used as a springboard for offline
reinforcement learning techniques as well.

Compressed Filename:   `early_surrenders.7z`
Decompressed Filename: `early_surrenders.db`

This database is roughly 175MB and is stored on Google Drive
instead of this repository.
[Google Drive Link](https://drive.google.com/file/d/1-r7pWwvi49r9vvU-xX4BkajVwfZrD0r_/view?usp=sharing)

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