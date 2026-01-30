import sys
import os
import argparse
import json
from pytvpaint.project import Project


def process_remaining_args(args):
    parser = argparse.ArgumentParser(
        description='TVPaint Fetch Arguments'
    )
    parser.add_argument('--output-path', dest='output_path')

    values, _ = parser.parse_known_args(args)

    return [values.output_path]


OUTPUT_PATH = process_remaining_args(sys.argv)[0]

project = Project.current_project()
clip = project.current_clip

layers_list = []
for layer in clip.layers:
    layers_list.append(dict(
        name=layer.name,
        start=layer.start,
        end=layer.end
    ))

OUTPUT_PATH = os.path.join(OUTPUT_PATH, "layers.json")
with open(OUTPUT_PATH, "w+") as f:
    layers_dict = dict(layers=layers_list)
    json.dump(layers_dict, f)

project.close_all(True)