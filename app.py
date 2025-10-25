from flask import Flask, render_template, request, jsonify, send_file
from model import EnhancedStockAnalyzer
import os
import traceback
from datetime import datetime
import base64

app = Flask(__name__)

# Use /tmp directory for Vercel (serverless environment)
TEMP_DIR = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure temp directory exists (though /tmp always exists in Vercel)
os.makedirs(TEMP_DIR, exist_ok=True)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_stock():
    """
    Analyze stock and generate PDF report
    Accepts: { "stock_name": "TCS" }
    Returns: { "success": bool, "pdf_filename": str, "message": str }
    """
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
            # Move PDF to /tmp folder if it's not already there
            if not pdf_path.startswith(TEMP_DIR):
                new_path = os.path.join(TEMP_DIR, os.path.basename(pdf_path))
                if os.path.exists(pdf_path):
                    os.rename(pdf_path, new_path)
                    pdf_path = new_path
            
            # Get filename
            pdf_filename = os.path.basename(pdf_path)
            
            # Optional: Read PDF as base64 for direct download in frontend
            with open(pdf_path, 'rb') as f:
                pdf_data = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'pdf_filename': pdf_filename,
                'pdf_data': pdf_data,  # Base64 encoded PDF for immediate download
                'message': 'Analysis completed successfully!',
                'results': analyzer.analysis_results
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate analysis report. Please check if the stock symbol is valid.'
            }), 500
            
    except ValueError as ve:
        # Handle specific validation errors
        print(f"Validation error: {ve}")
        return jsonify({
            'success': False,
            'error': f'Invalid input: {str(ve)}'
        }), 400
        
    except Exception as e:
        # Handle general errors
        print(f"Error in analyze_stock: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}. Please verify the stock symbol and try again.'
        }), 500


@app.route('/download/<filename>')
def download_pdf(filename):
    """
    Download generated PDF report
    """
    try:
        # Sanitize filename to prevent directory traversal
        filename = os.path.basename(filename)
        file_path = os.path.join(TEMP_DIR, filename)
        
        if os.path.exists(file_path):
            return send_file(
                file_path, 
                as_attachment=True, 
                download_name=filename,
                mimetype='application/pdf'
            )
        else:
            return jsonify({
                'error': 'File not found. The report may have expired.'
            }), 404
            
    except Exception as e:
        print(f"Error downloading file: {e}")
        traceback.print_exc()
        return jsonify({
            'error': f'Download failed: {str(e)}'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Stock Analysis API'
    })


# This section is only for local development
# Vercel will ignore this when deployed
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
