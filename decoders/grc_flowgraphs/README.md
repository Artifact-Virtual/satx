# GRC Flowgraphs

This directory contains GNU Radio Companion (.grc) flowgraphs for satellite signal decoding.

## Available Flowgraphs

### 1. NOAA APT Decoder (noaa_apt.grc)
- **Frequency:** 137.1, 137.5, 137.9 MHz
- **Modulation:** AM (APT)
- **Output:** Weather images
- **Usage:** Real-time or recorded I/Q

### 2. CubeSat AFSK Decoder (cubesat_afsk.grc)
- **Frequency:** 435-438 MHz
- **Modulation:** AFSK (1200 baud)
- **Protocol:** AX.25
- **Output:** Telemetry packets

### 3. Generic FSK Decoder (generic_fsk.grc)
- **Configurable** center frequency and deviation
- **Supports:** 1200, 2400, 4800, 9600 baud
- **Output:** Raw bits or decoded frames

### 4. Doppler Correction (doppler_correct.grc)
- Real-time frequency correction
- Integrates with GPredict
- Works with rtl_tcp

## Usage

### Open in GNU Radio Companion

```bash
gnuradio-companion flowgraph_name.grc
```

### Run from Command Line

```bash
python3 flowgraph_name.py --input-file recording.iq --output-file decoded.txt
```

### Generate Python Script

In GRC:
1. Open flowgraph
2. Click "Generate" (F5)
3. Run generated Python script

## Creating Custom Flowgraphs

### Basic Structure

1. **Source:** File Source or rtl_tcp Source
2. **Frequency Translation:** Xlating FIR Filter
3. **Resampling:** Rational Resampler
4. **Demodulation:** Quad Demod / GMSK / BPSK
5. **Clock Recovery:** Symbol Sync or M&M Clock Recovery
6. **Decoding:** HDLC Deframer / Custom Protocol
7. **Sink:** File Sink or TCP Sink

### Example: Simple FM Demod

```
File Source → Xlating FIR → Quad Demod → Audio Sink
```

## Integration with gr-satellites

Many satellites are already supported by gr-satellites:

```bash
# List available satellites
gr_satellites --list

# Decode recording
gr_satellites recording.iq --norad 25544 --samp_rate 2.4e6 --verbose
```

## Resources

- [GNU Radio Tutorials](https://wiki.gnuradio.org/index.php/Tutorials)
- [gr-satellites Documentation](https://gr-satellites.readthedocs.io/)
- [GRC Examples](https://github.com/gnuradio/gnuradio/tree/master/gr-digital/examples)

## Contributing

Add your own flowgraphs here and document them in this README!
