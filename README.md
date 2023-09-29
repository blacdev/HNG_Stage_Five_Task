# File Storage, Transcribing, and Retrieval Application

Welcome to the documentation of the File Storage, Transcribing, and Retrieval Application. This application is a simple web application that allows users to upload files, transcribe them, and retrieve them. The application is built using the [FatAPI](https://fastapi.tiangolo.com/) framework and [PostgreSQL](https://www.postgresql.org/) database. The application is hosted on [render](https://render.com/).

Here is a **[link]()** to a live version of this application.

## Setup

 Follow the instructions below to setup the application on your local machine.

### Windows

1. **Install Python:** Download and install Python from [python.org](https://www.python.org/downloads/).
2. **Clone the Repository:** Use `git clone` to clone the application [repository](https://github.com/blacdev/HNG_Stage_Two.git).

3. **Install Dependencies:** Navigate to the project directory and run the following command to install required packages:

            pip install -r requirements.txt

### Linux & macOS

1. **Install Python:** Most Linux distributions and macOS come with Python pre-installed. You can verify by running `python --version`.

2. **Clone the Repository:** Use `git clone` to clone the application [repository](https://github.com/blacdev/HNG_Stage_Five_Task.git).

3. **Install Dependencies:** Navigate to the project directory and run the following command to install required packages:

          pip install -r requirements.txt

## Database Setup

The application uses postgresql provided by [render](https://render.com/). To setup the database, follow the instructions below:

1. **Signup:** Create an account on [render](https://render.com/).
2. **Create a Database:** Create a new database on render and copy the database URL.
3. **Set Environment Variable:** Set the environment variable `DATABASE_URL` to the database URL you copied in the previous step.


## Running the Application

After setting up the application, you can run it by running the following command in the project directory:

    python app.py