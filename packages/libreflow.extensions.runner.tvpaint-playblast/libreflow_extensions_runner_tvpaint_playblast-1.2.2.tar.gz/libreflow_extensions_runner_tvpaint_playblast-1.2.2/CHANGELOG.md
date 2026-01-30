# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)[^1].

<!---
Types of changes

- Added for new features.
- Changed for changes in existing functionality.
- Deprecated for soon-to-be removed features.
- Removed for now removed features.
- Fixed for any bug fixes.
- Security in case of vulnerabilities.

-->

## [Unreleased]

## [1.2.2] - 2026-01-21

### Added

* Export TVPaint Layers action handles the export of all frames, not just instances.
  * For After Effects usage, only instances should be used.

## [1.2.1] - 2026-01-15

### Fixed

* Create folder action is now parented in the `ManagedTask` class.

## [1.2.0.1] - 2026-01-14

### Fixed

* `pytvpaint` plugin check does not handle session environnement path override.

## [1.2.0] - 2026-01-14

### Changed

* Export TVPaint Layers action:
  * Make it more generic so that it can be used for any project, and not just for compositing task.
  * It is now possible to export specific layers.
    * TVPaint project is opened temporarily to retrieve the list of layer names.

### Removed

* Due to major changes to Export TVPaint Layers action, jobs support and Kitsu task status updates are temporarily disabled.

### Fixed

* Change the TVPaint camera FPS number to use the Kabaret contextual dict for playblast rendering.

## [1.1.6] - 2025-11-06

### Fixed

* Camera FPS number is now set according to the project parameter for playblast rendering.

## [1.1.5] - 2025-09-05

### Added

* Render action: An exception is now raised if the `pytvpaint` plugin is not found in the installation folder

### Changed

* Mark Image Sequence is no longer overridden on compositing task.
    * Create a conflict with an another extension for a specific project. Maybe need to revisit this scenario later.

## [1.1.4] - 2025-08-14

### Added

* Change the synchronisation status to Available for revision of the playblast file.

## [1.1.3.2] - 2025-08-07

### Fixed

* Export layers to comp job: wait runner in session worker doesn't work and force sync status availability if folder revision already exists.

## [1.1.3.1] - 2025-08-07

### Fixed

* Export layers to comp job: kitsu connection is now established at the start of the session.

## [1.1.3] - 2025-08-06

### Changed

* Export layers to comp
    * Job label has been simplified.
        * Only the necessary data is shown, no longer the full entity OID.
    * Kitsu task status is now updated with the export status and if it's processed locally or from a job pool.

### Fixed

* Export AE Audio action should be hidden from the GUI interface.
* Export to Comp action class is now only loaded for certain projects.

## [1.1.2] - 2025-06-12

### Added

* A job type for the export layers to comp action.
    * This action can now be used with `kabaret.jobs` (for batch export or like a render farm on multiple computers).

## [1.1.1] - 2025-05-09

### Added

* Export to Comp action that creates a folder with layers exported as image sequences in the compositing task (limited to certain projects)

## [1.1.0] - 2025-04-03

### Added

* Render will execute even when the audio file is missing
* Improved default file name matching to avoid confusion between final and preview playblast versions
* In and Out marks on the TvPaint timeline are now handled by the render action

### Fixed

* Frame ranged in now forced on the pytvpaint render action to avoid frame range issues
* Folder name is now parsed correctly to the MarkSequence action
* Marking will now initiate only when both the PythonRunner and TvPaint processes are stopped, meaning
that the marking will start only if the TvPaint render worked properly

### Changed

* "Preview" render option is temporarily disabled due to a pytvpaint error that prevent a keyframed camera to be resized properly when the project resolution is changed 

## [1.0.7] - 2025-02-21

### Added

* Export Audio will now create a .wav default file in animatic


## [1.0.6] - 2024-12-12

### Changed

* Show reference is now checked by default in exposition task

## [1.0.5] - 2024-12-06

### Fixed

* imported re

## [1.0.4] - 2024-12-06

### Fixed

* scripts folder is now properly packed in releases.

## [1.0.3] - 2024-12-05

### Fixed

* show_reference fixed

## [1.0.2] - 2024-12-04

### Added

* the video output will now have the audio from the animatic
* an option to show the reference in the video output

## [1.0.1] - 2024-10-27

### Changed

* The playblast rendering action is enabled on TVPaint files only.

## [1.0.0] - 2024-10-25

### Added

* Extension for rendering playblast from a TVPaint file.
