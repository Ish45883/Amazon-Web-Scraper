from flask import Flask, render_template, request, jsonify, url_for
from scraper import get_product_details
import webbrowser
import threading
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

def open_browser():
    """Function to open the browser after a short delay"""
    time.sleep(1.5)  # Wait for the server to start
    webbrowser.open('http://127.0.0.1:5000')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        product_url = data.get('url', '').strip()
        
        if not product_url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Check if it's an Amazon URL
        if not ('amazon.in' in product_url or 'amazon.com' in product_url):
            return jsonify({'error': 'Please enter a valid Amazon product URL'}), 400
        
        # Add http:// if not present
        if not product_url.startswith(('http://', 'https://')):
            product_url = 'https://' + product_url
        
        # Try to get product details
        product_details = get_product_details(product_url)
        
        if not product_details:
            return jsonify({'error': 'Could not fetch product details'}), 404
        
        # Format price with commas for Indian numbering system
        if 'price' in product_details:
            try:
                price = int(product_details['price'])
                product_details['formatted_price'] = format_indian_price(price)
            except:
                pass
        
        return jsonify(product_details)
    except Exception as e:
        print(f"Error in scrape route: {str(e)}")  # Debug log
        return jsonify({'error': 'Could not fetch product details. Please check the URL and try again.'}), 500

def format_indian_price(price):
    """Format price with commas for Indian numbering system"""
    s = str(price)
    l = len(s)
    if l > 3:
        i = l - 3
        s = s[:i] + ',' + s[i:]
        i -= 2
        while i > 0:
            s = s[:i] + ',' + s[i:]
            i -= 2
    return '₹' + s

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Start the browser opening function in a new thread
    threading.Thread(target=open_browser).start()
    # Start the Flask application
    app.run(debug=True, use_reloader=False)
