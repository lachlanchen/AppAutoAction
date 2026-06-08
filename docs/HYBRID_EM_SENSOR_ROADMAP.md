# Hybrid Electron-Microscopy Sensor Roadmap

Date: 2026-06-08

## Goal

Build toward an open detector and acquisition stack for a NanoMi-style electron microscope that combines:

- a frame channel for spatial detail and operator context;
- an event channel for sparse, fast changes;
- a single-pixel / bucket-detector channel for high dynamic range and flexible detector physics;
- optional spectral channels for material contrast or optical/scintillator spectroscopy.

The near-term path should be board-level and modular. A true monolithic "frame + event + spectrum + single-pixel" image sensor is a longer-term ASIC/foundry project.

## Local Source Repositories

- `/home/lachlan/ProjectsLFS/NanoMi`: open electron microscope platform, including CAD, electron optics, high-voltage scan electronics, STEM scanner, detector context, and safety constraints.
- `/home/lachlan/ProjectsLFS/CustomSensor`: digiOBSCURA 32x32 phototransistor camera, firmware, KiCad boards, and staged notes for comparator-assisted event mode and full event-sensor redesign.

Use NanoMi as the microscope and detector-interface reference. Use CustomSensor as the first practical custom array, muxing, firmware, and event-readout reference.

## Research Anchors

- NanoMi is a modular open electron microscope platform targeting SEM/TEM/STEM/ED, up to 50 keV, with about 10 nm intended image resolution and UHV-compatible modular optics.
- Event cameras report asynchronous brightness-change events rather than only full frames. Reported advantages include low latency, high temporal resolution, high dynamic range, and lower data rate when scenes are sparse.
- Prophesee's Metavision sensors are a commercial event-sensor reference: each pixel triggers independently, with advertised >120 dB dynamic range and >10k fps time-resolution equivalent.
- DAVIS is the key precedent for hybrid event + frame imaging: it combines DVS events and APS grayscale frames in the same pixel array.
- Single-pixel imaging is relevant because one detector can be paired with structured illumination/scanning/compressive reconstruction, and it can be easier to adapt across spectral bands or unusual detector physics.
- Direct electron detectors are the high-performance EM reference point. They avoid scintillator conversion and can offer far higher sensitivity than scintillator + CCD/CMOS paths, but they raise radiation-hardness, vacuum, packaging, and data-throughput difficulty.

## Proposed Architecture

Start as a modular "Weiqi board" with explicit channels instead of trying to make a custom CMOS sensor first:

```text
NanoMi scan timing / beam state
  -> detector front-end board
      -> frame/scintillator camera input
      -> event/comparator path
      -> single-pixel TIA / bucket detector path
      -> spectral detector or spectrometer input
  -> FPGA or fast MCU timestamp hub
  -> USB/Ethernet data stream
  -> host fusion software
```

Data model:

- Frames: `(frame_id, exposure, timestamp, image)`
- Events: `(timestamp, x, y, polarity, magnitude?)`
- Single-pixel samples: `(timestamp, scan_x, scan_y, detector_value, gain, integration_time)`
- Spectral samples: `(timestamp, scan_x, scan_y, wavelength/bin, intensity)`

## Staged Build Plan

1. **Detector interface audit**
   - Map NanoMi detector locations, scan timing, analog outputs, camera path, and voltage domains.
   - Identify safe external detector ports first; avoid modifying high-voltage or vacuum-critical parts.

2. **Single-pixel detector board**
   - Build a low-noise TIA board for photodiode/PMT/SiPM/scintillator pickup.
   - Synchronize each sample with NanoMi scan coordinates.
   - Validate dark noise, dynamic range, bandwidth, and saturation behavior.

3. **Comparator event mezzanine**
   - Reuse CustomSensor's comparator-event roadmap.
   - Add programmable threshold DACs, hysteresis, event polarity, and timestamp capture.
   - Prototype first on a small 4x4 or 8x8 tile.

4. **Frame + event fusion**
   - Keep a conventional frame/scintillator camera for context.
   - Add event overlay and single-pixel reconstruction in the host software.
   - Store all channels with shared timestamps and calibration metadata.

5. **Spectral branch**
   - Start outside vacuum using scintillator/light-output spectroscopy.
   - Later evaluate electron-energy or optical spectral channels if the microscope geometry supports it.

6. **Custom array respin**
   - Evolve CustomSensor from 32x32 muxed frames to tiled comparators and parallel readout.
   - Candidate blocks: per-tile TIA, comparator, local sample/hold, FPGA timestamping, USB/Ethernet output.

7. **ASIC / direct detector research**
   - Only after board-level proof: consider custom CMOS/event pixel design or partner with a detector foundry.
   - Direct electron exposure requires radiation-hard design and serious packaging/vacuum review.

## Immediate Engineering Requirements

- Keep all high-voltage and vacuum interfaces isolated from early prototypes.
- Add calibration datasets: dark frames, flat fields, comparator thresholds, TIA gain, scan timing, detector geometry.
- Use KiCad project-local libraries and deterministic scripts for every board.
- Export DRC/ERC, Gerbers, drill, STEP, top SVG, close render, and full-board render for review.
- Keep raw microscope captures and large external archives out of git.

## Sources

- NanoMi NRC overview: https://nrc.canada.ca/en/research-development/nanomi-worlds-first-open-source-transmission-electron-microscope
- NanoMi publication abstract: https://nrc-publications.canada.ca/eng/view/object/?id=02fb266b-721d-4a35-b825-0af8044db446
- Event-Based Vision survey: https://research.ibm.com/publications/event-based-vision-a-survey
- Prophesee Metavision sensors: https://www.prophesee.ai/event-based-sensors/
- DAVIS event + frame reference: https://rpg.ifi.uzh.ch/docs/EBCCSP16_Tedaldi.pdf
- Single-pixel imaging review: https://www.nature.com/articles/s41566-018-0300-7
- Direct electron detector glossary: https://www.jeol.com/words/emterms/20160713.103416.php
- 4D Camera direct electron detector: https://arxiv.org/abs/2305.11961
- Cascaded compressed-sensing single-pixel camera: https://link.springer.com/article/10.1186/s43074-024-00152-5
