import sqlite3
import math
import os

import pandas as pd
import numpy as np

from itertools import compress

import warnings
warnings.filterwarnings('ignore')

def set_player_pos(player_pos, row):
    player_pos[row["time"]] = [row["position_x"], row["position_z"]]

def linear_diff(row, col, player_pos, player_pos_idx):
    return row[col] - player_pos[row["time"]][player_pos_idx]

def multi_diff(row, player_pos):
    cur_pos  = row[["position_x", "position_z"]]
    player_p = player_pos[row["time"]]
    return math.dist(cur_pos, player_p)

def digitize_delta(val):
    if   val < -350:                 return -4
    elif val > -350 and val <= -250: return -3
    elif val > -250 and val <= -150: return -2
    elif val > -150 and val <= -50:  return -1
    elif val > -50  and val <=  50:  return +0
    elif val >= 50  and val <   150: return +1
    elif val >= 150 and val <   250: return +2
    elif val >= 250 and val <   350: return +3
    else:                            return +4

def is_spell_cast(row, spell):
    return (row[f"{spell}_prev_cd"] < row[f"{spell}_cd"]) & (row[f"{spell}_prev_cd"] == 0)

def get_previous_positions(table_df):
    champs_prev_pos_x = table_df["position_x"].shift(10)
    champs_prev_pos_y = table_df["position_y"].shift(10)
    champs_prev_pos_z = table_df["position_z"].shift(10)
    table_df["prev_position_x"] = champs_prev_pos_x
    table_df["prev_position_y"] = champs_prev_pos_y
    table_df["prev_position_z"] = champs_prev_pos_z
    table_df = table_df.fillna(0)

    return table_df

def get_distances_from_player(table_df, champs_df, player):
    # Get X, Y, (X, Y) Distances from Player
    player_df = champs_df[champs_df["name"] == player]
    player_pos = {}
    player_df.apply(lambda row: set_player_pos(player_pos, row), axis=1)
    x_champ_diffs   = table_df[["time", "position_x"]].apply(\
        lambda row: linear_diff(row,
                                "position_x",
                                player_pos,
                                player_pos_idx=0), axis=1)
    z_champ_diffs   = table_df[["time", "position_z"]].apply(\
        lambda row: linear_diff(row,
                                "position_z",
                                player_pos,
                                player_pos_idx=1), axis=1)
    x_z_champ_diffs = table_df[["time", "position_x", "position_z"]].apply(\
        lambda row: multi_diff(row, player_pos), axis=1)

    # Append X, Y, (X, Y) Distances from Player
    table_df["x_diff_from_player"]   = x_champ_diffs
    table_df["z_diff_from_player"]   = z_champ_diffs
    table_df["x_z_diff_from_player"] = x_z_champ_diffs

    return table_df

def find_aa_target(row, objects_df, champs_df):
    # Get auto attack time and destination
    t, x, z = row[["time", "end_position_x", "end_position_z"]]
    
    # Search turrets, jungle camps and minions for auto attack destination
    found_obj = objects_df[\
        (objects_df["position_x"] == x) &
        (objects_df["position_z"] == z)]
    if len(found_obj) > 0:
        return found_obj.iloc[0]["obj_type"], found_obj.iloc[0]["net_id"]

    # Search champs for auto attack destination
    found_champ = champs_df[\
        (champs_df["position_x"] == x) &
        (champs_df["position_z"] == z)]
    if len(found_champ) > 0:
        return found_champ.iloc[0]["obj_type"], found_champ.iloc[0]["net_id"]
        
    return None, -1

