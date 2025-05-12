from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/get_name", methods=["POST"])
def get_name():
    roll_number = request.form.get("roll_number")
    url = "https://info.aec.edu.in/ACET/olpayment.aspx"

    # Step 1: Start a session to handle cookies
    session = requests.Session()

    # Step 2: Load the page to get initial VIEWSTATE and validation fields
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract hidden form fields required for POST
    data = {
        "__VIEWSTATE": soup.find(id="__VIEWSTATE")["value"],
        "__VIEWSTATEGENERATOR": soup.find(id="__VIEWSTATEGENERATOR")["value"],
        "__EVENTVALIDATION": soup.find(id="__EVENTVALIDATION")["value"],
        "txtrollno": roll_number,
        "btnsearch": "Search"
    }

    # Step 3: Submit the roll number to get result
    post_response = session.post(url, data=data)
    soup = BeautifulSoup(post_response.text, "html.parser")

    # Step 4: Parse the result
    table = soup.find("table", class_="popupTable")
    if table:
        rows = table.find_all("tr")[1:]
        if rows:
            cols = rows[0].find_all("td")
            if len(cols) >= 2:
                name = cols[1].get_text(strip=True)
                return jsonify({"name": name})

    return jsonify({"name": "Not Found"})

# Bind to the dynamic port Render provides
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
