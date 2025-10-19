# Building a DIY Satellite Antenna

Complete guides for building cost-effective satellite antennas.

---

## 1. VHF Turnstile Antenna (137 MHz - NOAA Weather Satellites)

**Cost:** ~$15-25  
**Difficulty:** Easy  
**Performance:** Excellent for NOAA APT reception

### Materials Needed

- 4× 50cm lengths of 3mm solid copper wire
- 1× SO-239 (UHF) chassis mount connector
- 1× 50cm length of 20mm PVC pipe
- Coax cable (RG-58 or better)
- Solder and soldering iron
- Electrical tape or heat shrink
- Mounting hardware

### Construction Steps

1. **Cut Elements:**
   - Each dipole element: 53.4 cm (quarter wavelength at 137 MHz)
   - Cut 4 pieces of copper wire

2. **Prepare PVC Mast:**
   - Drill hole for SO-239 connector at center
   - Drill 4 holes at 90° intervals for dipole elements

3. **Assemble Dipoles:**
   - Create two dipoles perpendicular to each other
   - Phase one dipole 90° ahead using coax delay line

4. **Connect Feed:**
   - Solder dipoles to SO-239 center and shield
   - Waterproof all connections

### Detailed Guide
- [RTL-SDR Blog: Turnstile Guide](https://www.rtl-sdr.com/simple-noaa-weather-satellite-antenna-137-mhz-v-dipole/)

---

## 2. QFH Antenna (137 MHz - NOAA/METEOR)

**Cost:** ~$25-40  
**Difficulty:** Moderate  
**Performance:** Superior circular polarization, best for LEO

### Materials Needed

- 6 meters of 12 AWG copper wire
- 2× 60cm lengths of 20mm PVC pipe
- 1× 40cm length of 25mm PVC pipe (boom)
- 1× SO-239 connector
- 1× 1:1 balun or ferrite choke
- PVC T-joints and caps
- Coax cable
- Cable ties

### Construction Steps

1. **Calculate Dimensions for 137.5 MHz:**
   - Small loop circumference: 216.8 cm
   - Large loop circumference: 217.6 cm
   - Height: 54.4 cm

2. **Build Support Structure:**
   - Use PVC pipes to create vertical supports
   - Space them at calculated loop diameter

3. **Form Loops:**
   - Bend copper wire into helical loops
   - Small loop: 2 turns
   - Large loop: 2 turns, slightly larger diameter

4. **Phase and Connect:**
   - Connect loops with 90° phase difference
   - Use balun to match impedance

### Detailed Guides
- [AMSAT: QFH Construction](https://www.amsat.org/qfh-antenna-construction/)
- [N2YO: QFH Calculator](https://www.n2yo.com/api/)

---

## 3. UHF Yagi Antenna (435-438 MHz - CubeSats)

**Cost:** ~$30-50  
**Difficulty:** Moderate  
**Performance:** High gain, directional (requires tracking)

### Materials Needed

- 1× 1m length of 20mm PVC pipe (boom)
- 5-7× 6mm aluminum rods (elements)
- 1× SO-239 connector
- Coax cable
- U-bolts for mounting
- Hose clamps

### Construction Steps

1. **Calculate Element Lengths (435 MHz):**
   - Reflector: 35.8 cm
   - Driven element: 32.6 cm (dipole)
   - Director 1: 31.2 cm
   - Director 2: 30.5 cm
   - Director 3: 30.0 cm

2. **Element Spacing:**
   - Reflector to driven: 16.5 cm
   - Driven to director 1: 15.0 cm
   - Directors spaced: 12-15 cm apart

3. **Assembly:**
   - Drill holes in PVC boom for elements
   - Insert and secure elements
   - Connect driven element to SO-239
   - Isolate driven element from boom

4. **Tuning:**
   - Use antenna analyzer or SWR meter
   - Adjust element lengths for minimum SWR

### Detailed Guide
- [WA5VJB: Cheap Yagi Antennas](http://www.wa5vjb.com/yagi-pdf/cheapyagi.pdf)

---

## 4. Helical Antenna (2.4 GHz - S-band Satellites)

**Cost:** ~$40-60  
**Difficulty:** Advanced  
**Performance:** Circular polarization, high gain

### Materials Needed

- 3 meters of 2mm copper wire
- 1× 40cm length of 40mm PVC pipe
- 1× 15cm diameter ground plane (aluminum sheet)
- N-type connector
- Coax cable

### Construction Steps

1. **Calculate Helix Dimensions (2.4 GHz):**
   - Circumference: 12.5 cm (1λ)
   - Pitch: 3.125 cm (0.25λ)
   - Number of turns: 10-12
   - Diameter: 4 cm

2. **Wind Helix:**
   - Mark PVC pipe with spiral guide
   - Wrap copper wire following marks
   - Secure with epoxy or hot glue

3. **Ground Plane:**
   - Cut circular reflector
   - Mount at base of helix
   - Connect N-connector

4. **Feed Point:**
   - Connect helix start to center conductor
   - Ground plane to shield

### Detailed Guide
- [VK5DJ: Helical Antenna Design](http://www.vk5dj.com/helix.html)

---

## 5. Eggbeater Antenna (145/435 MHz - Dual-band LEO)

**Cost:** ~$35-50  
**Difficulty:** Moderate-Advanced  
**Performance:** Dual-band, circular polarization, omnidirectional

### Materials Needed

- Copper wire: 12 AWG
- PVC pipe: 20mm for structure
- 2× SO-239 connectors (VHF/UHF)
- Coax cable
- 2× Baluns
- PVC fittings

### Construction Steps

1. **VHF Elements (145 MHz):**
   - Loop circumference: 207 cm
   - Height: 51.8 cm

2. **UHF Elements (435 MHz):**
   - Loop circumference: 69 cm
   - Height: 17.3 cm

3. **Nested Construction:**
   - Mount UHF loops inside VHF loops
   - Use separate feed points
   - Maintain 90° phase offset for each band

4. **Tuning:**
   - Test each band independently
   - Adjust loop sizes for resonance

### Detailed Guide
- [Eggbeater Design](https://www.amsat.org/articles/...)

---

## Antenna Testing and Tuning

### Equipment Needed

- NanoVNA or antenna analyzer (~$50)
- SWR meter
- RTL-SDR for signal strength

### Testing Procedure

1. **SWR Measurement:**
   - Connect antenna to analyzer
   - Sweep frequency band
   - Target SWR < 2:1 at center frequency

2. **Pattern Testing:**
   - Use known satellite pass
   - Compare signal strength vs. time
   - Verify omnidirectional or directional pattern

3. **Tuning:**
   - Adjust element lengths for minimum SWR
   - Trim in small increments (1-2mm)
   - Retest after each adjustment

---

## Antenna Mounting

### Weatherproofing

- Seal all connections with self-amalgamating tape
- Apply liquid electrical tape or silicone
- Use UV-resistant cable ties
- Protect connectors with boots

### Mounting Hardware

- Use antenna masts or PVC pipes
- Guy wires for tall installations
- Ground plane if needed
- Lightning protection for permanent installations

### Positioning

- Mount as high as practical
- Clear line of sight to horizon
- Away from metal structures (>2m)
- Vertical orientation for LEO satellites

---

## Performance Comparison

| Antenna    | Frequency | Gain  | Pattern      | Difficulty | Cost |
|-----------|-----------|-------|--------------|------------|------|
| Dipole    | VHF/UHF   | 2 dBi | Omni         | Easy       | $10  |
| Turnstile | 137 MHz   | 3 dBi | Omni         | Easy       | $20  |
| QFH       | 137 MHz   | 4 dBi | Omni (CP)    | Moderate   | $35  |
| Yagi      | UHF       | 10+ dBi| Directional | Moderate   | $45  |
| Eggbeater | Dual-band | 5 dBi | Omni (CP)    | Advanced   | $50  |
| Helix     | S-band    | 12+ dBi| Directional | Advanced   | $60  |

**CP = Circular Polarization**

---

## Recommended First Antenna

**For beginners:** Start with a VHF Turnstile or QFH
- Easy to build
- Great for NOAA weather satellites
- Omnidirectional (no tracking needed)
- Forgiving design

**For intermediate:** Add a UHF Yagi
- Track satellites for better signals
- Decode CubeSat telemetry
- Learn about directional antennas

---

## Safety Notes

- Never work on antennas during storms
- Keep antennas away from power lines
- Ground metallic structures
- Use proper RF safety practices
- Follow local building codes

---

## Resources

### Online Calculators
- [ARRL Antenna Calculator](http://www.arrl.org/antenna-design-software)
- [66pacific: Antenna Tools](https://www.66pacific.com/calculators/)

### Communities
- r/amateurradio
- r/RTLSDR
- SatNOGS Forums
- AMSAT Mailing Lists

### Suppliers
- **Copper Wire:** Local hardware stores
- **PVC:** Home Depot, Lowe's
- **Connectors:** DX Engineering, Ham Radio Outlet
- **Coax:** Times Microwave, Belden

---

**Build once, receive forever!**
