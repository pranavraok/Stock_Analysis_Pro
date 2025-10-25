from flask import Flask, render_template, request, jsonify, send_file
from model import EnhancedStockAnalyzer
import os
import traceback
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'reports'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure reports directory exists
os.makedirs('reports', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.get_json()
        stock_name = data.get('stock_name', '').strip()
        
        if not stock_name:
            return jsonify({
                'success': False,
                'error': 'Please enter a stock name'
            }), 400
        
        # Create analyzer instance
        analyzer = EnhancedStockAnalyzer(stock_name)
        
        # Run complete analysis
        pdf_path = analyzer.run_complete_analysis()
        
        if pdf_path and os.path.exists(pdf_path):
            # Move PDF to reports folder
            new_path = os.path.join('reports', os.path.basename(pdf_path))
            if os.path.exists(pdf_path):
                os.rename(pdf_path, new_path)
                pdf_path = new_path
            
            return jsonify({
                'success': True,
                'pdf_filename': os.path.basename(pdf_path),
                'message': 'Analysis completed successfully!',
                'results': analyzer.analysis_results
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate analysis report. Please check if the stock symbol is valid.'
            }), 500
            
    except Exception as e:
        print(f"Error in analyze_stock: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_pdf(filename):
    try:
        file_path = os.path.join('reports', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)