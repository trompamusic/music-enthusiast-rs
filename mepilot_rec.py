#!/usr/bin/env python
# encoding: utf-8

import json
import pandas as pd
import argparse
import urllib.request

from datetime import datetime


URL_ANNOTATIONS = "https://trompa-mtg.upf.edu/data/annotations/{}_emotion.json"

QUADR_MAP = {("1", "1"): 1,
             ("1", "-1"): 2,
             ("-1", "-1"): 3,
             ("-1", "1"): 4}


def import_recommendations(recs):
    """
    """
    df = pd.read_csv(recs, delimiter="\t")
    return df


def import_annotations(anns):
    """
    """
    DictAnns = {}

    with open(anns) as inf:
        doc = json.load(inf)

    for c, ann in enumerate(doc['annotations']):
        uid = ann["userid"]
        tid = "_".join([ann['externalID'], ann['internalID']])
        a_val = (ann["valenceValue"], ann["arousalValue"])
        if uid not in DictAnns:
            DictAnns[uid] = []
        DictAnns[uid].append((tid, a_val))

    return DictAnns


def find_user_last_annotation(userid):
    """
    """
    ann_time_old = datetime(2000, 1, 1, 1, 1, 1)
    ann_old = None
    for ann in DictAnns[userid]:
        with urllib.request.urlopen(URL_ANNOTATIONS.format(ann[0])) as url:
            data = json.loads(url.read().decode())

            try:
                ann_time = data["dataset"][userid]["timestamp"]
            except KeyError:
                # If annotation not found in MTG server, continue
                continue

            ann_time_obj = datetime.fromtimestamp(int(ann_time))
            if ann_time_obj > ann_time_old:
                ann_time_old = ann_time_obj
                ann_old = ann

    return ann_old


def arg_parser():
    """
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--userid", type=str, dest='userid',
                        help="User ID for recommedantion")
    parser.add_argument("-a", "--annotations", type=str, dest='anns',
                        help="Annotation file")
    parser.add_argument("-r", "--recs", type=str, dest='recs',
                        help="Tracks for recommedantions")
    parser.add_argument('-s', '--seen', nargs='+',
                        help="Already recommended tracks")
    parser.add_argument("-l", "--logfile", type=str,
                        help="Log file path")

    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = arg_parser()

    seen = args.seen
    if not seen:
        seen = []

    # Import annotations from  file
    DictAnns = import_annotations(args.anns)
    # import recommendation from file
    recs = import_recommendations(args.recs)
    # Find last annotations from MTG server
    ann = find_user_last_annotation(args.userid)

    # Filter recommendation by quadrant and sort by popularity
    recs_list = recs[recs["quadrant"] == QUADR_MAP[ann[1]]].sort_values(
                        by="popularity", ascending=False)["cdr_track_num"]

    # Find and print new recommendation
    new_rec = None
    for tid in recs_list:
        if tid not in seen:
            new_rec = tid
            break

    if new_rec:
        print(new_rec)
    else:
        "No recommendation for user {}".format(args.userid)
