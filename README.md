# flask-backend
Python Flask Repositories for LLM/OCR and other APIs

## Installation

To install required Python libraries, use the following command:
```bash
pip install -r requirements.txt
```

## Running the Server

To start the Flask server, execute the following command:
```bash
python app.py
```

## Configuration

Get the `.env` file and add it to the home folder.

## Virtual Environment Setup (Optional)

If you encounter issues with existing Python packages, you can create a virtual environment.

### Install `virtualenv`

First, install `virtualenv` using pip:
```bash
pip install virtualenv
```

Verify the `virtualenv` version:
```bash
virtualenv --version
```

### Create and Activate Virtual Environment

Inside the repository folder:

Create a virtual environment named `venv`:
```bash
virtualenv venv
```

Activate the virtual environment:
- For Windows:
```bash
venv\Scripts\activate
```
- For Unix or MacOS:
```bash
source venv/bin/activate
```

Your command prompt or terminal should now display `(venv)` to indicate the virtual environment is active.

### Install Required Packages

Check if no packages are installed (optional):
```bash
pip list
```

Install the exact versions of required packages considering dependencies:
```bash
pip install -r requirements.txt
```

Use the below command if you have added any new packages
```bash
pip freeze > requirements.txt
```

### Deactivate Virtual Environment

To exit the virtual environment, use the following command:
```bash
deactivate
```
