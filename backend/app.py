from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from solver import PDESolver

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "PDE Solver Backend is running"})

@app.route('/solve', methods=['POST'])
def solve_pde():
    try:
        data = request.json
        equation = data.get('equation', 'uxx + uyy') # Default heat eq
        domain = data.get('domain', {
            'x_min': 0, 'x_max': 3.14159,
            'y_min': 0, 'y_max': 3.14159,
            't_max': 1.0,
            'nx': 20, 'ny': 20,
            'dt': 0.001
        })
        ic = data.get('ic', 'sin(x)*sin(y)')
        bc = data.get('bc', {})
        
        solver = PDESolver(equation, domain, ic, bc)
        result = solver.solve()
        
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
