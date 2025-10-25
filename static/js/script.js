// Stock Analysis Pro - Complete Fixed JavaScript

// Page elements
const inputPage = document.getElementById('inputPage');
const loadingPage = document.getElementById('loadingPage');
const resultsPage = document.getElementById('resultsPage');
const stockInput = document.getElementById('stockInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const downloadBtn = document.getElementById('downloadBtn');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const errorToast = document.getElementById('errorToast');
const errorMessage = document.getElementById('errorMessage');

let currentPdfFilename = null;
let currentPdfData = null; // 🔥 CRITICAL FIX: Added this line to store base64 PDF data

// Loading animation steps
const loadingSteps = [
    { text: 'Connecting to market data sources...', progress: 15, step: 1 },
    { text: 'Fetching real-time stock information...', progress: 30, step: 1 },
    { text: 'Analyzing historical price trends...', progress: 45, step: 2 },
    { text: 'Calculating technical indicators...', progress: 60, step: 2 },
    { text: 'Evaluating fundamental metrics...', progress: 75, step: 3 },
    { text: 'Running AI analysis algorithms...', progress: 85, step: 3 },
    { text: 'Generating professional PDF report...', progress: 95, step: 3 },
    { text: 'Finalizing analysis...', progress: 100, step: 3 }
];

// Show page function
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    page.classList.add('active');
}

// Show error toast
function showError(message) {
    errorMessage.textContent = message;
    errorToast.classList.add('show');
    setTimeout(() => {
        errorToast.classList.remove('show');
    }, 5000);
}

// Simulate loading progress
function simulateLoading() {
    let currentStep = 0;
    const loadingText = document.getElementById('loadingText');
    const progressFill = document.getElementById('progressFill');
    const loaderPercentage = document.getElementById('loaderPercentage');

    const interval = setInterval(() => {
        if (currentStep < loadingSteps.length) {
            const step = loadingSteps[currentStep];
            loadingText.textContent = step.text;
            progressFill.style.width = step.progress + '%';
            loaderPercentage.textContent = step.progress + '%';

            // Activate step indicator
            const stepEl = document.getElementById('step' + step.step);
            if (stepEl && !stepEl.classList.contains('active')) {
                // Remove active from previous steps
                document.querySelectorAll('.step-modern.active').forEach(s => {
                    s.classList.remove('active');
                    s.classList.add('completed');
                });
                stepEl.classList.add('active');
            }

            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 1500);

    return interval;
}

// Analyze stock
async function analyzeStock() {
    const stockName = stockInput.value.trim();

    if (!stockName) {
        showError('Please enter a stock symbol to analyze');
        stockInput.focus();
        return;
    }

    console.log('=== Starting analysis for:', stockName);

    // Show loading page
    showPage(loadingPage);

    // Reset loading indicators
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('loaderPercentage').textContent = '0%';
    document.querySelectorAll('.step-modern').forEach(step => {
        step.classList.remove('active', 'completed');
    });

    // Start loading animation
    const loadingInterval = simulateLoading();

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ stock_name: stockName })
        });

        console.log('Response status:', response.status);

        const data = await response.json();
        console.log('Response data:', data);

        clearInterval(loadingInterval);

        if (data.success) {
            currentPdfFilename = data.pdf_filename;
            currentPdfData = data.pdf_data; // 🔥 CRITICAL FIX: Store base64 PDF data
            
            console.log('✓ Analysis successful!');
            console.log('✓ PDF filename:', currentPdfFilename);
            console.log('✓ Has PDF data:', !!currentPdfData);
            console.log('✓ PDF data length:', currentPdfData ? currentPdfData.length : 0);
            
            displayResults(data.results, stockName);
            showPage(resultsPage);
        } else {
            console.error('❌ Analysis failed:', data.error);
            showError(data.error || 'Analysis failed. Please check the stock symbol and try again.');
            showPage(inputPage);
        }
    } catch (error) {
        clearInterval(loadingInterval);
        console.error('❌ Network error:', error);
        showError('Connection error. Please check your internet connection and try again.');
        showPage(inputPage);
    }
}

