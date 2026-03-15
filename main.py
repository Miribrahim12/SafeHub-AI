from flask import Flask, request, jsonify, render_template
from processor import ThreatAnalyzer
import os

app = Flask(__name__, template_folder='templates')
analyzer = ThreatAnalyzer()

# Müvəqqəti yaddaş (Server yenilənənə qədər datanı saxlayır)
# Real startapda bura Database (Firestore) olmalıdır
scan_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    result = analyzer.analyze_message(data['message'])
    
    # Tarixçəyə əlavə et
    scan_history.append({
        "type": result['threat_type'],
        "score": result['risk_score']
    })
    
    return jsonify({
        "result": result,
        "stats": {
            "total_scans": len(scan_history),
            "threats_found": len([x for x in scan_history if x['score'] > 6])
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))