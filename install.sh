sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pyaudio portaudio19-dev libatlas-base-dev espeak-ng
if [ -e deepspeech-0.9.*-models.tflite ]
then
    echo "Models are already present"
else
    echo "Downloading tflite model and scorer"
    wget "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm"
    wget "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer"
fi

virtualenv ./ --python=python3
source bin/activate
pip3 install -r requirements.txt