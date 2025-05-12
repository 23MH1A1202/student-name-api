from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route("/get_name", methods=["POST"])
def get_name():
    roll_number = request.form.get("roll_number")

    if not roll_number:
        return jsonify({"name": "Roll number missing"})

    roll_number = roll_number.upper()

    # Choose the correct URL based on roll number prefix
    if "A9" in roll_number:
        url = "https://info.aec.edu.in/AEC/olpayment.aspx"
    else:
        url = "https://info.aec.edu.in/ACET/olpayment.aspx"

    try:
        # Step 1: Start a session and get VIEWSTATE, etc.
        session = requests.Session()
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        data = {
            "__VIEWSTATE": soup.find(id="__VIEWSTATE")["value"],
            "__VIEWSTATEGENERATOR": soup.find(id="__VIEWSTATEGENERATOR")["value"],
            "__EVENTVALIDATION": soup.find(id="__EVENTVALIDATION")["value"],
            "txtrollno": roll_number,
            "btnsearch": "Search"
        }

        # Step 2: POST the form
        post_response = session.post(url, data=data)
        soup = BeautifulSoup(post_response.text, "html.parser")

        # Step 3: Extract name
        table = soup.find("table", class_="popupTable")
        if table:
            rows = table.find_all("tr")[1:]
            if rows:
                cols = rows[0].find_all("td")
                if len(cols) >= 2:
                    name = cols[1].get_text(strip=True)
                    return jsonify({"name": name})
    except Exception as e:
        return jsonify({"name": "Error", "error": str(e)})

    return jsonify({"name": "Not Found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
