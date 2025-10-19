FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install RTL-SDR and dependencies
RUN apt-get update && apt-get install -y \
    rtl-sdr \
    librtlsdr0 \
    librtlsdr-dev \
    libusb-1.0-0-dev \
    udev \
    && rm -rf /var/lib/apt/lists/*

# Create udev rules for RTL-SDR
RUN echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", MODE="0666"' > /etc/udev/rules.d/20-rtlsdr.rules

# Expose rtl_tcp port
EXPOSE 1234

# Default command: start rtl_tcp server
CMD ["rtl_tcp", "-a", "0.0.0.0", "-p", "1234"]
