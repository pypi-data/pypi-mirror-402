import os
from pathlib import Path
import subprocess
import re
import tempfile
import psutil
import shutil
import time
import json

from kabaret import flow
from kabaret.app import resources
from kabaret.app.ui.gui.widgets.flow.flow_view import QtWidgets
from kabaret.flow_contextual_dict import get_contextual_dict
from libreflow.baseflow.file import (
    GenericRunAction,
    TrackedFile,
    TrackedFolder,
    FileRevisionNameChoiceValue,
    MarkImageSequence,
    FileJob
)
from libreflow.baseflow.task import Task
from libreflow.baseflow.site import SiteJobsPoolNames
from libreflow.baseflow.users import PresetSessionValue
from libreflow.utils.os import remove_folder_content

from . import scripts


class RenderQualityChoiceValue(flow.values.ChoiceValue):
    CHOICES = ["Final"]  # ['Preview','Final']


class RenderTvPaintPlayblast(flow.Action):
    ICON = ("icons.libreflow", "tvpaint")

    _file = flow.Parent()
    _files = flow.Parent(2)
    _task = flow.Parent(3)
    _shot = flow.Parent(5)
    _sequence = flow.Parent(7)

    revision = flow.Param(None, FileRevisionNameChoiceValue)
    render_quality = flow.Param("Final", RenderQualityChoiceValue)

    with flow.group("Advanced settings"):
        start_frame = flow.IntParam()
        end_frame = flow.IntParam()
        show_reference = flow.BoolParam(False)
        keep_existing_frames = flow.BoolParam(True)

    def allow_context(self, context):
        return (
            context
            and self._file.format.get() == "tvpp"
            and not self._file.is_empty(on_current_site=True, published_only=True)
        )

    def get_buttons(self):
        if self._task.name() == "exposition":
            self.show_reference.set(True)

        self.revision.revert_to_default()
        self.start_frame.revert_to_default()
        self.end_frame.revert_to_default()
        return ["Render", "Cancel"]

    def ensure_render_folder(self):
        folder_name = self._file.display_name.get().split(".")[0]
        folder_name += "_render"
        if self.render_quality.get() == "Preview":
            folder_name += "_preview"

        if not self._files.has_folder(folder_name):
            self._task.create_folder_action.folder_name.set(folder_name)
            self._task.create_folder_action.category.set("Outputs")
            self._task.create_folder_action.tracked.set(True)
            self._task.create_folder_action.run(None)

        return self._files[folder_name]

    def ensure_render_folder_revision(self):
        folder = self.ensure_render_folder()
        revision_name = self.revision.get()
        source_revision = self._file.get_revision(self.revision.get())

        if not folder.has_revision(revision_name):
            revision = folder.add_revision(revision_name)
            folder.set_current_user_on_revision(revision_name)
        else:
            revision = folder.get_revision(revision_name)

        revision.comment.set(source_revision.comment.get())

        folder.ensure_last_revision_oid()

        self._files.touch()

        return revision

    def start_tvpaint(self, path):
        start_action = self._task.start_tvpaint
        start_action.file_path.set(path)
        ret = start_action.run(None)
        self.tvpaint_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )

    def execute_render_script(
        self, path, start_frame, end_frame, render_quality, show_reference
    ):
        exec_script = self._file.execute_render_playblast_script
        exec_script.output_path.set(path)
        exec_script.start_frame.set(start_frame)
        exec_script.end_frame.set(end_frame)
        exec_script.render_quality.set(render_quality)
        exec_script.show_ref.set(show_reference)
        ret = exec_script.run(None)
        self.script_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )

    def check_audio(self):
        mng = self.root().project().get_task_manager()
        default_files = mng.default_files.get()
        for file_name, task_names in default_files.items():
            if "animatic.wav" in file_name:
                task = default_files[file_name][0]
                file_mapped_name = file_name.replace(".", "_")
                break

        if not self._shot.tasks.has_mapped_name(task):
            return None
        self.animatic_task = self._shot.tasks[task]

        name, ext = file_mapped_name.split("_")

        if not self.animatic_task.files.has_file(name, ext):
            return None
        f = self.animatic_task.files[file_mapped_name]
        rev = f.get_head_revision()
        rev_path = rev.get_path()

        if os.path.exists(rev_path):
            export_audio = self._file.export_ae_audio
            export_audio._audio_path.set(rev_path)
            return True
        else:
            return False

    def _export_audio(self):
        export_audio = self._file.export_ae_audio
        ret = export_audio.run("Export")
        return ret

    def _mark_image_sequence(self, folder_name, revision_name, render_pid):
        mark_sequence_wait = self._file.mark_image_sequence_wait
        mark_sequence_wait.folder_name.set(folder_name)
        mark_sequence_wait.revision_name.set(revision_name)
        for pid in render_pid:
            mark_sequence_wait.wait_pid(pid)
        mark_sequence_wait.run(None)

    def run(self, button):
        if button == "Cancel":
            return

        # Raise exception if pytvpaint plugin is not found in the installation folder
        self._task.start_tvpaint._check_env_priority('TVPAINT_EXEC_PATH')

        if "TVPAINT_EXEC_PATH" in os.environ:
            tvpaint_path = os.environ["TVPAINT_EXEC_PATH"]

            plugins_path = Path(Path(tvpaint_path).parent).joinpath("plugins")

            if os.path.exists(plugins_path) is False:
                raise Exception(f"[RUNNER] No plugins folder find on the installation folder. Please install pytvpaint plugin. - '{plugins_path}'")

            dll_file = any(
                file_name
                for file_name in os.listdir(plugins_path)
                if re.match("(?:tvpaint-rpc).*(?:\.dll)$", file_name)
            )
            if not dll_file:
                raise Exception(f"[RUNNER] pytvpaint plugin is not find on the installation folder - '{plugins_path}'")

        rev = self._file.get_revision(self.revision.get())
        self.start_tvpaint(rev.get_path())

        output_name = f"{self._sequence.name()}_{self._shot.name()}.#.png"
        output_path = os.path.join(
            self.ensure_render_folder_revision().get_path(), output_name
        )

        if (
            os.path.exists(os.path.split(output_path)[0])
            and self.keep_existing_frames.get() is False
        ):
            remove_folder_content(os.path.split(output_path)[0])

        self.execute_render_script(
            output_path,
            self.start_frame.get(),
            self.end_frame.get(),
            self.render_quality.get(),
            self.show_reference.get(),
        )
        if not self.check_audio():
            self._export_audio()

        # Configure image sequence marking
        folder_name = self._file.name()[: -len(self._file.format.get())]
        folder_name += "render"
        if self.render_quality.get() == "Preview":
            folder_name += "_preview"
        revision_name = self.revision.get()
        self._mark_image_sequence(
            folder_name,
            revision_name,
            render_pid=[self.tvpaint_runner["pid"], self.script_runner["pid"]],
        )


