# ====================================================================
# 📄 app/main.py - Aplikasi Prediksi Kebangkrutan (FIXED VERSION)
# ====================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import requests
import time
import warnings
from datetime import datetime
from typing import Dict, Tuple, Optional, Any

warnings.filterwarnings('ignore')

# ====================================================================
# KONFIGURASI HALAMAN
# ====================================================================
st.set_page_config(
    page_title="Bankruptcy Prediction App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# CSS STYLING
# ====================================================================
def load_css():
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 5px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .risk-high {
            border-left-color: #e74c3c !important;
            background: linear-gradient(135deg, #fdf2f2 0%, #fce4ec 100%) !important;
        }
        
        .risk-medium {
            border-left-color: #f39c12 !important;
            background: linear-gradient(135deg, #fef9e7 0%, #fff3cd 100%) !important;
        }
        
        .risk-low {
            border-left-color: #27ae60 !important;
            background: linear-gradient(135deg, #eafaf1 0%, #d4edda 100%) !important;
        }
        
        .stSelectbox > div > div {
            background-color: #f8f9fa;
        }
        
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .info-box {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #17a2b8;
            margin: 1rem 0;
        }
        
        .success-box {
            background: #d4edda;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            margin: 1rem 0;
        }
        
        .warning-box {
            background: #fff3cd;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 1rem 0;
        }
        
        .error-box {
            background: #f8d7da;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #dc3545;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

# ====================================================================
# CONSTANTS
# ====================================================================
BANKRUPT_COMPANIES = [
    'MYRX.JK', 'KPAS.JK', 'FORZ.JK', 'COWL.JK', 'KPAL.JK', 
    'PRAS.JK', 'NIPS.JK', 'BEEF.JK', 'MAMI.JK', 'TOYS.JK',
    'SBAT.JK', 'WMPP.JK', 'ETWA.JK', 'HOTL.JK', 'RICY.JK',
    'TDPM.JK', 'KRAH.JK', 'SRIL.JK'
]

POPULAR_TICKERS = [
    "BBRI.JK", "BMRI.JK", "BBCA.JK", "TLKM.JK", "UNVR.JK",
    "ASII.JK", "GGRM.JK", "KLBF.JK", "ICBP.JK", "SMGR.JK"
]

RISK_COLORS = {
    'Tinggi': '#e74c3c',
    'Sedang': '#f39c12',
    'Rendah': '#27ae60'
}

RISK_EMOJIS = {
    'Tinggi': '🔴',
    'Sedang': '🟡',
    'Rendah': '🟢'
}

# Define financial field names that should be converted to float
NUMERIC_FIELDS = {
    'current_assets', 'current_liabilities', 'total_assets', 'total_liabilities',
    'total_revenue', 'ebit', 'net_income', 'retained_earnings', 'market_cap',
    'total_equity', 'current_price', 'book_value', 'shares_outstanding',
    'ebitda', 'profit_margin'
}

# ====================================================================
# DATA PROVIDER CLASS
# ====================================================================
class DataProvider:
    """Kelas untuk mengambil data dari berbagai sumber"""
    
    @staticmethod
    def safe_float(value, default=0.0):
        """Safely convert value to float"""
        try:
            if value and value != 'None' and value != '-' and str(value).strip() != '':
                # Remove any commas or other formatting
                clean_value = str(value).replace(',', '').replace(' ', '')
                return float(clean_value)
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not convert '{value}' to float: {e}")
        return default
    
    @staticmethod
    def get_yfinance_data(ticker: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Mengambil data dari Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if ticker is valid
            if not info or info.get('regularMarketPrice') is None:
                return None, f"Ticker {ticker} tidak ditemukan atau tidak valid"
            
            # Get financial statements
            try:
                financials = stock.financials
                balance_sheet = stock.balance_sheet
                
                if balance_sheet.empty or financials.empty:
                    return None, "Data laporan keuangan tidak tersedia"
                
            except Exception as e:
                return None, f"Error mengambil laporan keuangan: {str(e)}"
            
            # Extract financial data
            financial_data = DataProvider._extract_yfinance_data(balance_sheet, financials, info)
            
            if not financial_data.get('total_assets') or financial_data['total_assets'] <= 0:
                return None, "Data total assets tidak valid atau tidak tersedia"
            
            return financial_data, None
            
        except Exception as e:
            return None, f"Error YFinance: {str(e)}"
    
    @staticmethod
    def _extract_yfinance_data(balance_sheet, financials, info):
        """Extract dan clean data dari YFinance"""
        financial_data = {}
        
        # Balance Sheet extraction dengan fallback
        try:
            # Total Assets
            total_assets_keys = ['Total Assets', 'TotalAssets']
            financial_data['total_assets'] = DataProvider._safe_extract(balance_sheet, total_assets_keys)
            
            # Current Assets
            current_assets_keys = ['Current Assets', 'CurrentAssets']
            financial_data['current_assets'] = DataProvider._safe_extract(balance_sheet, current_assets_keys)
            
            # Current Liabilities
            current_liab_keys = ['Current Liabilities', 'CurrentLiabilities']
            financial_data['current_liabilities'] = DataProvider._safe_extract(balance_sheet, current_liab_keys)
            
            # Total Liabilities
            total_liab_keys = [
                'Total Liabilities Net Minority Interest', 
                'Total Liabilities', 
                'TotalLiabilities'
            ]
            financial_data['total_liabilities'] = DataProvider._safe_extract(balance_sheet, total_liab_keys)
            
            # Retained Earnings
            retained_keys = ['Retained Earnings', 'RetainedEarnings']
            financial_data['retained_earnings'] = DataProvider._safe_extract(balance_sheet, retained_keys)
            
            # Total Equity
            equity_keys = [
                'Total Equity Gross Minority Interest',
                'Stockholder Equity',
                'TotalEquity'
            ]
            financial_data['total_equity'] = DataProvider._safe_extract(balance_sheet, equity_keys)
            
        except Exception as e:
            st.warning(f"Beberapa data balance sheet tidak tersedia: {str(e)}")
        
        # Income Statement extraction
        try:
            # Revenue
            revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales']
            financial_data['total_revenue'] = DataProvider._safe_extract(financials, revenue_keys)
            
            # EBIT
            ebit_keys = ['EBIT', 'Operating Income', 'OperatingIncome']
            financial_data['ebit'] = DataProvider._safe_extract(financials, ebit_keys)
            
            # Net Income
            net_income_keys = ['Net Income', 'NetIncome']
            financial_data['net_income'] = DataProvider._safe_extract(financials, net_income_keys)
            
        except Exception as e:
            st.warning(f"Beberapa data income statement tidak tersedia: {str(e)}")
        
        # Company information (keep as strings)
        financial_data['company_name'] = info.get('longName', info.get('shortName', 'Unknown'))
        financial_data['sector'] = info.get('sector', 'N/A')
        financial_data['industry'] = info.get('industry', 'N/A')
        financial_data['country'] = info.get('country', 'N/A')
        
        # Numeric company info
        financial_data['market_cap'] = DataProvider.safe_float(info.get('marketCap', 0))
        financial_data['current_price'] = DataProvider.safe_float(info.get('currentPrice', 0))
        
        # Calculate missing values
        if not financial_data.get('total_equity') and financial_data.get('total_assets') and financial_data.get('total_liabilities'):
            financial_data['total_equity'] = financial_data['total_assets'] - financial_data['total_liabilities']
        
        # Estimate EBIT if missing
        if not financial_data.get('ebit') and financial_data.get('net_income'):
            financial_data['ebit'] = financial_data['net_income'] * 1.2
        
        return financial_data
    
    @staticmethod
    def _safe_extract(dataframe, possible_keys, default=0):
        """Safely extract value dengan multiple possible keys"""
        if dataframe.empty:
            return default
        
        for key in possible_keys:
            if key in dataframe.index:
                try:
                    value = dataframe.loc[key].iloc[0]
                    if pd.notna(value) and value != 0:
                        return DataProvider.safe_float(value)
                except:
                    continue
        return default
    
    @staticmethod
    def get_alpha_vantage_data(ticker: str, api_key: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Mengambil data dari Alpha Vantage API"""
        if not api_key:
            return None, "API Key Alpha Vantage diperlukan"
        
        try:
            symbol = ticker.replace('.JK', '').replace('.', '-')
            
            # Rate limiting
            time.sleep(1)
            
            # Get company overview
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
            response = requests.get(overview_url, timeout=30)
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                return None, "Rate limit tercapai atau symbol tidak ditemukan"
            
            if not data or data == {}:
                return None, "Data tidak ditemukan untuk symbol ini"
            
            # Process Alpha Vantage data
            financial_data = {
                'company_name': data.get('Name', symbol),
                'sector': data.get('Sector', 'N/A'),
                'industry': data.get('Industry', 'N/A'),
                'market_cap': DataProvider.safe_float(data.get('MarketCapitalization', 0)),
                'total_revenue': DataProvider.safe_float(data.get('RevenueTTM', 0)),
                'ebitda': DataProvider.safe_float(data.get('EBITDA', 0)),
                'profit_margin': DataProvider.safe_float(data.get('ProfitMargin', 0)),
                'book_value': DataProvider.safe_float(data.get('BookValue', 0)),
                'shares_outstanding': DataProvider.safe_float(data.get('SharesOutstanding', 0))
            }
            
            # Calculate estimates
            financial_data['net_income'] = financial_data['total_revenue'] * financial_data['profit_margin']
            financial_data['ebit'] = financial_data['ebitda'] * 0.9  # Estimate
            financial_data['total_assets'] = financial_data['market_cap'] * 1.5  # Rough estimate
            financial_data['current_assets'] = financial_data['total_assets'] * 0.4
            financial_data['current_liabilities'] = financial_data['total_assets'] * 0.2
            financial_data['total_liabilities'] = financial_data['total_assets'] * 0.6
            financial_data['total_equity'] = financial_data['total_assets'] - financial_data['total_liabilities']
            financial_data['retained_earnings'] = financial_data['total_equity'] * 0.5
            
            return financial_data, None
            
        except Exception as e:
            return None, f"Error Alpha Vantage: {str(e)}"

# ====================================================================
# BANKRUPTCY PREDICTOR CLASS
# ====================================================================
class BankruptcyPredictor:
    """Kelas untuk prediksi kebangkrutan dengan berbagai model"""
    
    @staticmethod
    def validate_data(data: Dict) -> Tuple[bool, str]:
        """Validasi dan clean data finansial - FIXED VERSION"""
        try:
            # Make a copy to avoid modifying original data
            clean_data = data.copy()
            
            # Convert only numeric fields to float
            for key, value in clean_data.items():
                if key in NUMERIC_FIELDS:
                    if value is None:
                        clean_data[key] = 0.0
                    else:
                        clean_data[key] = DataProvider.safe_float(value, 0.0)
                # Keep non-numeric fields as they are
            
            # Update original data with cleaned numeric values
            for key in NUMERIC_FIELDS:
                if key in clean_data:
                    data[key] = clean_data[key]
            
            # Minimum requirements
            if data.get('total_assets', 0) <= 0:
                return False, "Total Assets harus lebih besar dari 0"
            
            # Auto-fix missing data
            if data.get('current_assets', 0) <= 0:
                data['current_assets'] = data['total_assets'] * 0.4
            
            if data.get('current_liabilities', 0) <= 0:
                data['current_liabilities'] = data['current_assets'] * 0.5
            
            if data.get('total_liabilities', 0) <= 0:
                data['total_liabilities'] = data['total_assets'] * 0.5
            
            if data.get('total_equity', 0) <= 0:
                data['total_equity'] = data['total_assets'] - data['total_liabilities']
            
            if data.get('ebit', 0) == 0 and data.get('net_income', 0) != 0:
                data['ebit'] = data['net_income'] * 1.2
            
            if data.get('market_cap', 0) <= 0:
                data['market_cap'] = data.get('total_equity', data['total_assets'] * 0.4)
            
            return True, "Data valid"
            
        except Exception as e:
            return False, f"Error validasi: {str(e)}"
    
    @staticmethod
    def altman_z_score(data: Dict) -> Dict:
        """Menghitung Altman Z-Score"""
        try:
            # Create a copy for validation
            data_copy = data.copy()
            is_valid, message = BankruptcyPredictor.validate_data(data_copy)
            if not is_valid:
                return {'error': message}
            
            # Use validated data
            data = data_copy
            
            # Components
            x1 = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            x2 = data.get('retained_earnings', 0) / data['total_assets']
            x3 = data.get('ebit', 0) / data['total_assets']
            x4 = data.get('market_cap', 0) / max(data.get('total_liabilities', 1), 1)
            x5 = data.get('total_revenue', 0) / data['total_assets']
            
            # Z-Score calculation
            z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
            
            # Interpretation
            if z_score < 1.8:
                status, risk, color = "Distress Zone", "Tinggi", "🔴"
                recommendation = "Hindari investasi - Risiko kebangkrutan tinggi"
            elif z_score < 3.0:
                status, risk, color = "Gray Zone", "Sedang", "🟡"
                recommendation = "Hati-hati - Perlu analisis lebih dalam"
            else:
                status, risk, color = "Safe Zone", "Rendah", "🟢"
                recommendation = "Relatif aman - Kondisi keuangan baik"
            
            return {
                'score': round(z_score, 3),
                'status': status,
                'risk': risk,
                'color': color,
                'recommendation': recommendation,
                'components': {
                    'X1 (Working Capital/TA)': round(x1, 3),
                    'X2 (Retained Earnings/TA)': round(x2, 3),
                    'X3 (EBIT/TA)': round(x3, 3),
                    'X4 (Market Cap/TL)': round(x4, 3),
                    'X5 (Sales/TA)': round(x5, 3)
                },
                'formula': 'Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5'
            }
        except Exception as e:
            return {'error': f"Error Altman: {str(e)}"}
    
    @staticmethod
    def springate_score(data: Dict) -> Dict:
        """Menghitung Springate S-Score"""
        try:
            data_copy = data.copy()
            is_valid, message = BankruptcyPredictor.validate_data(data_copy)
            if not is_valid:
                return {'error': message}
            
            data = data_copy
            
            # Components
            a = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            b = data.get('ebit', 0) / data['total_assets']
            c = data.get('ebit', 0) / max(data['current_liabilities'], 1)
            d = data.get('total_revenue', 0) / data['total_assets']
            
            # S-Score calculation
            s_score = 1.03*a + 3.07*b + 0.66*c + 0.4*d
            
            # Interpretation
            if s_score < 0.862:
                status, risk, color = "Bankrupt", "Tinggi", "🔴"
                recommendation = "Potensi kebangkrutan tinggi"
            else:
                status, risk, color = "Healthy", "Rendah", "🟢"
                recommendation = "Kondisi finansial sehat"
            
            return {
                'score': round(s_score, 3),
                'status': status,
                'risk': risk,
                'color': color,
                'recommendation': recommendation,
                'components': {
                    'A (WC/TA)': round(a, 3),
                    'B (EBIT/TA)': round(b, 3),
                    'C (EBIT/CL)': round(c, 3),
                    'D (Sales/TA)': round(d, 3)
                },
                'formula': 'S = 1.03×A + 3.07×B + 0.66×C + 0.4×D'
            }
        except Exception as e:
            return {'error': f"Error Springate: {str(e)}"}
    
    @staticmethod
    def zmijewski_score(data: Dict) -> Dict:
        """Menghitung Zmijewski X-Score"""
        try:
            data_copy = data.copy()
            is_valid, message = BankruptcyPredictor.validate_data(data_copy)
            if not is_valid:
                return {'error': message}
            
            data = data_copy
            
            # Components
            x1 = data.get('net_income', 0) / data['total_assets']
            x2 = data.get('total_liabilities', 0) / data['total_assets']
            x3 = data['current_assets'] / max(data['current_liabilities'], 1)
            
            # X-Score calculation
            x_score = -4.3 - 4.5*x1 + 5.7*x2 - 0.004*x3
            
            # Prevent overflow
            x_score = max(min(x_score, 50), -50)
            probability = np.exp(x_score) / (1 + np.exp(x_score))
            
            # Interpretation
            if probability > 0.5:
                status, risk, color = "Financial Distress", "Tinggi", "🔴"
                recommendation = "Probabilitas kebangkrutan tinggi"
            else:
                status, risk, color = "Healthy", "Rendah", "🟢"
                recommendation = "Probabilitas kebangkrutan rendah"
            
            return {
                'score': round(x_score, 3),
                'probability': round(probability * 100, 1),
                'status': status,
                'risk': risk,
                'color': color,
                'recommendation': recommendation,
                'components': {
                    'X1 (NI/TA)': round(x1, 3),
                    'X2 (TL/TA)': round(x2, 3),
                    'X3 (CA/CL)': round(x3, 3)
                },
                'formula': 'X = -4.3 - 4.5×X1 + 5.7×X2 - 0.004×X3'
            }
        except Exception as e:
            return {'error': f"Error Zmijewski: {str(e)}"}
    
    @staticmethod
    def grover_score(data: Dict) -> Dict:
        """Menghitung Grover G-Score"""
        try:
            data_copy = data.copy()
            is_valid, message = BankruptcyPredictor.validate_data(data_copy)
            if not is_valid:
                return {'error': message}
            
            data = data_copy
            
            # Components
            x1 = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            x2 = data.get('ebit', 0) / data['total_assets']
            x3 = data.get('net_income', 0) / data['total_assets']
            debt_ratio = data.get('total_liabilities', 0) / data['total_assets']
            
            # G-Score calculation
            g_score = 1.65*x1 + 3.404*x2 - 0.016*debt_ratio + 0.057
            
            # Interpretation
            if g_score <= -0.02:
                status, risk, color = "Bankrupt", "Tinggi", "🔴"
            elif g_score <= 0.01:
                status, risk, color = "Gray Zone", "Sedang", "🟡"
            else:
                status, risk, color = "Healthy", "Rendah", "🟢"
            
            return {
                'score': round(g_score, 3),
                'status': status,
                'risk': risk,
                'color': color,
                'components': {
                    'X1 (WC/TA)': round(x1, 3),
                    'X2 (EBIT/TA)': round(x2, 3),
                    'X3 (NI/TA)': round(x3, 3),
                    'Debt Ratio': round(debt_ratio, 3)
                },
                'formula': 'G = 1.65×X1 + 3.404×X2 - 0.016×DebtRatio + 0.057'
            }
        except Exception as e:
            return {'error': f"Error Grover: {str(e)}"}

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================
def format_currency(amount, currency="Rp"):
    """Format currency with appropriate suffix"""
    if amount == 0:
        return f"{currency} 0"
    
    if abs(amount) >= 1e12:
        return f"{currency} {amount/1e12:.1f}T"
    elif abs(amount) >= 1e9:
        return f"{currency} {amount/1e9:.1f}B"
    elif abs(amount) >= 1e6:
        return f"{currency} {amount/1e6:.1f}M"
    elif abs(amount) >= 1e3:
        return f"{currency} {amount/1e3:.1f}K"
    else:
        return f"{currency} {amount:,.0f}"

def display_company_info(financial_data: Dict, ticker: str = None, data_source: str = None):
    """Display company information in a nice layout"""
    st.subheader(f"🏢 {financial_data.get('company_name', 'Unknown Company')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💼 Sektor", financial_data.get('sector', 'N/A'))
        if ticker:
            st.metric("📊 Ticker", ticker)
    
    with col2:
        market_cap = financial_data.get('market_cap', 0)
        st.metric("💰 Market Cap", format_currency(market_cap))
        
        current_price = financial_data.get('current_price', 0)
        if current_price > 0:
            st.metric("💹 Harga Saham", format_currency(current_price))
    
    with col3:
        total_assets = financial_data.get('total_assets', 0)
        st.metric("🏛️ Total Assets", format_currency(total_assets))
        
        industry = financial_data.get('industry', 'N/A')
        if len(industry) > 20:
            industry = industry[:20] + "..."
        st.metric("🏭 Industri", industry)
    
    with col4:
        if data_source:
            st.metric("📡 Data Source", data_source.split(" ")[0])
        
        # Calculate and display current ratio
        current_assets = financial_data.get('current_assets', 0)
        current_liabilities = financial_data.get('current_liabilities', 1)
        current_ratio = current_assets / max(current_liabilities, 1)
        st.metric("📈 Current Ratio", f"{current_ratio:.2f}")

def display_model_result(model_name: str, result: Dict, col):
    """Display individual model result"""
    with col:
        risk_class = f"risk-{result['risk'].lower()}"
        
        st.markdown(f"""
        <div class="metric-card {risk_class}">
            <h4>{result['color']} {model_name}</h4>
            <h2 style="margin: 0.5rem 0;">{result['score']}</h2>
            <p><strong>Status:</strong> {result['status']}</p>
            <p><strong>Risiko:</strong> {result['risk']}</p>
            <p style="font-size: 0.9em; color: #666; margin-top: 1rem;">
                {result.get('recommendation', '')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'probability' in result:
            st.caption(f"Probabilitas: {result['probability']}%")
        
        # Component details
        with st.expander("📋 Detail Komponen"):
            st.code(result.get('formula', ''))
            for comp, value in result['components'].items():
                st.text(f"{comp}: {value}")

def create_risk_chart(results: Dict) -> go.Figure:
    """Create risk assessment chart"""
    models = list(results.keys())
    scores = [results[model]['score'] for model in models]
    risks = [results[model]['risk'] for model in models]
    
    colors = [RISK_COLORS[risk] for risk in risks]
    
    fig = go.Figure(data=[
        go.Bar(
            x=models,
            y=scores,
            marker_color=colors,
            text=scores,
            texttemplate='%{text:.2f}',
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title={
            'text': 'Perbandingan Score Model Prediksi Kebangkrutan',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Model",
        yaxis_title="Score",
        xaxis_tickangle=-45,
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def show_overall_assessment(risk_counts: pd.Series):
    """Show overall risk assessment and recommendations"""
    st.subheader("🎯 Kesimpulan & Rekomendasi")
    
    high_risk = risk_counts.get('Tinggi', 0)
    medium_risk = risk_counts.get('Sedang', 0)
    low_risk = risk_counts.get('Rendah', 0)
    
    if high_risk >= 3:
        st.markdown("""
        <div class="error-box">
            <h4>⚠️ PERINGATAN TINGGI</h4>
            <p>Mayoritas model menunjukkan risiko kebangkrutan tinggi!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **🚨 Rekomendasi:**
        - ❌ **Hindari investasi** pada saham ini
        - 🔍 **Due diligence mendalam** jika sudah berinvestasi
        - 📉 **Pertimbangkan untuk menjual** posisi yang ada
        - 💼 **Konsultasi dengan financial advisor**
        """)
        
    elif medium_risk >= 3 or (medium_risk >= 2 and high_risk >= 1):
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ PERHATIAN</h4>
            <p>Beberapa model menunjukkan risiko sedang hingga tinggi.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **⚠️ Rekomendasi:**
        - 👁️ **Monitor perkembangan** secara berkala
        - 📊 **Analisis lebih dalam** sebelum investasi tambahan
        - 🔄 **Diversifikasi portofolio** untuk mengurangi risiko
        - 📈 **Perhatikan tren** kinerja keuangan
        """)
        
    else:
        st.markdown("""
        <div class="success-box">
            <h4>✅ KONDISI BAIK</h4>
            <p>Mayoritas model menunjukkan kondisi finansial yang sehat.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **✅ Rekomendasi:**
        - 💹 **Dapat dipertimbangkan** untuk investasi
        - 📊 **Lakukan analisis fundamental** tambahan
        - 💰 **Pertimbangkan sebagai bagian** dari portofolio diversifikasi
        - 📈 **Monitor kinerja** secara berkala
        """)

def show_welcome_screen():
    """Show welcome screen and instructions"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Cara Menggunakan Aplikasi")
        st.markdown("""
        **1. Pilih Sumber Data:**
        - 🆓 **YFinance**: Gratis, tanpa API key, data real-time
        - 🔑 **Alpha Vantage**: Perlu API key gratis (500 requests/day)
        - ✏️ **Input Manual**: Masukkan data laporan keuangan sendiri
        
        **2. Masukkan Ticker atau Data:**
        - Format ticker saham Indonesia: `BBRI.JK`, `TLKM.JK`, dll.
        - Pilih dari daftar ticker populer atau emiten pailit
        - Atau input data keuangan secara manual
        
        **3. Analisis Otomatis:**
        - 4 Model prediksi kebangkrutan terintegrasi
        - Visualisasi interaktif dengan color-coding
        - Rekomendasi investasi berdasarkan hasil analisis
        """)
        
        st.subheader("📊 Model Prediksi yang Digunakan")
        models_info = {
            "🎯 Altman Z-Score": "Model klasik Edward Altman (1968) untuk prediksi kebangkrutan perusahaan manufaktur",
            "🌸 Springate S-Score": "Model dengan 4 rasio keuangan, sederhana namun akurat",
            "📈 Zmijewski X-Score": "Menggunakan pendekatan probabilistik untuk prediksi financial distress",
            "⭐ Grover G-Score": "Model yang dikembangkan khusus untuk sektor jasa dan perdagangan"
        }
        
        for model, desc in models_info.items():
            st.markdown(f"**{model}:** {desc}")
    
    with col2:
        st.subheader("🚨 Emiten Pailit (Referensi)")
        st.markdown("Daftar emiten yang pernah mengalami kepailitan di BEI:")
        
        # Display bankrupt companies in groups
        for i in range(0, len(BANKRUPT_COMPANIES), 3):
            companies_batch = BANKRUPT_COMPANIES[i:i+3]
            st.markdown("• " + " • ".join(companies_batch))
        
        st.markdown("""
        <div class="info-box">
            <strong>💡 Tips Testing:</strong><br>
            • Gunakan ticker di atas untuk melihat pola risiko tinggi<br>
            • Bandingkan dengan emiten sehat (BBRI.JK, UNVR.JK)<br>
            • Perhatikan konsistensi hasil antar model
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🔑 API Key Gratis")
        st.markdown("""
        **Alpha Vantage (Recommended):**
        - 🔗 [Daftar Gratis](https://www.alphavantage.co/support/#api-key)
        - 📊 500 requests/day
        - 🎯 Data finansial yang lebih lengkap dan akurat
        """)

# ====================================================================
# MAIN APPLICATION
# ====================================================================
def main():
    """Main application function"""
    
    # Load CSS
    load_css()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Aplikasi Prediksi Kebangkrutan Multi-Model</h1>
        <p>Analisis Keuangan dengan Data Real-time & Multiple Model Validation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        
        # Data source selection
        data_source = st.selectbox(
            "📊 Pilih Sumber Data:",
            ["YFinance (Gratis)", "Alpha Vantage (API Key)", "Input Manual"],
            help="YFinance: Data gratis tanpa API key\nAlpha Vantage: Perlu API key, data lebih akurat"
        )
        
        # API Key input
        api_key = None
        if "Alpha Vantage" in data_source:
            st.subheader("🔑 Alpha Vantage API")
            api_key = st.text_input(
                "API Key:",
                type="password",
                help="Daftar gratis: https://www.alphavantage.co/support/#api-key"
            )
            
            if api_key:
                st.success("✅ API Key tersimpan")
            else:
                st.warning("⚠️ API Key diperlukan untuk Alpha Vantage")
            
            st.info("📝 **Free Tier:** 500 requests/day, 5 requests/minute")
        
        # Input section
        if data_source != "Input Manual":
            st.subheader("📈 Input Ticker Saham")
            
            # Ticker suggestions
            ticker_type = st.radio(
                "Pilih jenis ticker:",
                ["Ticker Populer", "Emiten Pailit", "Custom Input"],
                help="Pilih kategori untuk suggestions atau input manual"
            )
            
            if ticker_type == "Ticker Populer":
                ticker_input = st.selectbox("Pilih Ticker:", [""] + POPULAR_TICKERS)
            elif ticker_type == "Emiten Pailit":
                ticker_input = st.selectbox("Pilih Emiten Pailit:", [""] + BANKRUPT_COMPANIES)
            else:
                ticker_input = st.text_input(
                    "Custom Ticker:",
                    value="BBRI.JK",
                    placeholder="Contoh: BBRI.JK, TLKM.JK"
                )
            
            # Quick ticker buttons
            st.markdown("**⚡ Quick Access:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("BBRI.JK", use_container_width=True):
                    ticker_input = "BBRI.JK"
                    st.rerun()
            with col2:
                if st.button("MYRX.JK", use_container_width=True):
                    ticker_input = "MYRX.JK"
                    st.rerun()
            
            # Analysis button
            analyze_btn = st.button(
                "🚀 Analisis Sekarang!", 
                type="primary", 
                use_container_width=True,
                disabled=not ticker_input or (data_source == "Alpha Vantage (API Key)" and not api_key)
            )
        
        else:
            # Manual input form
            st.subheader("✏️ Input Data Manual")
            
            with st.form("manual_form"):
                company_name = st.text_input("Nama Perusahaan", "PT Manual Input Tbk")
                
                st.markdown("**📊 Data Keuangan (dalam Rupiah):**")
                
                col1, col2 = st.columns(2)
                with col1:
                    current_assets = st.number_input(
                        "Current Assets", 
                        min_value=0.0, 
                        value=0.0, 
                        format="%.0f",
                        help="Aset lancar perusahaan"
                    )
                    total_assets = st.number_input(
                        "Total Assets", 
                        min_value=0.0, 
                        value=0.0, 
                        format="%.0f",
                        help="Total aset perusahaan"
                    )
                    total_revenue = st.number_input(
                        "Total Revenue", 
                        min_value=0.0, 
                        value=0.0, 
                        format="%.0f",
                        help="Pendapatan total"
                    )
                    net_income = st.number_input(
                        "Net Income", 
                        value=0.0, 
                        format="%.0f",
                        help="Laba bersih (bisa negatif)"
                    )
                
                with col2:
                    current_liabilities = st.number_input(
                        "Current Liabilities", 
                        min_value=0.0, 
                        value=0.0, 
                        format="%.0f",
                        help="Utang lancar"
                    )
                    total_liabilities = st.number_input(
                        "Total Liabilities", 
                        min_value=0.0, 
                        value=0.0, 
                        format="%.0f",
                        help="Total utang"
                    )
                    ebit = st.number_input(
                        "EBIT", 
                        value=0.0, 
                        format="%.0f",
                        help="Earnings Before Interest & Tax"
                    )
                    retained_earnings = st.number_input(
                        "Retained Earnings", 
                        value=0.0, 
                        format="%.0f",
                        help="Laba ditahan"
                    )
                
                market_cap = st.number_input(
                    "Market Cap", 
                    min_value=0.0, 
                    value=0.0, 
                    format="%.0f",
                    help="Nilai pasar perusahaan"
                )
                
                analyze_btn = st.form_submit_button(
                    "🧮 Hitung Prediksi", 
                    type="primary",
                    use_container_width=True
                )
    
    # Main content
    if data_source == "Input Manual" and analyze_btn:
        if total_assets > 0:
            manual_data = {
                'company_name': company_name,
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_revenue': total_revenue,
                'ebit': ebit,
                'net_income': net_income,
                'retained_earnings': retained_earnings,
                'market_cap': market_cap if market_cap > 0 else total_assets - total_liabilities,
                'total_equity': total_assets - total_liabilities,
                'sector': 'Manual Input',
                'industry': 'Manual Input'
            }
            
            process_analysis(manual_data, "Manual Input")
        else:
            st.error("❌ Total Assets harus lebih besar dari 0!")
    
    elif data_source != "Input Manual" and analyze_btn:
        if ticker_input:
            # Get data based on source
            with st.spinner(f"📡 Mengambil data dari {data_source}..."):
                if "YFinance" in data_source:
                    financial_data, error = DataProvider.get_yfinance_data(ticker_input)
                elif "Alpha Vantage" in data_source:
                    financial_data, error = DataProvider.get_alpha_vantage_data(ticker_input, api_key)
                
                if financial_data and not error:
                    process_analysis(financial_data, data_source, ticker_input)
                else:
                    st.error(f"❌ {error}")
                    show_troubleshooting_tips()
        else:
            st.error("❌ Harap masukkan ticker saham!")
    
    else:
        # Welcome screen
        show_welcome_screen()

def process_analysis(financial_data: Dict, data_source: str, ticker: str = None):
    """Process bankruptcy analysis and display results"""
    
    # Display company info
    display_company_info(financial_data, ticker, data_source)
    
    # Perform analysis
    st.subheader("📊 Hasil Analisis Prediksi Kebangkrutan")
    
    # Run all models
    models = {
        'Altman Z-Score': BankruptcyPredictor.altman_z_score,
        'Springate S-Score': BankruptcyPredictor.springate_score,
        'Zmijewski X-Score': BankruptcyPredictor.zmijewski_score,
        'Grover G-Score': BankruptcyPredictor.grover_score
    }
    
    results = {}
    error_models = []
    
    for model_name, model_func in models.items():
        result = model_func(financial_data.copy())
        if 'error' not in result:
            results[model_name] = result
        else:
            error_models.append(f"{model_name}: {result['error']}")
    
    if results:
        # Display model results
        cols = st.columns(2)
        for i, (model_name, result) in enumerate(results.items()):
            display_model_result(model_name, result, cols[i % 2])
        
        # Visual summary
        st.subheader("📈 Ringkasan Visual")
        
        # Risk summary metrics
        risk_counts = pd.Series([result['risk'] for result in results.values()]).value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟢 Risiko Rendah", risk_counts.get('Rendah', 0))
        with col2:
            st.metric("🟡 Risiko Sedang", risk_counts.get('Sedang', 0))
        with col3:
            st.metric("🔴 Risiko Tinggi", risk_counts.get('Tinggi', 0))
        with col4:
            st.metric("📊 Total Model", len(results))
        
        # Risk chart
        fig = create_risk_chart(results)
        st.plotly_chart(fig, use_container_width=True)
        
        # Overall assessment
        show_overall_assessment(risk_counts)
        
        # Model explanations
        with st.expander("📚 Penjelasan Model & Threshold"):
            st.markdown("""
            **🎯 Altman Z-Score:**
            - **Safe Zone (> 3.0)**: Perusahaan sehat, risiko kebangkrutan rendah
            - **Gray Zone (1.8-3.0)**: Perlu perhatian khusus, monitoring ketat
            - **Distress Zone (< 1.8)**: Risiko kebangkrutan tinggi
            
            **🌸 Springate S-Score:**
            - **Healthy (> 0.862)**: Kondisi keuangan baik
            - **Bankrupt (≤ 0.862)**: Potensi kesulitan keuangan
            
            **📈 Zmijewski X-Score:**
            - Menggunakan analisis probabilitas kebangkrutan
            - **Healthy**: Probabilitas ≤ 50%
            - **Financial Distress**: Probabilitas > 50%
            
            **⭐ Grover G-Score:**
            - **Healthy (> 0.01)**: Kondisi finansial sehat
            - **Gray Zone (-0.02 to 0.01)**: Perlu monitoring
            - **Bankrupt (≤ -0.02)**: Risiko kebangkrutan tinggi
            """)
        
        # Show errors if any
        if error_models:
            with st.expander("⚠️ Model dengan Error"):
                for error in error_models:
                    st.warning(error)
    
    else:
        st.error("❌ Tidak ada model yang dapat dijalankan dengan data yang tersedia")
        if error_models:
            for error in error_models:
                st.error(error)
        show_troubleshooting_tips()

def show_troubleshooting_tips():
    """Show troubleshooting tips"""
    st.info("💡 **Tips Troubleshooting:**")
    st.markdown("""
    - ✅ **Cek format ticker**: Pastikan format benar (contoh: BBRI.JK)
    - 🔄 **Coba ticker lain**: Beberapa emiten mungkin tidak memiliki data lengkap
    - 📡 **Ganti sumber data**: Coba YFinance jika Alpha Vantage bermasalah
    - 🔑 **Periksa API key**: Pastikan API key valid dan belum mencapai limit
    - 📊 **Gunakan manual input**: Jika data API tidak tersedia
    """)

# ====================================================================
# RUN APPLICATION
# ====================================================================
if __name__ == "__main__":
    main()