// Display results
function displayResults(results, stockName) {
    console.log('=== Displaying results ===');
    console.log('Stock name:', stockName);
    console.log('Results:', results);

    // Stock symbol and company name
    const ticker = stockName.toUpperCase().replace('.NS', '').replace('.BO', '');
    document.getElementById('stockSymbol').textContent = ticker;
    console.log('✓ Set ticker:', ticker);

    const companyName = results.company_details?.company_name || `${ticker} Limited`;
    document.getElementById('companyName').textContent = companyName;
    console.log('✓ Set company name:', companyName);

    // Verdict
    const verdict = results.verdict || {};
    const verdictValue = verdict.verdict || 'HOLD';
    const verdictEl = document.getElementById('verdictValue');
    const verdictBadge = document.getElementById('verdictBadge');
    verdictEl.textContent = verdictValue;
    console.log('✓ Set verdict:', verdictValue);

    // Set verdict color and badge
    if (verdictValue.includes('BUY')) {
        verdictEl.style.background = 'linear-gradient(135deg, #10b981, #059669)';
        verdictEl.style.webkitBackgroundClip = 'text';
        verdictEl.style.webkitTextFillColor = 'transparent';
        verdictBadge.textContent = 'Bullish';
        verdictBadge.style.background = 'rgba(16, 185, 129, 0.2)';
        verdictBadge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        verdictBadge.style.color = '#10b981';
    } else if (verdictValue.includes('HOLD') || verdictValue.includes('ACCUMULATE')) {
        verdictEl.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
        verdictEl.style.webkitBackgroundClip = 'text';
        verdictEl.style.webkitTextFillColor = 'transparent';
        verdictBadge.textContent = 'Neutral';
        verdictBadge.style.background = 'rgba(245, 158, 11, 0.2)';
        verdictBadge.style.borderColor = 'rgba(245, 158, 11, 0.3)';
        verdictBadge.style.color = '#f59e0b';
    } else {
        verdictEl.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
        verdictEl.style.webkitBackgroundClip = 'text';
        verdictEl.style.webkitTextFillColor = 'transparent';
        verdictBadge.textContent = 'Bearish';
        verdictBadge.style.background = 'rgba(239, 68, 68, 0.2)';
        verdictBadge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
        verdictBadge.style.color = '#ef4444';
    }

    // Confidence with animated ring
    const confidence = verdict.confidence || 50;
    document.getElementById('confidenceValue').textContent = confidence + '%';
    const confidenceRing = document.getElementById('confidenceRing');
    const circumference = 2 * Math.PI * 40; // radius is 40
    const offset = circumference - (confidence / 100) * circumference;
    setTimeout(() => {
        confidenceRing.style.strokeDashoffset = offset;
    }, 100);
    console.log('✓ Set confidence:', confidence + '%');

    // Current price
    const priceAnalysis = results.price_analysis || {};
    const currentPrice = priceAnalysis.current_price || 0;
    document.getElementById('priceValue').textContent = `₹${currentPrice.toFixed(2)}`;
    console.log('✓ Set price:', currentPrice);

    console.log('=== Results display complete ===');
}

// Download PDF
function downloadPDF() {
    console.log('=== Download button clicked ===');
    console.log('Current PDF filename:', currentPdfFilename);
    console.log('Has PDF data:', !!currentPdfData);
    console.log('PDF data length:', currentPdfData ? currentPdfData.length : 0);

    if (currentPdfData) {
        // 🔥 CRITICAL FIX: Use base64 data for direct download (PRIMARY METHOD)
        console.log('Downloading using base64 data...');
        try {
            const link = document.createElement('a');
            link.href = `data:application/pdf;base64,${currentPdfData}`;
            link.download = currentPdfFilename || 'stock_analysis.pdf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            console.log('✓ Download initiated successfully!');
        } catch (error) {
            console.error('❌ Base64 download failed:', error);
            // Fallback to endpoint
            if (currentPdfFilename) {
                console.log('Trying fallback download endpoint...');
                window.location.href = '/download/' + currentPdfFilename;
            }
        }
    } else if (currentPdfFilename) {
        // Fallback to download endpoint
        console.log('Downloading using endpoint:', `/download/${currentPdfFilename}`);
        window.location.href = '/download/' + currentPdfFilename;
    } else {
        console.error('❌ No PDF available for download');
        showError('No report available for download. Please try analyzing again.');
    }
}

// New analysis
function newAnalysis() {
    console.log('=== Starting new analysis ===');
    stockInput.value = '';
    currentPdfFilename = null;
    currentPdfData = null; // 🔥 CRITICAL FIX: Reset PDF data
    showPage(inputPage);
    stockInput.focus();

    // Reset loading indicators
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('loaderPercentage').textContent = '0%';
    document.querySelectorAll('.step-modern').forEach(step => {
        step.classList.remove('active', 'completed');
    });
}

// Magnetic button effect
function addMagneticEffect() {
    const magneticBtns = document.querySelectorAll('.magnetic-btn');

    magneticBtns.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            btn.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translate(0, 0)';
        });
    });
}

// Event listeners
analyzeBtn.addEventListener('click', analyzeStock);
downloadBtn.addEventListener('click', downloadPDF);
newAnalysisBtn.addEventListener('click', newAnalysis);

stockInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault(); // 🔥 CRITICAL FIX: Prevent form submission
        analyzeStock();
    }
});

// Input animation
stockInput.addEventListener('input', (e) => {
    if (e.target.value) {
        e.target.style.transform = 'scale(1.01)';
        setTimeout(() => {
            e.target.style.transform = 'scale(1)';
        }, 100);
    }
});

// Initialize
window.addEventListener('load', () => {
    console.log('=== Stock Analysis Pro Loaded ===');
    console.log('Version: 2.0');
    console.log('All elements:', {
        inputPage: !!inputPage,
        loadingPage: !!loadingPage,
        resultsPage: !!resultsPage,
        stockInput: !!stockInput,
        analyzeBtn: !!analyzeBtn,
        downloadBtn: !!downloadBtn,
        newAnalysisBtn: !!newAnalysisBtn
    });
    
    stockInput.focus();
    addMagneticEffect();

    // SVG gradient is already in HTML, no need to add dynamically
    console.log('✓ Initialization complete');
});

// Smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';

console.log('✓ Script loaded successfully');