class ExportAudio(flow.Action):
    _file = flow.Parent()
    _files = flow.Parent(2)
    _task = flow.Parent(3)
    _shot = flow.Parent(5)

    _audio_path = flow.Param("")

    def allow_context(self, context):
        return False

    def get_latest_animatic(self):
        mng = self.root().project().get_task_manager()
        default_files = mng.default_files.get()
        for file_name, task_names in default_files.items():
            if "animatic" in file_name:
                if "wav" in file_name:
                    continue
                task = default_files[file_name][0]
                file_mapped_name = file_name.replace(".", "_")
                break

        if not self._shot.tasks.has_mapped_name(task):
            return None
        self.animatic_task = self._shot.tasks[task]

        name, ext = file_mapped_name.split("_")

        if not self.animatic_task.files.has_file(name, ext):
            return None
        f = self.animatic_task.files[file_mapped_name]

        rev = f.get_head_revision(sync_status="Available")
        return rev if rev is not None else None

    def get_default_file(self):
        mng = self.root().project().get_task_manager()
        default_files = mng.default_files.get()
        for file_name, task_names in default_files.items():
            if "animatic.wav" in file_name:
                task = default_files[file_name][0]
                file_mapped_name = file_name.replace(".", "_")
                break

        dft_task = mng.default_tasks[task]
        if not dft_task.files.has_mapped_name(file_mapped_name):  # check default file
            # print(f'Scene Builder - default task {task_name} has no default file {filename} -> use default template')
            return None

        dft_file = dft_task.files[file_mapped_name]
        return dft_file

    def _ensure_file(self, name, format, path_format, source_revision):
        file_name = "%s_%s" % (name, format)

        if self.animatic_task.files.has_file(name, format):
            f = self.animatic_task.files[file_name]
        else:
            f = self.animatic_task.files.add_file(
                name=name,
                extension=format,
                tracked=True,
                default_path_format=path_format,
            )

        f.file_type.set("Works")

        if f.has_revision(source_revision.name()):
            audio_revision = f.get_revision(source_revision.name())
        else:
            audio_revision = f.add_revision(
                name=source_revision.name(), comment=source_revision.comment.get()
            )

        audio_revision.set_sync_status("Available")

        _audio_path = audio_revision.get_path().replace("\\", "/")

        if not os.path.exists(_audio_path):
            os.makedirs(os.path.dirname(_audio_path), exist_ok=True)
        else:
            os.remove(_audio_path)

        return _audio_path

    def get_audio_path(self):
        return self._audio_path.get()

    def run(self, button):
        if button == "Cancel":
            return

        self._audio_path.set(None)

        # Get latest animatic revision
        animatic_rev = self.get_latest_animatic()
        if animatic_rev:
            animatic_path = animatic_rev.get_path()
            if os.path.isfile(animatic_path):
                # Create audio revision according to animatic number
                path_format = None

                default_file = self.get_default_file()
                if default_file is not None:
                    path_format = default_file.path_format.get()

                    audio_path = self._ensure_file(
                        name="animatic",
                        format="wav",
                        path_format=path_format,
                        source_revision=animatic_rev,
                    )

                    subprocess.call(
                        f"ffmpeg -i {animatic_path} -map 0:a {audio_path} -y",
                        shell=True,
                    )
                    self._audio_path.set(audio_path)
                else:
                    self.root().session().log_error(
                        "[Reload Audio] Animatic sound default file do not exist"
                    )
            else:
                self.root().session().log_error(
                    "[Reload Audio] Animatic latest revision path do not exist"
                )
        else:
            self.root().session().log_error(
                "[Reload Audio] Animatic latest revision not found"
            )


