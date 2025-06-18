#!/bin/bash

#set the project
gcloud config set project speech-analyst-ecc

#enable apis
gcloud services enable documentai.googleapis.com
gcloud services enable storage.googleapis.com

# enter the folder
#cd audio_entity_extraction/

# Create a new virtual environment
#virtualenv entity_extraction_env

# Activate the virtual environment
source entity_extraction_env/bin/activate

# Install the dependencies
pip install -r requirements.txt

# Upgrade. if necessary
#pip install -r requirements.txt --upgrade

# Run the script
python3 main.py 

gcloud auth application-default login

# Deactivate the virtual environment
#deactivate



