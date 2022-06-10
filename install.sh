sudo apt install build-essential python-dev
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pyaudio portaudio19-dev libatlas-base-dev espeak-ng libcec-dev
if [ -e deepspeech-0.9.*-models.tflite ]
then
    echo "Models are already present"
else
    echo "Downloading tflite model and scorer"
    wget "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm"
    wget "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer"
fi

python -m venv ./ 
source bin/activate
pip install -r requirements.txt