class MarkImageSeqTvPaint(MarkImageSequence):
    def _get_audio_path(self):
        scene_name = re.search(r"(.+?(?=_render))", self._folder.name()).group()
        scene_name += "_tvpp"

        print("scene_name", scene_name)

        if not self._files.has_mapped_name(scene_name):
            print("[GET_AUDIO_PATH] Scene not found")
            return None

        print(
            "get_audio_path", self._files[scene_name].export_ae_audio.get_audio_path()
        )

        return self._files[scene_name].export_ae_audio.get_audio_path()

    def mark_sequence(self, revision_name):
        # Compute playblast prefix
        prefix = self._folder.name()
        if "preview" in prefix:
            prefix = prefix.replace("_render_preview", "")
        else:
            prefix = prefix.replace("_render", "")

        source_revision = self._file.get_revision(revision_name)
        revision = self._ensure_file_revision(
            f"{prefix}_movie_preview"
            if "preview" in self._folder.name()
            else f"{prefix}_movie",
            revision_name,
        )

        # Get revision available
        revision.set_sync_status("Available")

        revision.comment.set(source_revision.comment.get())

        # Get the path of the first image in folder
        img_path = self._get_first_image_path(revision_name)

        file_name = prefix + ".tvpp"

        self._extra_argv = {
            "image_path": img_path,
            "video_output": revision.get_path(),
            "file_name": file_name,
            "audio_file": self._get_audio_path(),
        }

        return super(MarkImageSequence, self).run("Render")


class StartTvPaint(GenericRunAction):
    file_path = flow.Param()

    def allow_context(self, context):
        return context

    def runner_name_and_tags(self):
        return "TvPaint", []

    def target_file_extension(self):
        return "tvpp"

    def extra_argv(self):
        return [self.file_path.get()]


class ExecuteRenderPlayblastScript(GenericRunAction):
    output_path = flow.Param()
    start_frame = flow.IntParam()
    end_frame = flow.IntParam()
    render_quality = flow.Param()
    show_ref = flow.Param()

    def allow_context(self, context):
        return False

    def runner_name_and_tags(self):
        return "PythonRunner", []

    def get_version(self, button):
        return None

    def get_run_label(self):
        return "Render TvPaint Playblast"

    def extra_argv(self):
        settings = get_contextual_dict(self._file, "settings")

        current_dir = os.path.split(__file__)[0]
        script_path = os.path.normpath(os.path.join(current_dir, "scripts/render.py"))
        return [
            script_path,
            "--output-path", self.output_path.get(),
            "--start-frame", self.start_frame.get(),
            "--end-frame", self.end_frame.get(),
            "--render-quality", self.render_quality.get(),
            "--show-ref", self.show_ref.get(),
            "--frame_rate", settings.get('frame_rate', 24.0)
        ]


