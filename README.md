# flask-backend
Python Flask Repositories for LLM/OCR and other APIs

To install required python libraries 
pip install -r requirements.txt

To start the flask server
python app.py

Get .env file and add to home folder

If you are having issues with python packages due to existing ones installed. Create a virtual environment:

pip install virtualenv
virtualenv --version

Then inside the repo folder:
virtualenv venv
venv\Scripts\activate

Then your cmd or terminal should start with (venv)

Check if no packages are installed:
pip list

pip install -r requirements.txt

Now all the exact versions considering dependencies should be installed.

To exit this virtual environment:
deactivate

