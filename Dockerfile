# Use a base image with Python installed
FROM python:3.10.16

# Set the working directory inside the container
WORKDIR /fashion_project

# Copy the complete working directory to remote directory
COPY . /fashion_project

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#building the custom packages
RUN pip install .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Set the entry point or default command for the container
CMD ["python", "./app.py"]  # Adjust as per your project structure