class ExportTVPaintLayersJob(FileJob):

    _file = flow.Parent(2)
    revision = flow.Param()

    def get_label(self):
        return 'EXPORT TVPAINT LAYERS JOB'

    def _do_job(self):
        session = self.root().session()

        session.log_info(f"[{self.get_label()}] Start - {self.get_time()}")

        self.root().project().ensure_runners_loaded()

        # Trigger kitsu login
        kitsu_url = self.root().project().admin.kitsu.server_url.get()
        self.root().project().kitsu_api().set_host(f"{kitsu_url}/api")
        kitsu_status = self.root().project().show_login_page()
        if kitsu_status:
            raise Exception(
                "No connection with Kitsu host. Log in to your account in the GUI session."
            )
            return

        revision = self.revision.get()
        export_comp = self._file.export_layers_to_comp
        export_comp.revision.set(revision)

        result = export_comp.run('Render')
        self.wait_runner([result[1]['runner_id']])

        session.log_info(f"[{self.get_label()}] End - {self.get_time()}")


class SubmitTVPaintExportLayersJob(flow.Action):
    
    _file = flow.Parent()
    _task = flow.Parent(3)
    
    pool = flow.Param('default', SiteJobsPoolNames)
    priority = flow.SessionParam(10).ui(editor='int')
    
    revision = flow.Param().ui(hidden=True)
    
    def get_buttons(self):
        self.message.set('<h2>Submit TVPaint export layers to pool</h2>')
        self.pool.apply_preset()
        return ['Submit', 'Cancel']
    
    def allow_context(self, context):
        return False
    
    def _get_job_label(self):
        settings = get_contextual_dict(self._file, "settings")
        file_label = [
            settings['project_name'],
            settings['sequence'],
            settings['shot'],
            settings['task'],
            settings['file_display_name'],
            self.revision.get()
        ]
        label = f"TVPaint Export Layers - {' '.join(file_label)}"
        return label
    
    def run(self, button):
        if button == 'Cancel':
            return

        # Update pool preset
        self.pool.update_preset()

        job = self._file.jobs.create_job(job_type=ExportTVPaintLayersJob)
        job.revision.set(self.revision.get())
        site_name = self.root().project().get_current_site().name()        

        self._task.change_kitsu_status._is_job.set(True)
        self._task.change_kitsu_status._job_type.set("d'export")
        self._task.change_kitsu_status._status.set("ON_HOLD")
        self._task.change_kitsu_status._pool_name.set(self.pool.get())
        self._task.change_kitsu_status.run("run")

        job.submit(
            pool=site_name + '_' + self.pool.get(),
            priority=self.priority.get(),
            label=self._get_job_label(),
            creator=self.root().project().get_user_name(),
            owner=self.root().project().get_user_name(),
            paused=False,
            show_console=False,
        )


