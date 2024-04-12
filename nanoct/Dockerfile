FROM python:3.9

# Install LevelDB and Python bindings
RUN apt-get update && apt-get install -y libleveldb-dev
RUN pip install plyvel

WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy application files
COPY . .

CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:5000"]

