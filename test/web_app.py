from flask import Flask, render_template

app = Flask(__name__)


# Route to display the list of URLs and their status
@app.route('/')
def urls_status():
    urls = get_urls()  # Function to get the list of URLs and their status
    return render_template('index.html', urls=urls)

# Function to check the status of each URL
def get_urls():
    urls = [
        {'url': 'https://arsanrah.abramad.cloud/sg', 'status': check_url_status('https://arsanrah.abramad.cloud/sg')},
        {'url': 'https://hoonam-r.abramad.cloud/abramad', 'status': check_url_status('https://hoonam-r.abramad.cloud/abramad')},
        {'url': 'https://google.com', 'status': check_url_status('https://google.com')}
        # Add more URLs as needed
    ]
    return urls

# Function to check the status of a URL
def check_url_status(url):
    # Add code to check the status of the URL
    # Return True if the URL is up and contains the specific text, False otherwise
    return True  # Placeholder value for demonstration purposes