class ExportTVPaintLayers(flow.Action):
    ICON = ("icons.libreflow", "tvpaint")

    _file = flow.Parent()
    _task = flow.Parent(3)
    _shot = flow.Parent(5)
    _sequence = flow.Parent(7)

    revision = flow.Param(None, FileRevisionNameChoiceValue)
    all_layers = flow.SessionParam(True, PresetSessionValue).ui(editor="bool")
    send_to_comp = flow.SessionParam(True, PresetSessionValue).watched().ui(
        editor="bool",
        tooltip="Store layers in compositing task and generate JSON file needed for After Effects",
    )

    with flow.group("Advanced"):
        all_frames = flow.SessionParam(False, PresetSessionValue).ui(editor="bool")

    def allow_context(self, context):
        return (
            context
            and self._file.format.get() == "tvpp"
            and not self._file.is_empty(on_current_site=True, published_only=True)
        )

    def needs_dialog(self):
        return True

    def get_buttons(self):
        self.revision.revert_to_default()
        self.check_default_values()

        buttons = ["Export", "Cancel"]
        # if (
        #     self.root().project().get_current_site().site_type.get() == "Studio"
        #     and self.root().project().get_current_site().pool_names.get()
        # ):
        #     buttons.insert(1, "Submit job")
        return buttons

    def check_default_values(self):
        self.all_layers.apply_preset()
        self.send_to_comp.apply_preset()
        self.all_frames.apply_preset()
        self._file.execute_export_layers_script.filter_layers.set(None)

    def update_presets(self):
        self.all_layers.update_preset()
        self.send_to_comp.update_preset()
        self.all_frames.update_preset()

    def child_value_changed(self, child_value):
        if child_value is self.send_to_comp and self.send_to_comp.get() is True:
            self.all_frames.set(False)

    def ensure_layers_folder(self):
        if self.send_to_comp.get():
            mng = self.root().project().get_task_manager()
            # Find any file with 'layers' in its name that is used for compositing task
            self.dft_file = mng.get_default_file(file_regex="layers", task_regex="comp")

            if self.dft_file is None:
                self.root().session().log_error(
                    "[EXPORT TVPAINT LAYERS] No default file found with 'layers' in naming and on a compositing task."
                )
                return None

            task = self._shot.tasks[self.dft_file.task.name()]
            folder_name = self.dft_file.name()
        else:
            task = self._task
            folder_name = f"{self._file.complete_name.get()}_layers"

        if not task.files.has_folder(folder_name):
            task.create_folder_action.folder_name.set(folder_name)
            task.create_folder_action.category.set(
                self.dft_file.file_type.get() if self.send_to_comp.get() else "Outputs"
            )
            task.create_folder_action.tracked.set(True)
            task.create_folder_action.run(None)

        return task.files[folder_name]

    def ensure_layers_folder_revision(self, source_revision):
        folder = self.ensure_layers_folder()
        if folder is None:
            return None

        revision_name = self.revision.get()

        if not folder.has_revision(revision_name):
            revision = folder.add_revision(revision_name)
            folder.set_current_user_on_revision(revision_name)
        else:
            revision = folder.get_revision(revision_name)

        revision.comment.set(
            f"from {self._file.display_name.get()}"
            if self.send_to_comp.get()
            else source_revision.comment.get()
        )
        revision.set_sync_status("Available")

        folder.ensure_last_revision_oid()

        if self.send_to_comp.get():
            self._shot.tasks[self.dft_file.task.name()].files.touch()
        else:
            self._shot.tasks[self._task.name()].files.touch()

        return revision

    def start_tvpaint(self, path):
        start_action = self._task.start_tvpaint
        start_action.file_path.set(path)
        ret = start_action.run(None)
        self.tvpaint_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )

    def execute_render_script(self, path):
        exec_script = self._file.execute_export_layers_script
        exec_script.output_path.set(path)
        exec_script.all_frames.set(self.all_frames.get())
        exec_script.delete_json.set(not self.send_to_comp.get())
        ret = exec_script.run(None)
        self.script_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )
        return ret

    def run(self, button):
        if button == "Cancel":
            return
        elif button == "Submit job":
            submit_action = self._file.submit_tvpaint_export_layers_job
            submit_action.revision.set(self.revision.get())
            
            return self.get_result(
                next_action=submit_action.oid()
            )
        elif button != "Export selection":
            self.update_presets()

            if self.all_layers.get() is False:
                page2_action = self._file.export_tvpaint_layers_page2

                return self.get_result(
                    next_action=page2_action.oid()
                )

        # Open TVPaint project
        source_revision = self._file.get_revision(self.revision.get())
        self.start_tvpaint(source_revision.get_path())

        # Configure output
        layers_revision = self.ensure_layers_folder_revision(source_revision)
        if layers_revision is None:
            return self.get_result(close=False)

        if os.path.exists(layers_revision.get_path()):
            remove_folder_content(layers_revision.get_path())
        else:
            os.makedirs(layers_revision.get_path())

        json_name = f"{self._sequence.name()}_{self._shot.name()}_layers_data.json"
        json_path = os.path.join(layers_revision.get_path(), json_name)

        self.execute_render_script(json_path)


