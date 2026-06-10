# V2 Artifact Runs

This folder is split by generation run so printable outputs and editable Boolean/decomposition outputs are not mixed.

| Run | Folder | Use |
| --- | --- | --- |
| Printable assembly | `2026-06-09_v2_printable_assembly/` | Finished printable STLs, renders, side/top sketches, and final threaded/envelope STEP files. |
| Editable decomposition | `2026-06-10_v2_editable_decomposition/` | Latest run. Same-coordinate and exploded STEP files for tube base, male threads, holder parts, and female thread cutters. |

## Single File To Copy

For the latest editable run, copy:

`2026-06-10_v2_editable_decomposition/threaded_reflector_full_decomposition.step`

This single STEP keeps the full design split into named editable objects:

- tube base;
- left and right male thread solids;
- holder cube shell;
- holder socket cylinder;
- holder bottom reinforcement;
- holder bore cutter;
- holder female thread cutter.

If you only need the finished assembled geometry, copy:

`2026-06-09_v2_printable_assembly/threaded_reflector_assembly_threaded.step`
