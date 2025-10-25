import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from fpdf import FPDF
import requests
import os
import warnings
import time

warnings.filterwarnings('ignore')

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def get_full_stock_name(stock_name):
    if not stock_name:
        raise ValueError("Stock name cannot be empty")
    
    stock_name = stock_name.upper().strip()
    
    if not stock_name.endswith((".NS", ".BO", ".BSE", ".NSE")):
        stock_name = stock_name + ".NS"
    
    return stock_name

def get_usd_to_inr():
    try:
        url_primary = "https://api.exchangerate-api.com/v4/latest/USD"
        response_primary = requests.get(url_primary, timeout=5)
        
        if response_primary.status_code == 200:
            data = response_primary.json()
            if "rates" in data and "INR" in data["rates"]:
                rate = data["rates"]["INR"]
                print(f"Currency Rate: {rate:.2f}")
                return rate
    except Exception as e:
        print(f"Primary exchange rate API failed: {e}")

    try:
        url_secondary = "https://api.exchangerate.host/latest?base=USD&symbols=INR"
        response_secondary = requests.get(url_secondary, timeout=5)
        
        if response_secondary.status_code == 200:
            data = response_secondary.json()
            if "rates" in data and "INR" in data["rates"]:
                rate = data["rates"]["INR"]
                return rate
    except Exception as e:
        print(f"Secondary exchange rate API failed: {e}")
    
    return 87.80

def safe_str(value):
    try:
        text = str(value)
        text = text.replace('Rs.', 'Rs.')
        text = text.encode('ascii', 'replace').decode('ascii')
        return text
    except Exception:
        return "N/A"

def calculate_rsi(prices, period=14):
    try:
        if len(prices) < period:
            return None
        
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        print(f"RSI calculation error: {e}")
        return None

def fetch_with_retry(stock_symbol, max_retries=3, backoff=2):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    end_date_str = end_date.strftime('%Y-%m-%d')
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    for attempt in range(max_retries):
        try:
            print(f"Downloading {stock_symbol}... (Attempt {attempt + 1}/{max_retries})")
            
            data = yf.download(
                stock_symbol, 
                start=start_date_str, 
                end=end_date_str,
                progress=False,
                timeout=30
            )
            
            if data is not None and not data.empty and len(data) > 50:
                print(f"Downloaded {len(data)} days of data")
                return data
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                wait_time = backoff ** attempt
                time.sleep(wait_time)
    
    return None

# =====================================================
# PROFESSIONAL PDF CLASS
# =====================================================

class ProfessionalStockPDF(FPDF):
    
    HEADER_COLOR = (24, 44, 68)      
    ACCENT_COLOR = (41, 128, 185)    
    GOOD_COLOR = (39, 174, 96)        
    BAD_COLOR = (231, 76, 60)        
    NEUTRAL_COLOR = (243, 156, 18)    
    TEXT_DARK = (33, 47, 61)          
    TEXT_LIGHT = (149, 165, 166)      

    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.page_height = 297
        self.margin_bottom = 20
        self.margin_top = 15
        self.margin_left = 15
        self.margin_right = 15
        
    def footer(self):
        """Footer with page number in bottom right corner"""
        self.set_y(-15)
        self.set_font('Arial', '', 8)
        self.set_text_color(*self.TEXT_LIGHT)
        page_text = f'Page {self.page_no()}'
        self.cell(0, 10, page_text, 0, 0, 'R')
        
    def add_main_header(self, title, subtitle=""):
        self.set_fill_color(*self.HEADER_COLOR)
        self.rect(0, 0, 210, 45, 'F')
        
        self.set_font("Arial", "B", 26)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, 12)
        self.cell(0, 10, title, 0, 1, 'C')
        
        if subtitle:
            self.set_font("Arial", "", 12)
            self.set_text_color(200, 220, 255)
            self.set_xy(15, 26)
            self.cell(0, 8, subtitle, 0, 1, 'C')
        
        self.set_xy(15, 52)
        self.set_text_color(*self.TEXT_DARK)
    
    def add_section_header(self, title):
        """Section header with horizontal line below"""
        self.ln(3)
        self.set_font("Arial", "B", 13)
        self.set_fill_color(*self.HEADER_COLOR)
        self.set_text_color(255, 255, 255)
        self.cell(0, 9, f"  {title}", 0, 1, "L", True)
        self.ln(2)
        self.set_text_color(*self.TEXT_DARK)
    
    def add_section_separator(self):
        """Add horizontal line separator after sections"""
        self.ln(2)
        self.set_draw_color(*self.TEXT_LIGHT)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
    
    def add_info_pair(self, label, value, bold_value=False):
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.TEXT_DARK)
        
        self.cell(70, 6, safe_str(label) + ":", 0, 0, "L")
        
        self.set_font("Arial", "B" if bold_value else "", 10)
        self.cell(0, 6, safe_str(value), 0, 1, "L")
    
    def add_colored_box(self, label, value, status_color, reasoning=""):
        """Add colored recommendation box with reasoning inside"""
        if status_color == "good":
            self.set_fill_color(*self.GOOD_COLOR)
        elif status_color == "bad":
            self.set_fill_color(*self.BAD_COLOR)
        else:
            self.set_fill_color(*self.NEUTRAL_COLOR)
        
        self.ln(2)
        
        self.set_font("Arial", "B", 11)
        self.set_text_color(255, 255, 255)
        
        self.cell(180, 9, f"  {safe_str(label)}", 0, 1, "L", True)
        
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.TEXT_DARK)
        self.set_x(20)
        self.cell(170, 6, f"{safe_str(value)}", 0, 1)
        
        if reasoning:
            self.ln(1)
            self.set_font("Arial", "", 9)
            self.set_text_color(*self.TEXT_DARK)
            self.set_x(20)
            self.multi_cell(170, 4.5, f"{reasoning}", 0, 'L')
        
        self.ln(2)
    
    def check_page_space(self, space_needed=60):
        if self.get_y() + space_needed > self.page_height - self.margin_bottom:
            self.add_page()
            return True
        return False

