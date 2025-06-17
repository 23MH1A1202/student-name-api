from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ✅ Route: Health check
@app.route('/ping', methods=['GET'])
def ping():
    return "OK", 200

# ✅ Route: Get student name from roll number
@app.route("/get_name", methods=["POST"])
def get_name():
    roll_number = request.form.get("roll_number")

    if not roll_number:
        return jsonify({"name": "Roll number missing"})

    roll_number = roll_number.upper()

    if "A9" in roll_number:
        url = "https://info.aec.edu.in/AEC/olpayment.aspx"
    else:
        url = "https://info.aec.edu.in/ACET/olpayment.aspx"

    try:
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

        post_response = session.post(url, data=data)
        soup = BeautifulSoup(post_response.text, "html.parser")

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

# ✅ Route: Search students by name and return roll, name, branch, campus
@app.route("/resolve_name_to_roll", methods=["POST"])
def resolve_name_to_roll():
    name_query = request.form.get("query", "").strip().lower()
    if not name_query or len(name_query) < 3:
        return jsonify([])

    # Only allowed prefixes
    valid_prefixes = ("MH", "P3", "A9")
    valid_years = {"21", "22", "23", "24", "25", "26", "27", "28", "29" ,"30"}

    branch_map = {
        "01": "CE", "02": "EEE", "03": "ME", "04": "ECE", "05": "CSE",
        "12": "IT", "14": "ECT", "15": "CSSE", "19": "ECE", "26": "Mining",
        "27": "PT", "00": "Pharma", "42": "CSE(AIML)", "44": "DS", "49": "IoT", "61":"AIML"
    }

    campus_map = {
        "MH": "ACOE",
        "P3": "ACET",
        "A9": "AEC"
    }

    urls = {
        "ACET": "https://info.aec.edu.in/ACET/olpayment.aspx",
        "AEC": "https://info.aec.edu.in/AEC/olpayment.aspx"
    }

    grouped_results = {
        "MH": [],
        "P3": [],
        "A9": []
    }

    for college, url in urls.items():
        try:
            session = requests.Session()
            response = session.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            data = {
                "__VIEWSTATE": soup.find(id="__VIEWSTATE")["value"],
                "__VIEWSTATEGENERATOR": soup.find(id="__VIEWSTATEGENERATOR")["value"],
                "__EVENTVALIDATION": soup.find(id="__EVENTVALIDATION")["value"],
                "txtname": name_query,
                "btnsearch": "Search"
            }

            post_response = session.post(url, data=data)
            soup = BeautifulSoup(post_response.text, "html.parser")
            table = soup.find("table", class_="popupTable")

            if not table:
                continue

            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    roll = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)

                    if name_query not in name.lower():
                        continue
                    if roll[:2] not in valid_years:
                        continue
                    if "B11" in roll:
                        continue

                    series = roll[2:4]
                    if series not in valid_prefixes:
                        continue

                    branch_code = roll[6:8]
                    branch = branch_map.get(branch_code, "Unknown")
                    campus = campus_map.get(series, "Unknown")

                    grouped_results[series].append({
                        "roll": roll,
                        "name": name,
                        "branch": branch,
                        "campus": campus
                    })

        except Exception as e:
            print(f"Error in {college} lookup:", e)
            continue

    final_results = grouped_results["MH"] + grouped_results["P3"] + grouped_results["A9"]
    return jsonify(final_results)

# ✅ Optional homepage message
@app.route('/')
def home():
    return "Flask backend is running.", 200

# ✅ Start the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
