import os
import subprocess

from datetime import datetime

from absl import app
from absl import flags

from lib.lib import *
import concurrent.futures

FLAGS = flags.FLAGS
flags.DEFINE_string("db_dir",   None,  "Directory of replay DBs to convert")
flags.DEFINE_string("out_path", None,  "Output directory")
flags.DEFINE_string("player", "jinx",  "Player to tailor observations towards")
flags.DEFINE_float("cutoff",  5.0,     "Timestep to start dataset from")
flags.DEFINE_integer("max_workers", 4, "Maximum number of workers to generate dataset")
#flags.mark_flag_as_required("db_dir")
#flags.mark_flag_as_required("out_path")

def go_wrapper(fi, db_dir, player, cutoff, out_path):
    db_path = os.path.join(db_dir, fi)
    print(f"Started: {db_path}")
    res = go(db_path, player, cutoff, out_path)
    if res == -1:
        print("Invalid replay:", os.path.basename(db_path))
    else:
        print("Valid replay:", os.path.basename(db_path))
    return res

def main(unused_argv):
    fi_s     = os.listdir(FLAGS.db_dir)
    player   = FLAGS.player
    cutoff   = FLAGS.cutoff
    out_path = FLAGS.out_path

    with concurrent.futures.ProcessPoolExecutor(max_workers=FLAGS.max_workers) as executor:
        future_res = (executor.submit(
            go_wrapper,
            fi,
            FLAGS.db_dir,
            player,
            cutoff,
            out_path
        ) for fi in fi_s)
        for future in concurrent.futures.as_completed(future_res):
            try:
                print(future.result())
            except Exception as exc:
                print(exc)
            finally:
                print("Cur replay done!")

def entry_point():
    app.run(main)

if __name__ == "__main__":
    app.run(main)