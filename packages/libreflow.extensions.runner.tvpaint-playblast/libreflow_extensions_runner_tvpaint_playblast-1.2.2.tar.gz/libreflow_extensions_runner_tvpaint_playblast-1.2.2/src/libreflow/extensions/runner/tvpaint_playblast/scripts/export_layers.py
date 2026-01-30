import os
import sys
import argparse
import fileseq
import shutil
from pathlib import Path
from pytvpaint import george
from pytvpaint.project import Project


def process_remaining_args(args):
    parser = argparse.ArgumentParser(
        description='TVPaint Render Arguments'
    )
    parser.add_argument('--output-path', dest='output_path')
    parser.add_argument('--filter-layers', dest='filter_layers', action="append")
    parser.add_argument('--all-frames', dest='all_frames', action='store_true')
    parser.add_argument('--delete-json', dest='delete_json', action='store_true')

    values, _ = parser.parse_known_args(args)

    return [values.output_path, values.filter_layers, values.all_frames, values.delete_json]

OUTPUT_PATH, FILTER_LAYERS, ALL_FRAMES, DELETE_JSON = process_remaining_args(sys.argv)

project = Project.current_project()
clip = project.current_clip

layers = None
if FILTER_LAYERS:
    # Get layer objects
    layers = []
    for name in FILTER_LAYERS:
        layer = clip.get_layer(by_name=name)
        if layer:
            layers.append(layer)

# Export layers in image sequence and with layers ordering in a json file
clip.export_json(
    OUTPUT_PATH,
    george.SaveFormat.PNG,
    folder_pattern="%3li_%ln",
    file_pattern="%ln.%4ii",
    layer_selection=layers,
    all_images=True,
)

# Duplicate frames if all frames option are enabled
if ALL_FRAMES:
    output_dir = Path(OUTPUT_PATH).parent.absolute()
    for name in os.listdir(output_dir):
        dir_path = os.path.join(output_dir, name)
        if os.path.isdir(dir_path):

            first_frame = os.path.join(dir_path, os.listdir(dir_path)[0])
            seq = fileseq.FilePathSequence(
                fileseq.findSequenceOnDisk(first_frame)
            )

            layer = clip.get_layer(by_name=seq.basename()[:-1])

            previous_frame = seq[0]

            end_frame = None
            if clip.mark_out is not None:
                if layer.end > clip.mark_out:
                    end_frame = clip.mark_out
            elif layer.end > project.end_frame:
                end_frame = project.end_frame
            
            if end_frame is None:
                end_frame = layer.end

            for frame_n in range(layer.start, end_frame + 1):
                frame = seq.frame(frame_n)
                if frame == previous_frame:
                    continue
                if frame.is_file():
                    previous_frame = frame
                else:
                    shutil.copy(previous_frame, frame)

if DELETE_JSON:
    os.remove(OUTPUT_PATH)

project.close_all(True)