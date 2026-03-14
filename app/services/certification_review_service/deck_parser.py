from flask import Flask, request, jsonify
from preprocess import *  # Import your existing functions here
  
# Initialize Flask app  
app = Flask(__name__)  
  
# Your Python program function (replace with your actual implementation)  
def deck_analyzer(file_path):  
    """  
    Example function to process a file.  
    Replace this with your actual implementation that analyzes the file.  
    """  
    try:
        response = analyze_inputdeck(file_path)
        return response  

    except FileNotFoundError:  
        response = {"status": "error", "details": f"File '{file_path}' not found"}  
    except Exception as e:  
        response = {"status": "error", "details": str(e)}  
  
    return response  
  
# Flask endpoint for `deck_analyzer`  
@app.route('/deck_analyzer', methods=['POST'])  
def deck_analyzer_endpoint():  
    try:  
        # Get the JSON data from request  
        request_data = request.get_json()  
  
        # Extract the file path from the JSON data  
        file_path = request_data.get("file_path")  
        if not file_path:  
            return jsonify({"status": "error", "details": "Missing 'file_path' in request"}), 400  
  
        # Call the `deck_analyzer` function with the file path  
        response = deck_analyzer(file_path)  
  
        # Return the dictionary response as JSON  
        return jsonify(response)  
  
    except Exception as e:  
        # Handle unexpected errors  
        return jsonify({"status": "error", "details": str(e)}), 500  
  
  
# Run Flask app  
if __name__ == '__main__':  
    # Use host='0.0.0.0' to make the server publicly accessible  
    app.run(host='0.0.0.0', port=5000)  