class ExportTVPaintLayersPage2(flow.Action):
    ICON = ("icons.libreflow", "tvpaint")

    _file = flow.Parent()
    _task = flow.Parent(3)

    def allow_context(self, context):
        return context

    def needs_dialog(self):
        return True

    def get_buttons(self):
        msg = '<font color=#EFDD5B><h3>TVPaint will be started to fetch list of layer names.</h3></font>'
        msg += '\nYour Libreflow will freeze during the process.'
        self.message.set(msg)

        return ["Fetch", "Cancel"]

    def start_tvpaint(self, path):
        start_action = self._task.start_tvpaint
        start_action.file_path.set(path)
        ret = start_action.run(None)
        self.tvpaint_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )

    def execute_fetch_script(self):
        exec_script = self._file.execute_fetch_layers_script
        ret = exec_script.run(None)
        self.script_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )
        return ret

    def run(self, button):
        if button == "Cancel":
            return

        self.message.set('<font color=#EFDD5B><h3>TVPaint process is running.</h3></font>')

        # Open TVPaint project
        base_action = self._file.export_tvpaint_layers

        source_rev = self._file.get_revision(base_action.revision.get())
        self.start_tvpaint(source_rev.get_path())
        self.execute_fetch_script()

        # Force Qt to refresh GUI to display message
        QtWidgets.QApplication.processEvents()
        QtWidgets.QApplication.processEvents()

        # Wait for TVPaint process to end
        while psutil.pid_exists(int(self.script_runner['pid'])):
            time.sleep(1.0)

        # Go to layers selection
        select_action = self._file.select_tvpaint_layers
        select_action.layers.force_touch()
        return self.get_result(next_action=select_action.oid())


class ExecuteFetchLayersScript(GenericRunAction):

    output_path = flow.Param()

    def allow_context(self, context):
        return False

    def runner_name_and_tags(self):
        return "PythonRunner", []

    def get_version(self, button):
        return None

    def get_run_label(self):
        return "Fetch TvPaint Layers"

    def extra_argv(self):
        self.output_path.set(tempfile.mkdtemp())
        return [resources.get("scripts", "fetch_layers.py"), "--output-path", self.output_path.get()]


class SelectTVPaintLayer(flow.Action):

    _item = flow.Parent()
    _map  = flow.Parent(2)

    def needs_dialog(self):
        return False
    
    def allow_context(self, context):
        return False
    
    def run(self, button):
        self._item.selected.set(
            not self._item.selected.get()
        )
        self._map.touch()


class TVPaintLayer(flow.Object):
    layer_name = flow.Computed()
    start_frame = flow.Computed()
    end_frame = flow.Computed()
    selected = flow.SessionParam(False)

    select_action = flow.Child(SelectTVPaintLayer)

    _map = flow.Parent()

    def compute_child_value(self, child_value):
        if child_value is self.layer_name:
            self.layer_name.set(self._map.get_entity_data(self.name(), "name"))
        if child_value is self.start_frame:
            self.start_frame.set(self._map.get_entity_data(self.name(), "start"))
        if child_value is self.end_frame:
            self.end_frame.set(self._map.get_entity_data(self.name(), "end"))


class ClearTVPaintLayersSelection(flow.Action):
    
    ICON = ('icons.libreflow', 'clean')
    _map = flow.Parent()

    def needs_dialog(self):
        return False
    
    def run(self, button):
        for item in self._map.mapped_items():
            item.selected.set(False)

        self._map.touch()


class TVPaintLayers(flow.DynamicMap):
    ICON = ("icons.libreflow", "dependencies")

    _action = flow.Parent()
    _file = flow.Parent(2)

    clear_selection = flow.Child(ClearTVPaintLayersSelection)

    @classmethod
    def mapped_type(cls):
        return TVPaintLayer

    def __init__(self, parent, name):
        super(TVPaintLayers, self).__init__(parent, name)
        self._layers_data = None

    def columns(self):
        return ["Name"]

    def mapped_names(self, page_num=0, page_size=None):
        if self._layers_data is None:
            self._layers_data = {}

            temp_path = self._file.execute_fetch_layers_script.output_path.get()
            json_path = os.path.join(temp_path, "layers.json")
            with open(json_path, "r") as f:
                data = json.loads(f.read())

                for index, layer in enumerate(data["layers"]):
                    mapped_name = f"layer_{index}"
                    self._layers_data[mapped_name] = layer

            shutil.rmtree(temp_path)

        return self._layers_data.keys()

    def get_entity_data(self, mapped_name, key):
        self.mapped_names()
        return self._layers_data[mapped_name][key]

    def force_touch(self):
        self._layers_data = None
        super(TVPaintLayers, self).touch()

    def _fill_row_cells(self, row, item):
        row["Name"] = item.layer_name.get()

    def _fill_row_style(self, style, item, row):
        style['Name_icon'] = (
            'icons.gui',
            'check' if item.selected.get() else 'check-box-empty'
        )
        style['Name_activate_oid'] = item.select_action.oid()


