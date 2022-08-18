sudo apt install build-essential python3-dev python3-venv -y
sudo apt install python3-gi \
 libcairo2-dev \
 python3-gi-cairo \
 gir1.2-gtk-3.0 \
 python3-pyaudio \
 portaudio19-dev \
 libatlas-base-dev \
 espeak-ng \
 libcec-dev \
 swig \
 libpulse-dev -y
 
python -m venv ./ 
source bin/activate
pip install -r requirements.txt
