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

const data = await response.json();

clearInterval(loadingInterval);

if (data.success) {
currentPdfFilename = data.pdf_filename;
displayResults(data.results, stockName);
showPage(resultsPage);
} else {
showError(data.error || 'Analysis failed. Please check the stock symbol and try again.');
showPage(inputPage);
}
} catch (error) {
clearInterval(loadingInterval);
console.error('Error:', error);
showError('Connection error. Please check your internet connection and try again.');
showPage(inputPage);
}
}

// Display results
function displayResults(results, stockName) {
// Stock symbol and company name
const ticker = stockName.toUpperCase().replace('.NS', '').replace('.BO', '');
document.getElementById('stockSymbol').textContent = ticker;

const companyName = results.company_details?.company_name || `${ticker} Limited`;
document.getElementById('companyName').textContent = companyName;

// Verdict
const verdict = results.verdict || {};
const verdictValue = verdict.verdict || 'HOLD';
const verdictEl = document.getElementById('verdictValue');
const verdictBadge = document.getElementById('verdictBadge');
verdictEl.textContent = verdictValue;

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

// Current price
const priceAnalysis = results.price_analysis || {};
const currentPrice = priceAnalysis.current_price || 0;
document.getElementById('priceValue').textContent = `₹${currentPrice.toFixed(2)}`;
}

// Download PDF
function downloadPDF() {
if (currentPdfFilename) {
window.location.href = '/download/' + currentPdfFilename;
} else {
showError('No report available for download');
}
}

// New analysis
function newAnalysis() {
stockInput.value = '';
currentPdfFilename = null;
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
stockInput.focus();
addMagneticEffect();

// Add gradient to SVG
const svg = document.querySelector('.logo-icon');
if (svg && !document.getElementById('gradient1')) {
const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
gradient.setAttribute('id', 'gradient1');
gradient.setAttribute('x1', '0%');
gradient.setAttribute('y1', '0%');
gradient.setAttribute('x2', '100%');
gradient.setAttribute('y2', '100%');

const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
stop1.setAttribute('offset', '0%');
stop1.setAttribute('style', 'stop-color:#8b5cf6;stop-opacity:1');

const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
stop2.setAttribute('offset', '100%');
stop2.setAttribute('style', 'stop-color:#ec4899;stop-opacity:1');

gradient.appendChild(stop1);
gradient.appendChild(stop2);
defs.appendChild(gradient);
svg.appendChild(defs);
}
});

// Smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';