class SelectTVPaintLayers(flow.Action):
    ICON = ("icons.libreflow", "tvpaint")

    _file = flow.Parent()
    _task = flow.Parent(3)
    _shot = flow.Parent(5)
    _sequence = flow.Parent(7)

    layers = flow.Child(TVPaintLayers).ui(expanded=True)

    def allow_context(self, context):
        return context

    def needs_dialog(self):
        return True

    def get_buttons(self):
        self.message.set('<h2>Select TVPaint layers to export</h2>')

        return ["Export", "Cancel"]

    def run(self, button):
        if button == "Cancel":
            return

        selection = [
            layer.layer_name.get()
            for layer in self.layers.mapped_items()
            if layer.selected.get()
        ]
        self._file.execute_export_layers_script.filter_layers.set(selection)
        
        self._file.export_tvpaint_layers.run("Export selection")


class ExecuteExportLayersScript(GenericRunAction):
    output_path = flow.Param()
    filter_layers = flow.Param(None)
    all_frames = flow.Param(False)
    delete_json = flow.Param(False)

    def allow_context(self, context):
        return False

    def runner_name_and_tags(self):
        return "PythonRunner", []

    def get_version(self, button):
        return None

    def get_run_label(self):
        return "Export TvPaint Layers"

    def extra_argv(self):
        args = [
            resources.get("scripts", "export_layers.py"),
            "--output-path",
            self.output_path.get(),
        ]
        if self.filter_layers.get():
            for layer in self.filter_layers.get():
                args += ["--filter-layers", layer]
        if self.all_frames.get():
            args += ["--all-frames"]
        if self.delete_json.get():
            args += ["--delete-json"]

        return args


def start_tvpaint(parent):
    if isinstance(parent, Task):
        r = flow.Child(StartTvPaint)
        r.name = "start_tvpaint"
        r.index = None
        r.ui(hidden=True)
        return r


def export_audio(parent):
    if isinstance(parent, TrackedFile) and (parent.name().endswith("_tvpp")):
        r = flow.Child(ExportAudio)
        r.name = "export_ae_audio"
        r.index = None
        r.ui(hidden=True)
        return r


def render_tvpaint_playblast(parent):
    if isinstance(parent, TrackedFile) and (parent.name().endswith("_tvpp")):
        r = flow.Child(RenderTvPaintPlayblast)
        r.name = "render_tvpaint_playblast"
        r.index = None
        return r


def execute_render_playblast_script(parent):
    if isinstance(parent, TrackedFile) and (parent.name().endswith("_tvpp")):
        r = flow.Child(ExecuteRenderPlayblastScript)
        r.name = "execute_render_playblast_script"
        r.index = None
        r.ui(hidden=True)
        return r


def mark_sequence_tvpaint(parent):
    if isinstance(parent, TrackedFolder) and (parent._task.name() != "compositing"):
        r = flow.Child(MarkImageSeqTvPaint)
        r.name = "mark_image_sequence"
        r.index = None
        return r


def export_layers(parent):
    if isinstance(parent, TrackedFile) and parent.format.get() == "tvpp":
        export = flow.Child(ExportTVPaintLayers)
        export.name = "export_tvpaint_layers"
        export.index = None

        export_page2 = flow.Child(ExportTVPaintLayersPage2)
        export_page2.name = "export_tvpaint_layers_page2"
        export_page2.index = None
        export_page2.ui(hidden=True)

        execute_export = flow.Child(ExecuteExportLayersScript)
        execute_export.name = "execute_export_layers_script"
        execute_export.index = None
        execute_export.ui(hidden=True)

        execute_fetch = flow.Child(ExecuteFetchLayersScript)
        execute_fetch.name = "execute_fetch_layers_script"
        execute_fetch.index = None
        execute_fetch.ui(hidden=True)

        select = flow.Child(SelectTVPaintLayers)
        select.name = "select_tvpaint_layers"
        select.index = None
        select.ui(hidden=True, dialog_size=(510, 550))

        submit = flow.Child(SubmitTVPaintExportLayersJob)
        submit.name = "submit_tvpaint_export_layers_job"
        submit.ui(hidden=True)

        return [export, export_page2, execute_export, execute_fetch, select, submit]


def install_extensions(session):
    return {
        "tvpaint_playblast": [
            start_tvpaint,
            render_tvpaint_playblast,
            execute_render_playblast_script,
            export_audio,
            mark_sequence_tvpaint,
            export_layers,
        ]
    }
