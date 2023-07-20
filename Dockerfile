# Use the official Python base image
FROM python:3

# Install Bluetooth-related packages
RUN apt-get update && \
    apt-get install -y bluez bluez-hcidump && \
    apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the Python dependencies file
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script and settings file to the container
COPY ruuvi2mqtt.py .
COPY settings.py .

# Run the Python script as the default command
CMD ["python3", "ruuvi2mqtt.py"]
