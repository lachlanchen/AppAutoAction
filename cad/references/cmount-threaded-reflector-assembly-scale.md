# C-Mount Threaded Reflector Assembly Scale Reference

Date: 2026-06-09

## Purpose

New two-part design for connecting the old 4f system female C-mount side to a top-open reflector holder. This does not replace the earlier one-piece adapter.

## Old Design Details Used

The old OpenHI/Nature STEP files are millimetre STEP exports. Exact thread labels found:

- `OpenHI_STEP/A.step`: `Thread top`
- `OpenHI_STEP/B.step`: `Thread camera 24.4`, `Thread lens 29.6*`
- `OpenHI_STEP/C.step`: `Thread camera 24.4`, `Thread lens 29.6`
- `OpenHI_STEP/Collimator tube.step`: `Outer thread`, `Thread left 24.8`
- `OpenHI_STEP/Collimator cap.step`: `Cap thread 24.8`
- `Nature_STEP/BS lateral.step.step`: repeated `Thread camera 24.4`, `Thread lens 29.6`, `Thread top`, `Thread BS`

Imported A/B/C branch bounding boxes:

| Branch | Bounding box |
| --- | --- |
| `A.step` | `40 x 40 x 50 mm` |
| `B.step` | `40 x 40 x 54.4 mm` |
| `C.step` | `54 x 40 x 40 mm` |

## New Tube

| Feature | Value |
| --- | ---: |
| Total length | `50 mm` |
| Left male thread length | `20 mm` |
| Right male thread length | `20 mm` |
| Center unthreaded body | `10 mm` |
| Male printed thread OD | `24.4 mm` |
| Body OD | `28 mm` |
| Bore | `20 mm` |
| Center body wall | `4 mm` |
| Thread pitch | `0.79375 mm` |
| Thread hand | right-hand when viewed from each engaging end |
| Center body bottom plane | `Z = 0`, same as holder bottom |

## New Reflector Holder

| Feature | Value |
| --- | ---: |
| Reflector pocket | `20 x 20 x 20 mm` |
| Wall thickness | `4 mm` |
| Top | open |
| Left side | open through threaded socket |
| Female socket length | `24 mm` |
| Female thread cutter OD | `24.8 mm` |
| Female minor bore | `23.8 mm` |
| Socket outer OD | `34 mm`, clipped flat at bottom |
| Optical axis height | `14 mm` |
| Holder STL bounds | `48 x 34 x 31 mm` |
| Assembly STL bounds | `78 x 34 x 31 mm` |

## Generated Support Files

Primary printable files:

- `cad/designs/cmount_threaded_reflector_assembly/artifacts/male_male_cmount_tube.stl`
- `cad/designs/cmount_threaded_reflector_assembly/artifacts/top_open_reflector_holder.stl`

Support files:

- `artifacts/male_male_cmount_tube_envelope.step`
- `artifacts/top_open_reflector_holder_envelope.step`
- `artifacts/threaded_reflector_assembly_envelope.step`
- `artifacts/male_male_cmount_tube_threaded.step`
- `artifacts/top_open_reflector_holder_threaded.step`
- `artifacts/threaded_reflector_assembly_threaded.step`
- `artifacts/threaded_reflector_exploded_thread_detail.png`
- `artifacts/assembly_side_section.svg`
- `artifacts/assembly_top_view.svg`
- `artifacts/threaded_reflector_assembly_top_sketch.dxf`

Use STL for printing because it is generated directly from the printable OpenSCAD thread geometry. Use `threaded_reflector_assembly_threaded.step` when a single STEP file with both threaded parts is needed. The envelope STEP files are intentionally smooth and lightweight.