def get_champs_df(con, player, cutoff=5.0):
    # Get unique champion records after cutoff
    champs_sql = pd.read_sql_query("SELECT * FROM champs", con)
    champs_df  = pd.DataFrame(champs_sql)
    champs_df  = champs_df.drop(labels=["game_id"], axis=1)
    champs_df  = champs_df[champs_df["time"] > cutoff]
    champs_df = champs_df.drop_duplicates(subset=["time", "obj_type", "name"])

    # If there aren't 10 champs or the champ obs aren't all the same length,
    # ... then this replay database is invalid :/
    val_counts = champs_df["name"].value_counts()
    champ_cnt  = len(champs_df["name"].unique())
    if champ_cnt != 10:
        print(f"Invalid Replay: There aren't 10 champs - Found {champ_cnt} champs.")
        return -1
    elif len(set(val_counts)) != 1:
        print("Invalid Replay: Inconsistent champ record counts.")
        return -1

    # Get previous positions
    champs_df = get_previous_positions(champs_df)

    # Calculate position deltas
    champs_df["position_x_delta"]   = champs_df["position_x"] - champs_df["prev_position_x"]
    champs_df["position_z_delta"]   = champs_df["position_z"] - champs_df["prev_position_z"]
    champs_df["position_x_z_delta"] = [math.dist((x, y), (prev_x, prev_y))
                                       for x, y, prev_x, prev_y in \
                                       zip(champs_df["position_x"],
                                           champs_df["position_z"],
                                           champs_df["prev_position_x"],
                                           champs_df["prev_position_z"])]
    pos_x_delta_digital = \
        champs_df["position_x_delta"].apply(lambda val: digitize_delta(val))
    pos_z_delta_digital = \
        champs_df["position_z_delta"].apply(lambda val: digitize_delta(val))
    champs_df["position_x_delta_digital"] = pos_x_delta_digital
    champs_df["position_z_delta_digital"] = pos_z_delta_digital

    # Get spell casts
    champs_df["q_prev_cd"] = champs_df["q_cd"].shift(10)
    champs_df["w_prev_cd"] = champs_df["w_cd"].shift(10)
    champs_df["e_prev_cd"] = champs_df["e_cd"].shift(10)
    champs_df["r_prev_cd"] = champs_df["r_cd"].shift(10)
    champs_df["d_prev_cd"] = champs_df["d_cd"].shift(10)
    champs_df["f_prev_cd"] = champs_df["f_cd"].shift(10)
    for spell in ["q", "w", "e", "r", "d", "f"]:
        champs_df[f"{spell}_cast"] = \
            champs_df.apply(lambda row: is_spell_cast(row, spell), axis=1)
    champs_df = champs_df.fillna(0)

    # Get X, Y, (X, Y) Distances from Player
    player_df = champs_df[champs_df["name"] == player]
    player_pos = {}
    player_df.apply(lambda row: set_player_pos(player_pos, row), axis=1)
    x_champ_diffs   = champs_df[["time", "position_x"]].apply(\
        lambda row: linear_diff(row,
                                "position_x",
                                player_pos,
                                player_pos_idx=0), axis=1)
    z_champ_diffs   = champs_df[["time", "position_z"]].apply(\
        lambda row: linear_diff(row,
                                "position_z",
                                player_pos,
                                player_pos_idx=1), axis=1)
    x_z_champ_diffs = champs_df[["time", "position_x", "position_z"]].apply(\
        lambda row: multi_diff(row, player_pos), axis=1)

    # Append X, Y, (X, Y) Distances from Player
    champs_df["x_diff_from_player"]   = x_champ_diffs
    champs_df["z_diff_from_player"]   = z_champ_diffs
    champs_df["x_z_diff_from_player"] = x_z_champ_diffs

    return champs_df

def get_table_df(con, player, champs_df, table, cutoff=5.0):
    table_sql = pd.read_sql_query(f"SELECT * FROM {table}", con)
    table_df  = pd.DataFrame(table_sql)
    table_df  = table_df.drop(labels=["game_id"], axis=1)
    table_df  = table_df[table_df["time"] > cutoff]
    table_df  = table_df.drop_duplicates(subset=["time", "obj_type", "name", "net_id"])
    table_df  = get_distances_from_player(table_df, champs_df, player)
    return table_df

def get_target_idx(\
    row, enemy_champs_df_, enemy_minions_df_, jungle_df_pre_, enemy_turrets_df_):
    tm          = row["time"]
    target_type = row["target_type"]
    target_id   = row["target_id"]
    if target_type == "champs":
        cur_units  = enemy_champs_df_[\
            enemy_champs_df_["time"] == tm]
        cur_units  = cur_units.sort_values(["time", "x_z_diff_from_player"], ascending=True)
        cur_units  = cur_units[
            (cur_units["obj_type"] != 0)]
        target_idx = cur_units[cur_units["net_id"] == target_id].index
        target_idx = list(cur_units.index).index(target_idx) + 1
        return target_idx
    elif target_type == "minions":
        cur_units  = enemy_minions_df_[\
            enemy_minions_df_["time"] == tm]
        cur_units  = cur_units.sort_values(["time", "x_z_diff_from_player"], ascending=True)
        cur_units  = cur_units[
            (cur_units["obj_type"] != 0)]
        target_idx = cur_units[cur_units["net_id"] == target_id].index
        target_idx = list(cur_units.index).index(target_idx) + 1
        return target_idx
    elif target_type == "jungle":
        cur_units  = jungle_df_pre_[\
            jungle_df_pre_["time"] == tm]
        cur_units  = cur_units.sort_values(["time", "x_z_diff_from_player"], ascending=True)
        cur_units  = cur_units[
            (cur_units["obj_type"] != 0)]
        target_idx = cur_units[cur_units["net_id"] == target_id].index
        target_idx = list(cur_units.index).index(target_idx) + 1
        return target_idx
    elif target_type == "turrets":
        cur_units  = enemy_turrets_df_[\
            enemy_turrets_df_["time"] == tm]
        cur_units  = cur_units.sort_values(["time", "x_z_diff_from_player"], ascending=True)
        cur_units  = cur_units[
            (cur_units["obj_type"] != 0)]
        target_idx = cur_units[cur_units["net_id"] == target_id].index
        target_idx = list(cur_units.index).index(target_idx) + 1
        return target_idx
    return 0