# =====================================================
# ENHANCED STOCK ANALYZER CLASS
# =====================================================

class EnhancedStockAnalyzer:
    
    def __init__(self, stock_name):
        self.stock_name = get_full_stock_name(stock_name)
        self.end_date = datetime.today()
        self.start_date = self.end_date - timedelta(days=365)
        
        self.data = None
        self.stock_info = None
        self.rsi = None
        self.analysis_results = {}
        
        # IMPORTANT: Use /tmp directory for Vercel
        self.temp_dir = '/tmp'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"Initializing analysis for {self.stock_name}...")
        print(f"{'='*70}\n")
    
    def fetch_data(self):
        try:
            end_date_str = self.end_date.strftime('%Y-%m-%d')
            start_date_str = self.start_date.strftime('%Y-%m-%d')
            
            print(f"Fetching data from {start_date_str} to {end_date_str}...")
            
            self.data = fetch_with_retry(self.stock_name)
            
            if self.data is None or self.data.empty:
                alt_symbol = self.stock_name.replace(".NS", ".BO")
                print(f"Trying {alt_symbol}...")
                self.data = fetch_with_retry(alt_symbol)
                if self.data is not None and not self.data.empty:
                    self.stock_name = alt_symbol
            
            if self.data is None or self.data.empty:
                raise ValueError(f"No data for {self.stock_name}")
            
            if len(self.data) < 50:
                raise ValueError(f"Insufficient data: {len(self.data)} days")
            
            print("Data ready")
            return True
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False
    
    def fetch_stock_info(self):
        try:
            print("Fetching company information...")
            
            ticker = yf.Ticker(self.stock_name)
            self.stock_info = ticker.info
            
            if not self.stock_info:
                raise ValueError("No info available")
            
            print("Company info ready")
            return True
            
        except Exception as e:
            print(f"Limited info available: {e}")
            self.stock_info = {}
            return True
    
    def get_company_details(self):
        """Gather comprehensive company details"""
        try:
            details = {
                'company_name': self.stock_info.get('shortName', 'N/A'),
                'sector': self.stock_info.get('sector', 'N/A'),
                'industry': self.stock_info.get('industry', 'N/A'),
                'market_cap': self.stock_info.get('marketCap', 0),
                'book_value': self.stock_info.get('bookValue', 0),
                'trailing_eps': self.stock_info.get('trailingEps', 0),
                'forward_eps': self.stock_info.get('forwardEps', 0),
                'dividend_yield': self.stock_info.get('dividendYield', 0),
                'fifty_two_week_high': self.stock_info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': self.stock_info.get('fiftyTwoWeekLow', 0),
                'average_volume': self.stock_info.get('averageVolume', 0),
                'beta': self.stock_info.get('beta', 0),
                'website': self.stock_info.get('website', 'N/A')
            }
            
            self.analysis_results['company_details'] = details
            return details
        except Exception as e:
            print(f"Error fetching company details: {e}")
            self.analysis_results['company_details'] = {}
            return {}
    
    def analyze_price_data(self):
        """Comprehensive price analysis"""
        try:
            close_prices = self.data['Close']
            high_prices = self.data['High']
            low_prices = self.data['Low']
            volume_data = self.data['Volume']
            
            current_price = float(close_prices.iloc[-1])
            previous_close = float(close_prices.iloc[-2]) if len(close_prices) > 1 else current_price
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100 if previous_close != 0 else 0
            
            high_52w = float(high_prices.max())
            low_52w = float(low_prices.min())
            
            ma_50 = float(close_prices.tail(50).mean())
            ma_200 = float(close_prices.tail(200).mean()) if len(close_prices) >= 200 else ma_50
            
            distance_from_high = ((high_52w - current_price) / high_52w) * 100
            distance_from_low = ((current_price - low_52w) / low_52w) * 100
            
            avg_volume = float(volume_data.tail(30).mean())
            current_volume = float(volume_data.iloc[-1])
            volume_signal = "Above average" if current_volume > avg_volume else "Below average"
            
            if current_price > ma_50 > ma_200:
                price_trend = "Strong Uptrend"
                price_trend_good = True
            elif current_price > ma_50:
                price_trend = "Uptrend"
                price_trend_good = True
            elif current_price > ma_200:
                price_trend = "Neutral"
                price_trend_good = None
            else:
                price_trend = "Downtrend"
                price_trend_good = False
            
            self.analysis_results['price_analysis'] = {
                'current_price': current_price,
                'previous_close': previous_close,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'high_52w': high_52w,
                'low_52w': low_52w,
                'ma_50': ma_50,
                'ma_200': ma_200,
                'distance_from_high': distance_from_high,
                'distance_from_low': distance_from_low,
                'avg_volume': avg_volume,
                'current_volume': current_volume,
                'volume_signal': volume_signal,
                'price_trend': price_trend,
                'price_trend_good': price_trend_good
            }
            
            print(f"Price Analysis: {price_trend} | Current: Rs.{current_price:.2f} | Change: {price_change_pct:+.2f}%")
            return True
        except Exception as e:
            print(f"Error in price analysis: {e}")
            return False
    
    def analyze_all_time_high(self):
        """ATH analysis"""
        try:
            close_prices = self.data['Close']
            all_time_high = float(close_prices.max())
            current_price = float(close_prices.iloc[-1])
            
            discount_percentage = ((all_time_high - current_price) / all_time_high) * 100
            
            if discount_percentage < 0:
                discount_percentage = 0
            
            if discount_percentage < 10:
                is_good = False
                recommendation = "Stock near all-time high - may have limited upside"
            elif discount_percentage <= 20:
                is_good = None
                recommendation = "Moderate discount - reasonable valuation"
            elif discount_percentage <= 40:
                is_good = True
                recommendation = "Good discount - attractive entry point"
            else:
                is_good = True
                recommendation = "Excellent discount - potential opportunity"
            
            self.analysis_results['ath_analysis'] = {
                'all_time_high': all_time_high,
                'current_price': current_price,
                'discount_percentage': discount_percentage,
                'recommendation': recommendation,
                'is_good': is_good
            }
            
            print(f"ATH Analysis: {discount_percentage:.2f}% discount from Rs.{all_time_high:.2f}")
            return True
        except Exception as e:
            print(f"Error in ATH analysis: {e}")
            return False
    
    def analyze_rsi(self):
        """RSI analysis with reasoning"""
        try:
            close_prices = self.data['Close']
            self.rsi = calculate_rsi(close_prices, period=14)
            
            if self.rsi is None or self.rsi.empty:
                raise ValueError("RSI calculation failed")
            
            final_rsi = float(self.rsi.iloc[-1])
            
            if pd.isna(final_rsi):
                raise ValueError("RSI is NaN")
            
            if final_rsi <= 20:
                is_good = True
                recommendation = "Extremely Oversold"
                reasoning = "RSI below 20 indicates extreme oversold condition - potentially strong recovery signal."
            elif final_rsi <= 30:
                is_good = True
                recommendation = "Very Oversold - Strong Buy Signal"
                reasoning = "RSI below 30 indicates oversold condition - stock likely to recover."
            elif final_rsi <= 45:
                is_good = True
                recommendation = "Oversold - Buy Signal"
                reasoning = "RSI in 30-45 range indicates downward pressure exhaustion - good accumulation zone."
            elif final_rsi <= 55:
                is_good = None
                recommendation = "Neutral Zone"
                reasoning = "RSI 45-55 indicates no extreme momentum - neither overbought nor oversold."
            elif final_rsi <= 70:
                is_good = False
                recommendation = "Overbought - Caution Zone"
                reasoning = "RSI above 55 indicates upward momentum exhaustion - potential pullback ahead."
            else:
                is_good = False
                recommendation = "Extremely Overbought - Sell Signal"
                reasoning = "RSI above 70 indicates extremely overbought condition with strong probability of reversal."
            
            self.analysis_results['rsi_analysis'] = {
                'rsi_value': final_rsi,
                'recommendation': recommendation,
                'reasoning': reasoning,
                'is_good': is_good
            }
            
            print(f"RSI Analysis: {final_rsi:.2f} - {recommendation}")
            return True
        except Exception as e:
            print(f"Error in RSI analysis: {e}")
            return False
    
    def analyze_pe_ratio(self):
        """P/E ratio analysis with reasoning"""
        try:
            pe_ratio = self.stock_info.get("trailingPE", 0)
            
            if pe_ratio is None or pd.isna(pe_ratio) or pe_ratio <= 0:
                pe_ratio = 0
                recommendation = "P/E Ratio not available"
                reasoning = "Cannot determine valuation - data not available for this stock currently"
                is_good = None
            elif pe_ratio < 10:
                is_good = True
                recommendation = "Severely Undervalued"
                reasoning = "P/E below 10 indicates exceptional valuation - stock trading significantly below earnings."
            elif pe_ratio < 15:
                is_good = True
                recommendation = "Undervalued - Buy"
                reasoning = "P/E 10-15 indicates good valuation - stock offers value compared to earnings."
            elif pe_ratio < 20:
                is_good = True
                recommendation = "Fair Valuation - Good Value"
                reasoning = "P/E 15-20 indicates fair valuation - reasonable price-to-earnings ratio."
            elif pe_ratio < 30:
                is_good = None
                recommendation = "Slightly Expensive"
                reasoning = "P/E 20-30 indicates moderate premium - normal for growing companies."
            elif pe_ratio < 40:
                is_good = False
                recommendation = "Expensive - Caution"
                reasoning = "P/E above 30 indicates significant premium - limited margin of safety."
            else:
                is_good = False
                recommendation = "Severely Overvalued"
                reasoning = "P/E above 40 indicates extreme premium - high risk of correction."
            
            self.analysis_results['pe_analysis'] = {
                'pe_ratio': float(pe_ratio) if pe_ratio else 0,
                'recommendation': recommendation,
                'reasoning': reasoning,
                'is_good': is_good
            }
            
            if pe_ratio and pe_ratio > 0:
                print(f"P/E Analysis: {pe_ratio:.2f} - {recommendation}")
            else:
                print(f"P/E Analysis: Not available")
            
            return True
        except Exception as e:
            print(f"Error in P/E analysis: {e}")
            return False
    
    def analyze_fundamentals(self):
        """Quarterly fundamentals with revenue, operating profit, and net profit"""
        try:
            ticker = yf.Ticker(self.stock_name)
            income_stmt = ticker.quarterly_financials
            
            if income_stmt is None or income_stmt.empty:
                print("No quarterly data available")
                self.analysis_results['fundamentals_analysis'] = {
                    'recommendation': "Data not available",
                    'reasoning': "Quarterly financial data not accessible for analysis",
                    'is_good': None,
                    'dates': [],
                    'revenue_list': [],
                    'operating_profit_list': [],
                    'net_profit_list': []
                }
                return True
            
            dates = income_stmt.columns[:4]
            revenue_list = []
            operating_profit_list = []
            net_profit_list = []
            
            for date in dates:
                try:
                    rev = income_stmt.loc['Total Revenue', date] if 'Total Revenue' in income_stmt.index else 0
                    op_profit = income_stmt.loc['Operating Income', date] if 'Operating Income' in income_stmt.index else 0
                    net_profit = income_stmt.loc['Net Income', date] if 'Net Income' in income_stmt.index else 0
                    
                    rev = float(rev) if not isinstance(rev, (int, float)) else rev
                    op_profit = float(op_profit) if not isinstance(op_profit, (int, float)) else op_profit
                    net_profit = float(net_profit) if not isinstance(net_profit, (int, float)) else net_profit
                    
                    revenue_list.append(rev if rev else 0)
                    operating_profit_list.append(op_profit if op_profit else 0)
                    net_profit_list.append(net_profit if net_profit else 0)
                except Exception as inner_e:
                    print(f"Error processing date {date}: {inner_e}")
                    continue
            
            if len(revenue_list) >= 2:
                revenue_trend = revenue_list[0] > revenue_list[1]
                op_profit_trend = operating_profit_list[0] > operating_profit_list[1] if len(operating_profit_list) > 1 else False
                net_profit_trend = net_profit_list[0] > net_profit_list[1] if len(net_profit_list) > 1 else False
                
                revenue_growth = ((revenue_list[0] - revenue_list[1]) / abs(revenue_list[1])) * 100 if revenue_list[1] != 0 else 0
                
                if revenue_trend and net_profit_trend and revenue_growth > 5:
                    is_good = True
                    recommendation = "Strong Fundamentals"
                    reasoning = f"Revenue up {revenue_growth:.1f}% and profit growing - company expanding profitably."
                elif revenue_trend and net_profit_trend:
                    is_good = True
                    recommendation = "Improving Fundamentals"
                    reasoning = "Both revenue and net profit increasing - positive business momentum."
                elif revenue_trend:
                    is_good = None
                    recommendation = "Mixed Signals"
                    reasoning = "Revenue growing but net profit concerns - topline expansion not translating to bottom line."
                else:
                    is_good = False
                    recommendation = "Declining Fundamentals"
                    reasoning = "Revenue declining - business facing headwinds."
            else:
                is_good = None
                recommendation = "Insufficient Data"
                reasoning = "Limited historical quarterly data available."
            
            formatted_dates = [d.strftime('%b %Y') for d in dates]
            
            self.analysis_results['fundamentals_analysis'] = {
                'recommendation': recommendation,
                'reasoning': reasoning,
                'is_good': is_good,
                'dates': formatted_dates,
                'revenue_list': revenue_list,
                'operating_profit_list': operating_profit_list,
                'net_profit_list': net_profit_list
            }
            
            print(f"Fundamentals: {recommendation}")
            return True
        except Exception as e:
            print(f"Error in fundamentals: {e}")
            self.analysis_results['fundamentals_analysis'] = {
                'recommendation': "Error in analysis",
                'reasoning': str(e),
                'is_good': None,
                'dates': [],
                'revenue_list': [],
                'operating_profit_list': [],
                'net_profit_list': []
            }
            return False
    
    def generate_verdict(self):
        """Generate comprehensive investment verdict"""
        try:
            signals = []
            signal_count = 0
            positive_count = 0
            
            price_analysis = self.analysis_results.get('price_analysis', {})
            if price_analysis.get('price_trend_good') is True:
                signals.append(f"Price Trend: {price_analysis.get('price_trend')} with bullish MA alignment")
                positive_count += 1
            elif price_analysis.get('price_trend_good') is False:
                signals.append(f"Price Trend: {price_analysis.get('price_trend')} - bearish momentum")
            else:
                signals.append(f"Price Trend: {price_analysis.get('price_trend')} - neutral positioning")
            signal_count += 1
            
            ath_analysis = self.analysis_results.get('ath_analysis', {})
            if ath_analysis.get('is_good') is True:
                signals.append(f"Valuation: {ath_analysis.get('discount_percentage', 0):.1f}% discount from ATH")
                positive_count += 1
            elif ath_analysis.get('is_good') is False:
                signals.append("Valuation: Limited upside - stock near highs")
            else:
                signals.append("Valuation: Moderate discount available")
            signal_count += 1
            
            rsi_analysis = self.analysis_results.get('rsi_analysis', {})
            if rsi_analysis.get('is_good') is True:
                signals.append(f"Momentum: {rsi_analysis.get('recommendation')} - oversold condition")
                positive_count += 1
            elif rsi_analysis.get('is_good') is False:
                signals.append(f"Momentum: {rsi_analysis.get('recommendation')} - overbought condition")
            else:
                signals.append("Momentum: Neutral - balanced buying and selling pressure")
            signal_count += 1
            
            pe_analysis = self.analysis_results.get('pe_analysis', {})
            if pe_analysis.get('is_good') is True:
                signals.append(f"Valuation Metric: {pe_analysis.get('recommendation')} - attractive P/E")
                positive_count += 1
            elif pe_analysis.get('is_good') is False:
                signals.append(f"Valuation Metric: {pe_analysis.get('recommendation')} - expensive valuation")
            else:
                signals.append("Valuation Metric: Neutral P/E ratio")
            signal_count += 1
            
            fund_analysis = self.analysis_results.get('fundamentals_analysis', {})
            if fund_analysis.get('is_good') is True:
                signals.append(f"Fundamentals: {fund_analysis.get('recommendation')} - strong business metrics")
                positive_count += 1
            elif fund_analysis.get('is_good') is False:
                signals.append(f"Fundamentals: {fund_analysis.get('recommendation')} - weak business performance")
            else:
                signals.append("Fundamentals: Mixed or insufficient data")
            signal_count += 1
            
            confidence = int((positive_count / signal_count) * 100) if signal_count > 0 else 0
            
            if positive_count >= 4:
                verdict = "STRONG BUY"
                strategy = "Excellent for Long-term Holding"
                verdict_strength = "Very High Confidence"
            elif positive_count == 3:
                verdict = "BUY"
                strategy = "Good for Long-term Investment"
                verdict_strength = "High Confidence"
            elif positive_count == 2:
                verdict = "ACCUMULATE"
                strategy = "Suitable for Swing Trading (2-3 months)"
                verdict_strength = "Moderate Confidence"
            elif positive_count == 1:
                verdict = "HOLD"
                strategy = "Wait for Better Signals"
                verdict_strength = "Low Confidence"
            else:
                verdict = "AVOID"
                strategy = "Do Not Buy at Current Levels"
                verdict_strength = "Avoid Investment"
            
            self.analysis_results['verdict'] = {
                'verdict': verdict,
                'strategy': strategy,
                'confidence': confidence,
                'signals': signals,
                'strength': verdict_strength,
                'positive_count': positive_count,
                'total_signals': signal_count
            }
            
            print(f"\nFinal Verdict: {verdict} ({confidence}% confidence)")
            print(f"Strategy: {strategy}")
            
            return True
        except Exception as e:
            print(f"Error in verdict generation: {e}")
            return False
    
    def create_charts(self):
        """Create professional charts"""
        try:
            print("Creating professional charts...")
            
            # RSI Chart - Save to /tmp
            if self.rsi is not None and not self.rsi.empty:
                fig, ax = plt.subplots(figsize=(14, 7))
                fig.patch.set_facecolor('white')
                ax.set_facecolor('#F8F9F9')
                
                ax.plot(self.rsi.index, self.rsi.values, label='RSI (14)', color='#1F3864', linewidth=2.5)
                
                ax.axhline(70, linestyle='--', alpha=0.6, color='#E74C3C', label='Overbought (70)', linewidth=1.5)
                ax.axhline(30, linestyle='--', alpha=0.6, color='#27AE60', label='Oversold (30)', linewidth=1.5)
                
                ax.fill_between(self.rsi.index, 70, 100, alpha=0.08, color='#E74C3C')
                ax.fill_between(self.rsi.index, 0, 30, alpha=0.08, color='#27AE60')
                
                ax.set_ylim(0, 100)
                ax.set_title('Relative Strength Index (RSI) - 14 Period', fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Date', fontsize=12, fontweight='bold')
                ax.set_ylabel('RSI Value', fontsize=12, fontweight='bold')
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3, linestyle=':')
                
                final_rsi = float(self.rsi.iloc[-1])
                final_date = self.rsi.index[-1]
                color = '#27AE60' if final_rsi < 30 else '#E74C3C' if final_rsi > 70 else '#95A5A6'
                
                ax.scatter([final_date], [final_rsi], color=color, s=200, zorder=5, edgecolor='black', linewidth=2)
                ax.annotate(f'Current RSI: {final_rsi:.1f}', 
                           xy=(final_date, final_rsi),
                           xytext=(30, 30), 
                           textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.8', facecolor=color, alpha=0.8, edgecolor='black', linewidth=1),
                           arrowprops=dict(arrowstyle='->', lw=2, color='black'),
                           fontsize=11, fontweight='bold', color='white')
                
                plt.tight_layout()
                # SAVE TO /tmp INSTEAD OF CURRENT DIRECTORY
                rsi_chart_path = os.path.join(self.temp_dir, 'rsi_chart.png')
                plt.savefig(rsi_chart_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                print(f"✓ RSI Chart saved to {rsi_chart_path}")
            
            # Fundamentals Chart - Save to /tmp
            fund_data = self.analysis_results.get('fundamentals_analysis', {})
            if fund_data.get('revenue_list') and fund_data.get('dates') and len(fund_data['revenue_list']) > 0:
                revenue_list = fund_data['revenue_list']
                operating_profit_list = fund_data.get('operating_profit_list', [])
                net_profit_list = fund_data['net_profit_list']
                dates = fund_data['dates']
                
                fig, ax = plt.subplots(figsize=(14, 7))
                fig.patch.set_facecolor('white')
                ax.set_facecolor('#F8F9F9')
                
                x = list(range(len(dates)))
                width = 0.25
                
                revenue_crores = [float(r) / 1e7 if r and r > 0 else 0 for r in revenue_list]
                operating_profit_crores = [float(p) / 1e7 if p and p > 0 else 0 for p in operating_profit_list]
                net_profit_crores = [float(p) / 1e7 if p and p > 0 else 0 for p in net_profit_list]
                
                bars1 = ax.bar([i - width for i in x], revenue_crores, width, label='Revenue', color='#3498DB', alpha=0.9, edgecolor='black', linewidth=1.5)
                bars2 = ax.bar([i for i in x], operating_profit_crores, width, label='Operating Profit', color='#F39C12', alpha=0.9, edgecolor='black', linewidth=1.5)
                bars3 = ax.bar([i + width for i in x], net_profit_crores, width, label='Net Profit', color='#27AE60', alpha=0.9, edgecolor='black', linewidth=1.5)
                
                ax.set_title('Quarterly Financial Performance (₹ Crores)', fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Quarter', fontsize=12, fontweight='bold')
                ax.set_ylabel('Amount (₹ Crores)', fontsize=12, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(dates, fontsize=11, fontweight='bold')
                ax.legend(fontsize=11, loc='best')
                ax.grid(True, alpha=0.3, axis='y', linestyle=':')
                
                plt.tight_layout()
                # SAVE TO /tmp INSTEAD OF CURRENT DIRECTORY
                fund_chart_path = os.path.join(self.temp_dir, 'fundamentals_chart.png')
                plt.savefig(fund_chart_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                print(f"✓ Fundamentals Chart saved to {fund_chart_path}")
            
            print("All charts created successfully")
            return True
        except Exception as e:
            print(f"Error creating charts: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_professional_pdf(self):
        """Generate comprehensive professional PDF report"""
        try:
            print("Generating professional PDF report...")
            
            pdf = ProfessionalStockPDF()
            stock_ticker = self.stock_name.replace('.NS', '').replace('.BO', '')
            
            # PAGE 1: COVER & COMPANY OVERVIEW
            pdf.add_page()
            pdf.add_main_header(f"STOCK ANALYSIS REPORT", f"Ticker: {stock_ticker}")
            
            pdf.add_section_header("COMPANY OVERVIEW")
            company_details = self.analysis_results.get('company_details', {})
            
            pdf.add_info_pair("Ticker Symbol", stock_ticker)
            pdf.add_info_pair("Company Name", company_details.get('company_name', 'N/A'))
            pdf.add_info_pair("Sector", company_details.get('sector', 'N/A'))
            pdf.add_info_pair("Industry", company_details.get('industry', 'N/A'))
            
            market_cap = company_details.get('market_cap', 0)
            if market_cap:
                market_cap_crores = market_cap / 1e7
                pdf.add_info_pair("Market Cap", f"Rs. {market_cap_crores:,.0f} Cr")
            else:
                pdf.add_info_pair("Market Cap", "N/A")
            
            pdf.add_section_separator()
            
            pdf.add_section_header("KEY METRICS")
            
            book_value = company_details.get('book_value', 0)
            trailing_eps = company_details.get('trailing_eps', 0)
            forward_eps = company_details.get('forward_eps', 0)
            dividend_yield = company_details.get('dividend_yield', 0)
            
            if book_value:
                pdf.add_info_pair("Book Value/Share", f"Rs. {book_value:.2f}")
            if trailing_eps:
                pdf.add_info_pair("Trailing EPS", f"Rs. {trailing_eps:.2f}")
            if forward_eps:
                pdf.add_info_pair("Forward EPS", f"Rs. {forward_eps:.2f}")
            if dividend_yield and dividend_yield > 0:
                pdf.add_info_pair("Dividend Yield", f"{(dividend_yield * 100):.2f}%")
            
            average_volume = company_details.get('average_volume', 0)
            if average_volume:
                pdf.add_info_pair("Avg Volume", f"{average_volume:,.0f}")
            
            beta = company_details.get('beta', 0)
            if beta:
                pdf.add_info_pair("Beta", f"{beta:.2f}")
            
            pdf.add_section_separator()
            
            pdf.add_section_header("52-WEEK PERFORMANCE")
            
            fifty_two_week_high = company_details.get('fifty_two_week_high', 0)
            fifty_two_week_low = company_details.get('fifty_two_week_low', 0)
            
            if fifty_two_week_high:
                pdf.add_info_pair("52-Week High", f"Rs. {fifty_two_week_high:.2f}")
            if fifty_two_week_low:
                pdf.add_info_pair("52-Week Low", f"Rs. {fifty_two_week_low:.2f}")
            
            if fifty_two_week_high and fifty_two_week_low:
                range_pct = ((fifty_two_week_high - fifty_two_week_low) / fifty_two_week_low) * 100
                pdf.add_info_pair("Year Range %", f"{range_pct:.2f}%")
            
            price_data = self.analysis_results.get('price_analysis', {})
            current_price = price_data.get('current_price', 0)
            if current_price:
                pdf.add_info_pair("Current Price", f"Rs. {current_price:.2f}")
            
            distance_from_high = price_data.get('distance_from_high', 0)
            distance_from_low = price_data.get('distance_from_low', 0)
            if distance_from_high:
                pdf.add_info_pair("From 52W High", f"{distance_from_high:.2f}%")
            if distance_from_low:
                pdf.add_info_pair("From 52W Low", f"{distance_from_low:.2f}%")
            
            pdf.add_section_separator()
            
            # PAGE 2: PRICE ANALYSIS
            pdf.add_page()
            pdf.add_main_header("PRICE ANALYSIS")
            
            pdf.add_section_header("CURRENT PRICE INFORMATION")
            
            current_price = price_data.get('current_price', 0)
            price_change = price_data.get('price_change', 0)
            price_change_pct = price_data.get('price_change_pct', 0)
            
            pdf.add_info_pair("Current Price", f"Rs. {current_price:.2f}")
            
            color = "good" if price_change > 0 else "bad"
            price_str = f"Rs. {price_change:+.2f} ({price_change_pct:+.2f}%)"
            status_text = f"Gain: {price_str}" if price_change > 0 else f"Loss: {price_str}"
            
            price_reasoning = "Strong positive movement in recent trading session indicating bullish investor sentiment" if price_change > 0 else "Weakness in stock price reflecting bearish market sentiment and selling pressure"
            pdf.add_colored_box("Price Movement", status_text, color, price_reasoning)
            
            pdf.add_section_separator()
            
            pdf.add_section_header("PRICE TREND & MOVING AVERAGES")
            
            price_trend = price_data.get('price_trend', 'N/A')
            trend_good = price_data.get('price_trend_good')
            ma_50 = price_data.get('ma_50', 0)
            ma_200 = price_data.get('ma_200', 0)
            
            pdf.add_info_pair("50-Day MA", f"Rs. {ma_50:.2f}")
            pdf.add_info_pair("200-Day MA", f"Rs. {ma_200:.2f}")
            
            trend_color = "good" if trend_good is True else "bad" if trend_good is False else "neutral"
            trend_reason = "Stock trading above both key moving averages - strong uptrend with sustained bullish momentum" if trend_good is True else "Stock below key moving averages - weak downtrend with bearish momentum" if trend_good is False else "Stock near moving averages - mixed signals requiring clarity"
            
            pdf.add_colored_box("Price Trend", price_trend, trend_color, trend_reason)
            
            pdf.add_section_separator()
            
            pdf.add_section_header("VOLUME ANALYSIS")
            
            avg_volume = price_data.get('avg_volume', 0)
            current_volume = price_data.get('current_volume', 0)
            volume_signal = price_data.get('volume_signal', 'N/A')
            
            pdf.add_info_pair("30-Day Avg Volume", f"{avg_volume:,.0f} shares")
            pdf.add_info_pair("Current Volume", f"{current_volume:,.0f} shares")
            
            vol_color = "good" if "above" in volume_signal.lower() else "bad"
            vol_reason = "Higher than average trading volume confirms strength of price movement" if "above" in volume_signal.lower() else "Lower than average volume suggests weak conviction"
            pdf.add_colored_box("Volume Signal", volume_signal, vol_color, vol_reason)
            
            # PAGE 3: RSI ANALYSIS
            pdf.add_page()
            pdf.add_main_header("RSI ANALYSIS")
            
            pdf.add_section_header("RELATIVE STRENGTH INDEX (RSI) - 14 PERIOD")
            
            rsi_data = self.analysis_results.get('rsi_analysis', {})
            rsi_value = rsi_data.get('rsi_value', 0)
            rsi_recommendation = rsi_data.get('recommendation', 'N/A')
            rsi_reasoning = rsi_data.get('reasoning', '')
            rsi_good = rsi_data.get('is_good')
            
            pdf.add_info_pair("RSI (14)", f"{rsi_value:.2f}")
            
            rsi_color = "good" if rsi_good is True else "bad" if rsi_good is False else "neutral"
            pdf.add_colored_box("RSI Signal", rsi_recommendation, rsi_color, rsi_reasoning)
            
            pdf.add_section_separator()
            
            pdf.ln(5)
            
            # Use /tmp path for RSI chart
            rsi_chart_path = os.path.join(self.temp_dir, 'rsi_chart.png')
            if os.path.exists(rsi_chart_path):
                pdf.check_page_space(100)
                pdf.image(rsi_chart_path, x=15, y=pdf.get_y(), w=180)
            
            # PAGE 4: VALUATION ANALYSIS
            pdf.add_page()
            pdf.add_main_header("VALUATION ANALYSIS")
            
            pdf.add_section_header("PRICE-TO-EARNINGS (P/E) VALUATION")
            
            pe_data = self.analysis_results.get('pe_analysis', {})
            pe_ratio = pe_data.get('pe_ratio', 0)
            pe_recommendation = pe_data.get('recommendation', 'N/A')
            pe_reasoning = pe_data.get('reasoning', '')
            pe_good = pe_data.get('is_good')
            
            if pe_ratio and pe_ratio > 0:
                pdf.add_info_pair("P/E Ratio", f"{pe_ratio:.2f}x")
                pe_color = "good" if pe_good is True else "bad" if pe_good is False else "neutral"
                pdf.add_colored_box("Valuation Status", pe_recommendation, pe_color, pe_reasoning)
            else:
                pdf.set_font("Arial", "", 9)
                pdf.set_text_color(*pdf.TEXT_LIGHT)
                pdf.multi_cell(0, 5, "P/E ratio data not available for this stock", 0, 'L')
            
            pdf.add_section_separator()
            
            pdf.add_section_header("QUARTERLY FUNDAMENTALS ANALYSIS")
            
            fund_data = self.analysis_results.get('fundamentals_analysis', {})
            fund_recommendation = fund_data.get('recommendation', 'N/A')
            fund_reasoning = fund_data.get('reasoning', '')
            fund_good = fund_data.get('is_good')
            
            fund_color = "good" if fund_good is True else "bad" if fund_good is False else "neutral"
            pdf.add_colored_box("Fundamental Health", fund_recommendation, fund_color, fund_reasoning)
            
            pdf.add_section_separator()
            
            pdf.ln(5)
            
            # Use /tmp path for fundamentals chart
            fund_chart_path = os.path.join(self.temp_dir, 'fundamentals_chart.png')
            if os.path.exists(fund_chart_path):
                pdf.check_page_space(100)
                pdf.image(fund_chart_path, x=15, y=pdf.get_y(), w=180)
            
            # PAGE 5: FINAL VERDICT
            pdf.add_page()
            pdf.add_main_header("INVESTMENT VERDICT")
            
            verdict_data = self.analysis_results.get('verdict', {})
            verdict = verdict_data.get('verdict', 'HOLD')
            strategy = verdict_data.get('strategy', '')
            confidence = verdict_data.get('confidence', 0)
            signals = verdict_data.get('signals', [])
            
            pdf.ln(5)
            pdf.set_font("Arial", "B", 20)
            verdict_color = "good" if "BUY" in verdict else "bad" if "AVOID" in verdict else "neutral"
            
            if verdict_color == "good":
                pdf.set_fill_color(*pdf.GOOD_COLOR)
            elif verdict_color == "bad":
                pdf.set_fill_color(*pdf.BAD_COLOR)
            else:
                pdf.set_fill_color(*pdf.NEUTRAL_COLOR)
            
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 20, f"{verdict}", 0, 1, "C", True)
            
            pdf.set_text_color(*pdf.TEXT_DARK)
            
            pdf.add_section_separator()
            
            pdf.add_section_header("RECOMMENDED STRATEGY")
            pdf.set_font("Arial", "", 11)
            pdf.set_text_color(*pdf.TEXT_DARK)
            pdf.multi_cell(0, 6, f"{strategy}", 0, 'L')
            
            pdf.add_section_separator()
            
            pdf.add_section_header("CONFIDENCE SCORE ANALYSIS")
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, f"Confidence Score: {confidence}%", 0, 1)
            
            bar_width = 170
            filled_width = (confidence / 100) * bar_width
            
            pdf.set_draw_color(*pdf.TEXT_LIGHT)
            pdf.rect(15, pdf.get_y(), bar_width, 8)
            
            if confidence >= 75:
                pdf.set_fill_color(*pdf.GOOD_COLOR)
            elif confidence >= 50:
                pdf.set_fill_color(*pdf.ACCENT_COLOR)
            else:
                pdf.set_fill_color(*pdf.BAD_COLOR)
            
            pdf.rect(15, pdf.get_y(), filled_width, 8, 'F')
            pdf.ln(12)
            
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(*pdf.TEXT_LIGHT)
            confidence_text = f"Based on {verdict_data.get('positive_count', 0)} out of {verdict_data.get('total_signals', 0)} positive signals"
            pdf.multi_cell(0, 5, confidence_text, 0, 'L')
            
            pdf.add_section_separator()
            
            pdf.add_section_header("ANALYSIS SIGNALS SUMMARY")
            
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(*pdf.TEXT_DARK)
            
            for idx, signal in enumerate(signals, 1):
                pdf.set_x(20)
                pdf.set_font("Arial", "B", 9)
                pdf.cell(5, 6, f"{idx}.", 0, 0)
                pdf.set_font("Arial", "", 9)
                pdf.multi_cell(170, 6, f" {signal}", 0, 'L')
            
            pdf.ln(4)
            
            pdf.add_section_separator()
            
            pdf.check_page_space(80)
            
            # Disclaimer
            pdf.set_fill_color(255, 235, 59)
            pdf.set_draw_color(200, 180, 0)
            pdf.set_line_width(1.5)
            pdf.rect(10, pdf.get_y(), 190, 1, 'D')
            
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(255, 235, 59)
            pdf.cell(190, 8, "IMPORTANT DISCLAIMER AND CAUTION", 0, 1, "C", True)
            
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(*pdf.TEXT_DARK)
            
            caution_points = [
                "This analysis is for educational and informational purposes only, not financial advice.",
                "Stock market investments carry substantial risk; you may lose your entire investment.",
                "Past performance does not guarantee or predict future results.",
                "Do not invest money you cannot afford to lose completely.",
                "Market conditions change rapidly; always verify information from multiple sources.",
                "Diversify your investments to reduce concentration risk.",
                "Consult qualified financial advisors before making investment decisions.",
                "Technical and fundamental analysis are tools, not guarantees of future performance.",
                "Regulatory changes and geopolitical events can significantly impact stock prices.",
                "This report is general analysis; personal circumstances vary."
            ]
            
            for idx, point in enumerate(caution_points, 1):
                pdf.set_x(15)
                pdf.multi_cell(0, 4.2, f"{idx}. {point}", 0, 'L')
            
            pdf.ln(2)
            pdf.rect(10, pdf.get_y(), 190, 1, 'D')
            
            pdf.set_y(270)
            pdf.set_font("Arial", "I", 8)
            pdf.set_text_color(*pdf.TEXT_LIGHT)
            pdf.cell(0, 5, f"Report Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", 0, 1, "C")
            
            # Save PDF to /tmp directory - CRITICAL FIX
            pdf_filename = os.path.join(self.temp_dir, 
                                       f"Stock_Analysis_{stock_ticker}_{datetime.now().strftime('%d%m%Y')}.pdf")
            pdf.output(pdf_filename)
            print(f"✓ PDF Report generated: {pdf_filename}")
            
            return pdf_filename
        except Exception as e:
            print(f"PDF generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def cleanup_files(self):
        """Clean up temporary chart files"""
        try:
            chart_files = [
                os.path.join(self.temp_dir, 'rsi_chart.png'),
                os.path.join(self.temp_dir, 'fundamentals_chart.png')
            ]
            
            for file in chart_files:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"✓ Cleaned up: {file}")
            
            print("Temporary files cleaned up")
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def run_complete_analysis(self):
        """Execute full analysis pipeline"""
        print("\n" + "="*70)
        print("PROFESSIONAL STOCK ANALYSIS TOOL".center(70))
        print("="*70 + "\n")
        
        if not self.fetch_data():
            print("ERROR: Failed to fetch stock data")
            return None
        
        self.fetch_stock_info()
        
        print("\nRunning comprehensive analysis...")
        self.get_company_details()
        self.analyze_price_data()
        self.analyze_all_time_high()
        self.analyze_rsi()
        self.analyze_pe_ratio()
        self.analyze_fundamentals()
        self.generate_verdict()
        
        self.create_charts()
        
        pdf_file = self.generate_professional_pdf()
        
        self.cleanup_files()
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE".center(70))
        print("="*70 + "\n")
        
        return pdf_file