def collate_observations(con, player, cutoff):
    champs_df   = get_champs_df(con, player, cutoff=cutoff)
    if isinstance(champs_df, int):
        if champs_df == -1:
            return -1
    objects_df  = get_table_df(con, player, champs_df, "objects", cutoff=cutoff)
    missiles_df = get_table_df(con, player, champs_df, "missiles", cutoff=cutoff)
    return champs_df, objects_df, missiles_df

def infer_actions(\
    champs_df, objects_df, missiles_df, player, combined_df_base,
    enemy_champs_df_, enemy_minions_df_, jungle_df_pre_, enemy_turrets_df_):
    player_df = champs_df[champs_df["name"] == player]

    # Infer Auto Attacks
    aa_missile_names = [
        "jinxbasicattack",
        "jinxbasicattack2",
        "jinxqattack",
        "jinxqattack2"]
    aa_missiles = missiles_df[missiles_df["name"].isin(aa_missile_names)]
    aa_missile_dst_s = aa_missiles[["time", "end_position_x", "end_position_z", "x_diff_from_player", "z_diff_from_player", "x_z_diff_from_player"]]
    aa_missile_dst      = aa_missile_dst_s.apply(\
        lambda row: find_aa_target(row, objects_df, champs_df), axis=1)
    aa_missile_dst_type = aa_missile_dst.apply(lambda data: data[0])
    aa_missile_dst_id   = aa_missile_dst.apply(lambda data: data[1])
    aa_missile_dst_s["target_type"] = aa_missile_dst_type
    aa_missile_dst_s["target_id"]   = aa_missile_dst_id

    # Infer W's
    w_missiles    = missiles_df[missiles_df["name"] == "jinxwmissile"].index
    w_missile_tms = missiles_df[missiles_df.index.isin(w_missiles)]["time"]
    w_s           = player_df[player_df["w_cast"] == True]

    # Infer E's
    e_missiles    = missiles_df[missiles_df["name"] == "jinxehit"].index
    e_missile_tms = missiles_df[missiles_df.index.isin(e_missiles)]["time"]
    e_s           = []
    e_missile_filter = [True]
    for i in range(len(e_missiles[:-1])):
        cur_tm  = e_missile_tms.iloc[i]
        next_tm = e_missile_tms.iloc[i + 1]
        if next_tm - cur_tm < 5.0: # Jinx E is never 5 sec or lower so this is guaranteed to always be right
            e_missile_filter.append(False)
        else:
            e_missile_filter.append(True)
    e_missiles    = list(compress(list(e_missiles),    e_missile_filter))
    e_missile_tms = list(compress(list(e_missile_tms), e_missile_filter))
    for e_missile_tm in e_missile_tms:
        current_window = player_df[\
            (abs(player_df["time"] - e_missile_tm) < 2) &
            (player_df["e_cast"] == True)]
        e_s.append(current_window)
    
    # Infer Flashes
    flash_letter = "d" if player_df.iloc[0]["d_name"] == "flash" else "f"
    f_cast_idxs  = player_df[player_df[f"{flash_letter}_cast"] == True].index
    f_cast_tms   = player_df[player_df.index.isin(f_cast_idxs)]["time"]
    flashes      = []
    for cast_tm in f_cast_tms:
        current_window = player_df[\
            (abs(player_df["time"] - cast_tm) < 2) &
            (player_df["position_x_z_delta"] > 300.0)]
        flashes.append(current_window.iloc[0])
    
    # Infer Wards
    player_frame = player_df[player_df["name"] == player]
    player_team  = player_frame.iloc[0]["team"]
    ward_names = ["jammerdevice",
                "yellowtrinket",
                "ward"]
    allied_wards = objects_df[\
        (objects_df["team"] == player_team) &
        (objects_df["name"].isin(ward_names)) &
        (objects_df["x_z_diff_from_player"] <= 600)].index
    allied_ward_tms = objects_df[objects_df.index.isin(allied_wards)]["time"]
    wards = []
    try:
        wards = [objects_df[objects_df.index == allied_wards[0]].iloc[0]]
        for i in range(len(allied_wards[:-1])):
            cur_tm  = allied_ward_tms.iloc[i]
            next_tm = allied_ward_tms.iloc[i + 1]
            if next_tm - cur_tm < 60.0: # Ward duration never lower than 90secs, so this should be fine
                pass
            else:
                wards.append(objects_df[objects_df.index == allied_wards.index])
    except Exception as e:
        print(e)

    # Combine auto attacks
    valid_aa_missile_dst_s = aa_missile_dst_s[aa_missile_dst_s["target_id"] != -1]
    auto_attack_df_base    = valid_aa_missile_dst_s[["time", "x_diff_from_player", "z_diff_from_player", "x_z_diff_from_player", "target_type", "target_id"]]
    target_idx = auto_attack_df_base.apply(\
        lambda row: get_target_idx(row, enemy_champs_df_, enemy_minions_df_, jungle_df_pre_, enemy_turrets_df_), axis=1)
    target_type_enum = ["champs", "minions", "turrets", "jungle", "other"]
    auto_attack_df_base = aa_missile_dst_s[["time", "target_type"]]
    auto_attack_df_base["target_idx"] = target_idx
    auto_attack_df_base["target_type"] = \
        auto_attack_df_base["target_type"].apply(\
            lambda target_type_str: \
                target_type_enum.index(target_type_str)
                if target_type_str in target_type_enum
                else -1)
    auto_attack_df_base["using_auto"] = 1
    auto_attack_df_base = auto_attack_df_base.dropna()

    # Combine Q
    q_spell_df_base = player_df[player_df["q_cast"] == True]
    q_spell_df_base = q_spell_df_base[["time"]]
    q_spell_df_base["using_q"] = 1
    w_spell_df_base = missiles_df[missiles_df.index.isin(w_missiles)]
    w_spell_df_base = w_spell_df_base[["time", "x_diff_from_player", "z_diff_from_player"]]
    pos_x_delta_digital = \
        w_spell_df_base["x_diff_from_player"].apply(lambda val: digitize_delta(val))
    pos_z_delta_digital = \
        w_spell_df_base["z_diff_from_player"].apply(lambda val: digitize_delta(val))

    # Combine W
    w_spell_df_base["w_x_diff_digital"] = pos_x_delta_digital
    w_spell_df_base["w_z_diff_digital"] = pos_z_delta_digital
    w_spell_df_base = w_spell_df_base[["time", "w_x_diff_digital", "w_z_diff_digital"]]
    w_spell_df_base["using_w"] = 1
    e_spell_df_base = missiles_df[missiles_df.index.isin(e_missiles)]
    e_spell_df_base = e_spell_df_base[["time", "x_diff_from_player", "z_diff_from_player"]]
    pos_x_delta_digital = \
        e_spell_df_base["x_diff_from_player"].apply(lambda val: digitize_delta(val))
    pos_z_delta_digital = \
        e_spell_df_base["z_diff_from_player"].apply(lambda val: digitize_delta(val))
    
    # Combine E
    e_spell_df_base["e_x_diff_digital"] = pos_x_delta_digital
    e_spell_df_base["e_z_diff_digital"] = pos_z_delta_digital
    e_spell_df_base = e_spell_df_base[["time", "e_x_diff_digital", "e_z_diff_digital"]]
    e_spell_df_base["using_e"] = 1

    # Combine flash
    if flashes:
        d_spell_df_base = pd.DataFrame(flashes)
        d_spell_df_base = d_spell_df_base[["time", "position_x_delta_digital", "position_z_delta_digital"]]
        d_spell_df_base = d_spell_df_base.rename(\
            columns={
                "position_x_delta_digital": "d_x_diff_digital",
                "position_z_delta_digital": "d_z_diff_digital"})
        d_spell_df_base["using_d"] = 1
    else:
        d_spell_df_base = pd.DataFrame(
            columns=["time", "d_x_diff_digital", "d_z_diff_digital", "using_d"])

    # Combine secondary spell
    f_spell_df_base = player_df[player_df["f_cast"] == True]
    f_spell_df_base = f_spell_df_base[["time"]]
    f_spell_df_base["using_f"] = 1

    # Combine warding
    ward_idxs = [w.name for w in wards]
    ward_spell_df_base = objects_df[objects_df.index.isin(ward_idxs)]
    ward_spell_df_base = ward_spell_df_base[["time", "x_diff_from_player", "z_diff_from_player"]]
    pos_x_delta_digital = \
        ward_spell_df_base["x_diff_from_player"].apply(lambda val: digitize_delta(val))
    pos_z_delta_digital = \
        ward_spell_df_base["z_diff_from_player"].apply(lambda val: digitize_delta(val))
    ward_spell_df_base["ward_x_diff_digital"] = pos_x_delta_digital
    ward_spell_df_base["ward_z_diff_digital"] = pos_z_delta_digital
    ward_spell_df_base = ward_spell_df_base[["time", "ward_x_diff_digital", "ward_z_diff_digital"]]
    ward_spell_df_base["using_ward"] = 1

    # Combine recalling
    recall_df_base = player_df[player_df["recallState"] > 0]
    recall_df_base = recall_df_base[["time"]]
    recall_df_base["using_recall"] = 1

    # Combine movement
    movement_df_base = player_df[["time", "position_x_delta_digital", "position_z_delta_digital"]]
    movement_df_base = movement_df_base.rename(columns={
        "position_x_delta_digital": "movement_x_delta_digital",
        "position_z_delta_digital": "movement_z_delta_digital"})
        
    # Combine all actions
    action_df_list = [
        auto_attack_df_base,
        q_spell_df_base,
        w_spell_df_base,
        e_spell_df_base,
        d_spell_df_base,
        f_spell_df_base,
        ward_spell_df_base,
        recall_df_base,
        movement_df_base]
    for i in range(len(action_df_list)):
        cur_act_df = action_df_list[i]
        combined_df_base = \
            combined_df_base.merge(
                cur_act_df,
                on="time",
                how="left",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_df_base = combined_df_base.fillna(0)

    return combined_df_base

def get_combined_champ_obs(\
    champs_df, player_df, drop_columns, player, enemy_team):

    # Combine allied champ obs
    allied_champs_df      = champs_df[champs_df["team"] == player_df.iloc[0]["team"]]
    allied_champs_df      = allied_champs_df[allied_champs_df["name"] != player]
    allied_champs_df      = allied_champs_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    allied_champs_df_base = champs_df[champs_df["name"] == player]
    allied_champs_df_base = allied_champs_df_base.drop(labels=drop_columns, axis=1)
    allied_champs_df = allied_champs_df.drop(labels=drop_columns, axis=1)
    allied_champ_count = 4
    for i in range(allied_champ_count):
        cur_allied_champs_df  = allied_champs_df.iloc[i::allied_champ_count, :]
        allied_champs_df_base = \
            allied_champs_df_base.merge(
                cur_allied_champs_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))

    # Combine enemy champ obs
    enemy_champs_df      = champs_df[champs_df["team"] == enemy_team]
    enemy_champs_df      = enemy_champs_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    enemy_champs_df_     = enemy_champs_df
    enemy_champs_df_base = enemy_champs_df.iloc[0::5, :]
    enemy_champs_df_base = enemy_champs_df_base.drop(labels=drop_columns, axis=1)
    enemy_champs_df = enemy_champs_df.drop(labels=drop_columns, axis=1)
    enemy_champ_count = 5
    for i in range(1, enemy_champ_count):
        cur_enemy_champs_df  = enemy_champs_df.iloc[i::enemy_champ_count, :]
        enemy_champs_df_base = \
            enemy_champs_df_base.merge(
                cur_enemy_champs_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    enemy_champs_df      = champs_df[champs_df["team"] == enemy_team]
    enemy_champs_df      = enemy_champs_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    enemy_champs_df_     = enemy_champs_df
    enemy_champs_df_base = enemy_champs_df.iloc[0::5, :]
    drop_columns = ["obj_type", "obj_id", "net_id", "name", "q_name", "w_name", "e_name", "r_name", "d_name", "f_name"]
    enemy_champs_df_base = enemy_champs_df_base.drop(labels=drop_columns, axis=1)
    enemy_champs_df = enemy_champs_df.drop(labels=drop_columns, axis=1)
    enemy_champ_count = 5
    for i in range(1, enemy_champ_count):
        cur_enemy_champs_df  = enemy_champs_df.iloc[i::enemy_champ_count, :]
        enemy_champs_df_base = \
            enemy_champs_df_base.merge(
                cur_enemy_champs_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_champs_df_base = \
        allied_champs_df_base.merge(
            enemy_champs_df_base,
            on="time",
            suffixes=('_', '__'))
    return enemy_champs_df_, combined_champs_df_base

def get_combined_minion_obs(\
    objects_df, player_df, allied_minions_count, enemy_team, enemy_minions_count):

    # Allied minion obs
    allied_minions_df      = objects_df[\
        (objects_df["team"] == player_df.iloc[0]["team"]) &
        (objects_df["obj_type"] == "minions") &
        (objects_df["is_alive"] == 1)]
    allied_minions_tms     = allied_minions_df["time"].value_counts().iloc[::-1]
    allied_minions_df      = allied_minions_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    allied_minions_df_lst  = []
    for i in range(len(allied_minions_tms)):
        tm    = allied_minions_tms.index[i]
        count = allied_minions_tms.iloc[i]
        cur_data = allied_minions_df[allied_minions_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < allied_minions_count:
            cur_data_padding = [[tm] + [0] * 17] * (allied_minions_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:allied_minions_count]
        allied_minions_df_lst += cur_data
    allied_minions_df_pre = \
        pd.DataFrame(
            allied_minions_df_lst,
            columns=allied_minions_df.columns)
    allied_minions_df_pre = allied_minions_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    allied_minions_df_base = allied_minions_df_pre.iloc[0::allied_minions_count, :]
    for i in range(1, allied_minions_count):
        cur_allied_minions_df  = allied_minions_df_pre.iloc[i::allied_minions_count, :]
        allied_minions_df_base = \
            allied_minions_df_base.merge(
                cur_allied_minions_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))

    # Enemy minion obs
    enemy_minions_df      = objects_df[\
        (objects_df["team"] == enemy_team) &
        (objects_df["obj_type"] == "minions")]
    enemy_minions_tms     = enemy_minions_df["time"].value_counts().iloc[::-1]
    enemy_minions_df      = enemy_minions_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    enemy_minions_df_     = enemy_minions_df
    enemy_minions_df_lst  = []
    for i in range(len(enemy_minions_tms)):
        tm    = enemy_minions_tms.index[i]
        count = enemy_minions_tms.iloc[i]
        cur_data = enemy_minions_df[enemy_minions_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < enemy_minions_count:
            cur_data_padding = [[tm] + [0] * 17] * (enemy_minions_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:enemy_minions_count]
        enemy_minions_df_lst += cur_data
    enemy_minions_df_pre = \
        pd.DataFrame(
            enemy_minions_df_lst,
            columns=enemy_minions_df.columns)
    enemy_minions_df_pre = enemy_minions_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    enemy_minions_df_base = enemy_minions_df_pre.iloc[0::enemy_minions_count, :]
    for i in range(1, enemy_minions_count):
        cur_enemy_minions_df  = enemy_minions_df_pre.iloc[i::enemy_minions_count, :]
        enemy_minions_df_base = \
            enemy_minions_df_base.merge(
                cur_enemy_minions_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_minions_df_base = \
        allied_minions_df_base.merge(
            enemy_minions_df_base,
            on="time",
            suffixes=('_', '__'))
    
    return enemy_minions_df_, combined_minions_df_base

def get_combined_turret_obs(\
    objects_df, player_df, allied_turrets_count, enemy_turrets_count, enemy_team):

    # Allied turret obs
    allied_turrets_df      = objects_df[\
        (objects_df["team"] == player_df.iloc[0]["team"]) &
        (objects_df["obj_type"] == "turrets")]
    allied_turrets_tms     = allied_turrets_df["time"].value_counts().iloc[::-1]
    allied_turrets_df      = allied_turrets_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    allied_turrets_df_lst  = []
    for i in range(len(allied_turrets_tms)):
        tm    = allied_turrets_tms.index[i]
        count = allied_turrets_tms.iloc[i]
        cur_data = allied_turrets_df[allied_turrets_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < allied_turrets_count:
            cur_data_padding = [[tm] + [0] * 17] * (allied_turrets_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:allied_turrets_count]
        allied_turrets_df_lst += cur_data
    allied_turrets_df_pre = \
        pd.DataFrame(
            allied_turrets_df_lst,
            columns=allied_turrets_df.columns)
    allied_turrets_df_pre = allied_turrets_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    allied_turrets_df_base = allied_turrets_df_pre.iloc[0::allied_turrets_count, :]
    for i in range(1, allied_turrets_count):
        cur_allied_turrets_df  = allied_turrets_df_pre.iloc[i::allied_turrets_count, :]
        allied_turrets_df_base = \
            allied_turrets_df_base.merge(
                cur_allied_turrets_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))

    # Enemy turret obs
    enemy_turrets_df      = objects_df[\
        (objects_df["team"] == enemy_team) &
        (objects_df["obj_type"] == "turrets")]
    enemy_turrets_tms     = enemy_turrets_df["time"].value_counts().iloc[::-1]
    enemy_turrets_df      = enemy_turrets_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    enemy_turrets_df_     = enemy_turrets_df
    enemy_turrets_df_lst  = []
    for i in range(len(enemy_turrets_tms)):
        tm    = enemy_turrets_tms.index[i]
        count = enemy_turrets_tms.iloc[i]
        cur_data = enemy_turrets_df[enemy_turrets_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < enemy_turrets_count:
            cur_data_padding = [[tm] + [0] *17] * (enemy_turrets_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:enemy_turrets_count]
        enemy_turrets_df_lst += cur_data
    enemy_turrets_df_pre = \
        pd.DataFrame(
            enemy_turrets_df_lst,
            columns=enemy_turrets_df.columns)
    enemy_turrets_df_pre = enemy_turrets_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    enemy_turrets_df_base = enemy_turrets_df_pre.iloc[0::enemy_turrets_count, :]
    for i in range(1, enemy_turrets_count):
        cur_enemy_turrets_df  = enemy_turrets_df_pre.iloc[i::enemy_turrets_count, :]
        enemy_turrets_df_base = \
            enemy_turrets_df_base.merge(
                cur_enemy_turrets_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_turrets_df_base = \
        allied_turrets_df_base.merge(
            enemy_turrets_df_base,
            on="time",
            suffixes=('_', '__'))

    return enemy_turrets_df_, combined_turrets_df_base

def get_combined_jungle_obs(objects_df, jungle_count):
    jungle_df      = objects_df[\
        (objects_df["obj_type"] == "jungle") &
        (objects_df["is_alive"] == 1)]
    jungle_tms     = jungle_df["time"].value_counts().iloc[::-1]
    jungle_df      = jungle_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    jungle_df_lst  = []
    for i in range(len(jungle_tms)):
        tm    = jungle_tms.index[i]
        count = jungle_tms.iloc[i]
        cur_data = jungle_df[jungle_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < jungle_count:
            cur_data_padding = [[tm] + [0] * 17] * (jungle_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:jungle_count]
        jungle_df_lst += cur_data
    jungle_df_pre = \
        pd.DataFrame(
            jungle_df_lst,
            columns=jungle_df.columns)
    jungle_df_pre_ = jungle_df_pre
    jungle_df_pre = jungle_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    jungle_df_base = jungle_df_pre.iloc[0::jungle_count, :]
    for i in range(1, jungle_count):
        cur_jungle_df  = jungle_df_pre.iloc[i::jungle_count, :]
        jungle_df_base = \
            jungle_df_base.merge(
                cur_jungle_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_jungle_df_base = jungle_df_base
    return jungle_df_pre_, combined_jungle_df_base

def get_combine_other_obs(objects_df, other_count):
    other_df      = objects_df[\
        (objects_df["obj_type"] == "other") &
        (objects_df["name"] == "yellowtrinket") &
        (objects_df["is_alive"] == 1)]
    other_tms     = other_df["time"].value_counts().iloc[::-1]
    other_df      = other_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    other_df_     = other_df
    other_df_lst  = []
    for i in range(len(other_tms)):
        tm    = other_tms.index[i]
        count = other_tms.iloc[i]
        cur_data = other_df[other_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < other_count:
            cur_data_padding = [[tm] + [0] * 17] * (other_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:other_count]
        other_df_lst += cur_data
    other_df_pre = \
        pd.DataFrame(
            other_df_lst,
            columns=other_df.columns)
    other_df_pre = other_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    other_df_base = other_df_pre.iloc[0::other_count, :]
    for i in range(1, other_count):
        cur_other_df  = other_df_pre.iloc[i::other_count, :]
        other_df_base = \
            other_df_base.merge(
                cur_other_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_other_df_base = other_df_base
    return other_df_, combined_other_df_base

def combine_missile_obs(missiles_df, missile_count):
    missile_df      = missiles_df[\
        (missiles_df["obj_type"] == "missiles") &
        (missiles_df["is_alive"] == 1)]
    missile_tms     = missile_df["time"].value_counts().iloc[::-1]
    missile_df      = missile_df.sort_values(["time", "x_z_diff_from_player"], ascending=True)
    missile_df_     = missile_df
    missile_df_lst  = []
    for i in range(len(missile_tms)):
        tm    = missile_tms.index[i]
        count = missile_tms.iloc[i]
        cur_data = missile_df[missile_df["time"] == tm]
        cur_data = cur_data.values.tolist()
        if count < missile_count:
            cur_data_padding = [[tm] + [0] * 17] * (missile_count - count)
            cur_data += cur_data_padding
        else:
            cur_data = cur_data[0:missile_count]
        missile_df_lst += cur_data
    missile_df_pre = \
        pd.DataFrame(
            missile_df_lst,
            columns=missile_df.columns)
    missile_df_pre = missile_df_pre.drop(labels=["obj_type", "name", "obj_id", "net_id"], axis=1)
    missile_df_base = missile_df_pre.iloc[0::missile_count, :]
    for i in range(1, missile_count):
        cur_missile_df  = missile_df_pre.iloc[i::missile_count, :]
        missile_df_base = \
            missile_df_base.merge(
                cur_missile_df,
                on="time",
                suffixes=('_0' if i == 0 else '', f'_{i+1}'))
    combined_missile_df_base = missile_df_base
    return missile_df_, combined_missile_df_base

def combine_obs_acts(champs_df, objects_df, missiles_df, player):
    # Combined dataset settings
    player_df  = champs_df[champs_df["name"] == player]
    enemy_team = 100 if player_df.iloc[0]["team"] == 200 else 100
    drop_columns = ["obj_type", "obj_id", "net_id", "name", "q_name", "w_name", "e_name", "r_name", "d_name", "f_name"]

    # Unit limits
    minions_count = 30
    turrets_count = 11
    jungle_count  = 24
    other_count   = 5
    missile_count = 30
    allied_minions_count = minions_count
    enemy_minions_count  = minions_count
    allied_turrets_count = turrets_count
    enemy_turrets_count  = turrets_count

    # Combined champ obs
    enemy_champs_df_, combined_champs_df_base = get_combined_champ_obs(\
        champs_df, player_df, drop_columns, player, enemy_team)

    # Combine minion obs
    enemy_minions_df_, combined_minions_df_base = get_combined_minion_obs(\
        objects_df, player_df, allied_minions_count, enemy_team, enemy_minions_count)
    
    # Combine turret obs
    enemy_turrets_df_, combined_turrets_df_base = get_combined_turret_obs(\
        objects_df, player_df, allied_turrets_count, enemy_turrets_count, enemy_team)

    # Combine jungle obs
    enemy_jungle_df_, combined_jungle_df_base = get_combined_jungle_obs(\
        objects_df, jungle_count)

    # Combine other obs
    other_df_, combined_other_df_base = get_combine_other_obs(objects_df, other_count)

    # Combine missile obs
    missiles_df_, combined_missile_df_base = combine_missile_obs(missiles_df, missile_count)

    # Combine all obs
    combined_df_base = \
        combined_champs_df_base.merge(
            combined_minions_df_base,
            on="time",
            how="left",
            suffixes=('_', '__'))
    combined_df_base = \
        combined_df_base.merge(
            combined_turrets_df_base,
            on="time",
            how="left",
            suffixes=('_', '__'))
    combined_df_base = \
        combined_df_base.merge(
            combined_jungle_df_base,
            on="time",
            how="left",
            suffixes=('_', '__'))
    combined_df_base = \
        combined_df_base.merge(
            combined_other_df_base,
            on="time",
            how="left",
            suffixes=('_', '__'))
    combined_df_base = \
        combined_df_base.merge(
            combined_missile_df_base,
            on="time",
            how="left",
            suffixes=('_', '__'))

    return \
        enemy_champs_df_, \
        enemy_minions_df_, \
        enemy_turrets_df_, \
        enemy_jungle_df_, \
        other_df_, \
        missiles_df_, \
        combined_df_base

def go(db_path, player, cutoff, out_path):
    con = sqlite3.connect(db_path)

    # Collate observations
    print("Collate obs...")
    if collate_observations(con, player, cutoff) != -1:
        champs_df, objects_df, missiles_df = collate_observations(con, player, cutoff)
    else:
        return -1

    # Combine obs/acts
    print("Combine obs...")
    enemy_champs_df_, \
    enemy_minions_df_, \
    enemy_turrets_df_, \
    jungle_df_, \
    other_df_, \
    missiles_df_, \
    combined_df_base = combine_obs_acts(champs_df, objects_df, missiles_df, player)

    # Infer actions
    print("Combine acts...")
    combined_df_base = \
        infer_actions(\
            champs_df, objects_df, missiles_df, player, combined_df_base,
            enemy_champs_df_, enemy_minions_df_, jungle_df_, enemy_turrets_df_)

    # Append global
    print("Append global...")
    first_minion_spawn = 60 + 5
    minion_spawn_times = combined_df_base["time"].apply(\
    lambda tm: 30 - ((tm - first_minion_spawn) % 30)
               if tm >= first_minion_spawn
               else first_minion_spawn - tm)
    combined_df_base.insert(1, "minion_spawn_countdown", minion_spawn_times)
    combined_df_base = combined_df_base.fillna(0)
    
    # Save dataset...
    print("Save dataset...")
    player_team = champs_df[champs_df["name"] == player].iloc[0]["team"]
    fname = os.path.basename(db_path).split(".")[0]
    combined_df_base = combined_df_base.astype("float16")
    outname_pkl = f"./{fname}_{player}_{player_team}.pkl"
    outname_pkl = os.path.join(out_path, outname_pkl)
    combined_df_base.to_pickle(outname_pkl)

    return 0