# Aplikasi Prediksi Kebangkrutan Multi-Source
# Jalankan dengan: streamlit run app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import warnings
import time
warnings.filterwarnings('ignore')

# ====================================================================
# KONFIGURASI HALAMAN
# ====================================================================
st.set_page_config(
    page_title="Aplikasi Prediksi Kebangkrutan",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# CSS STYLING
# ====================================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-high {
        border-left-color: #e74c3c !important;
        background: #fdf2f2 !important;
    }
    .risk-medium {
        border-left-color: #f39c12 !important;
        background: #fef9e7 !important;
    }
    .risk-low {
        border-left-color: #27ae60 !important;
        background: #eafaf1 !important;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# CLASS: DATA PROVIDER
# ====================================================================
class DataProvider:
    """Kelas untuk mengambil data dari berbagai sumber gratis"""
    
    def __init__(self):
        self.sources = {
            'YFinance': self.get_yfinance_data,
            'Alpha Vantage': self.get_alpha_vantage_data,
            'Manual Input': self.manual_input
        }
        
    def get_yfinance_data(self, ticker, api_key=None):
        """Mengambil data dari Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Coba ambil data finansial
            try:
                financials = stock.financials
                balance_sheet = stock.balance_sheet
                
                if balance_sheet.empty or financials.empty:
                    return None, "Data finansial tidak tersedia untuk ticker ini"
                
            except Exception as e:
                return None, f"Tidak dapat mengambil laporan keuangan: {str(e)}"
            
            # Extract financial data dengan error handling
            financial_data = self._extract_yfinance_data(balance_sheet, financials, info)
            
            if not financial_data.get('total_assets'):
                return None, "Data keuangan tidak lengkap"
            
            return financial_data, None
            
        except Exception as e:
            return None, f"Error YFinance: {str(e)}"
    
    def _extract_yfinance_data(self, balance_sheet, financials, info):
        """Extract dan bersihkan data dari YFinance"""
        financial_data = {}
        
        # Balance Sheet Items dengan error handling
        try:
            # Coba berbagai nama kolom yang mungkin
            total_assets_keys = ['Total Assets', 'TotalAssets', 'Total assets']
            current_assets_keys = ['Current Assets', 'CurrentAssets', 'Current assets']
            current_liab_keys = ['Current Liabilities', 'CurrentLiabilities', 'Current liabilities']
            total_liab_keys = ['Total Liabilities Net Minority Interest', 'Total Liabilities', 'TotalLiabilities']
            retained_keys = ['Retained Earnings', 'RetainedEarnings', 'Retained earnings']
            equity_keys = ['Total Equity Gross Minority Interest', 'Total Equity', 'TotalEquity', 'Stockholder Equity']
            
            # Extract dengan fallback
            financial_data['total_assets'] = self._safe_extract(balance_sheet, total_assets_keys)
            financial_data['current_assets'] = self._safe_extract(balance_sheet, current_assets_keys)
            financial_data['current_liabilities'] = self._safe_extract(balance_sheet, current_liab_keys)
            financial_data['total_liabilities'] = self._safe_extract(balance_sheet, total_liab_keys)
            financial_data['retained_earnings'] = self._safe_extract(balance_sheet, retained_keys)
            financial_data['total_equity'] = self._safe_extract(balance_sheet, equity_keys)
            
        except Exception as e:
            st.warning(f"Beberapa data balance sheet tidak tersedia: {str(e)}")
        
        # Income Statement Items
        try:
            revenue_keys = ['Total Revenue', 'TotalRevenue', 'Revenue', 'Net Sales']
            ebit_keys = ['EBIT', 'Operating Income', 'OperatingIncome']
            net_income_keys = ['Net Income', 'NetIncome', 'Net income']
            
            financial_data['total_revenue'] = self._safe_extract(financials, revenue_keys)
            financial_data['ebit'] = self._safe_extract(financials, ebit_keys)
            financial_data['net_income'] = self._safe_extract(financials, net_income_keys)
            
        except Exception as e:
            st.warning(f"Beberapa data income statement tidak tersedia: {str(e)}")
        
        # Market data dan info perusahaan
        financial_data['market_cap'] = info.get('marketCap', 0)
        financial_data['company_name'] = info.get('longName', info.get('shortName', 'Unknown'))
        financial_data['sector'] = info.get('sector', 'N/A')
        financial_data['industry'] = info.get('industry', 'N/A')
        financial_data['country'] = info.get('country', 'N/A')
        
        # Hitung missing values
        if not financial_data.get('total_equity') and financial_data.get('total_assets') and financial_data.get('total_liabilities'):
            financial_data['total_equity'] = financial_data['total_assets'] - financial_data['total_liabilities']
        
        return financial_data
    
    def _safe_extract(self, dataframe, possible_keys):
        """Safely extract value from dataframe dengan multiple possible keys"""
        if dataframe.empty:
            return 0
        
        for key in possible_keys:
            if key in dataframe.index:
                try:
                    value = dataframe.loc[key].iloc[0]
                    if pd.notna(value) and value != 0:
                        return float(value)
                except:
                    continue
        return 0
    
    def get_alpha_vantage_data(self, ticker, api_key):
        """Mengambil data dari Alpha Vantage"""
        if not api_key:
            return None, "API Key Alpha Vantage diperlukan"
        
        try:
            # Remove .JK suffix for Alpha Vantage
            symbol = ticker.replace('.JK', '').replace('.', '-')
            
            # Rate limiting
            time.sleep(1)
            
            # Get company overview
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
            overview_response = requests.get(overview_url, timeout=30)
            overview_data = overview_response.json()
            
            if 'Error Message' in overview_data or 'Note' in overview_data:
                return None, "Rate limit atau symbol tidak ditemukan di Alpha Vantage"
            
            if not overview_data or overview_data == {}:
                return None, "Data tidak ditemukan untuk symbol ini"
            
            # Extract basic company info
            financial_data = {}
            financial_data['company_name'] = overview_data.get('Name', symbol)
            financial_data['sector'] = overview_data.get('Sector', 'N/A')
            financial_data['industry'] = overview_data.get('Industry', 'N/A')
            financial_data['market_cap'] = self._safe_float(overview_data.get('MarketCapitalization', 0))
            
            # Get latest financial data from overview
            financial_data['total_assets'] = self._safe_float(overview_data.get('BookValue', 0)) * self._safe_float(overview_data.get('SharesOutstanding', 0))
            financial_data['total_revenue'] = self._safe_float(overview_data.get('RevenueTTM', 0))
            financial_data['ebit'] = self._safe_float(overview_data.get('EBITDA', 0))
            financial_data['net_income'] = self._safe_float(overview_data.get('ProfitMargin', 0)) * financial_data['total_revenue']
            
            # Estimate other values
            pe_ratio = self._safe_float(overview_data.get('PERatio', 0))
            if pe_ratio > 0 and financial_data['net_income'] > 0:
                estimated_earnings = financial_data['market_cap'] / pe_ratio
                financial_data['net_income'] = estimated_earnings
            
            # Basic estimates for missing data
            if not financial_data['total_assets']:
                financial_data['total_assets'] = financial_data['market_cap'] * 1.5  # Rough estimate
            
            financial_data['current_assets'] = financial_data['total_assets'] * 0.4  # Estimate 40%
            financial_data['current_liabilities'] = financial_data['total_assets'] * 0.2  # Estimate 20%
            financial_data['total_liabilities'] = financial_data['total_assets'] * 0.6  # Estimate 60%
            financial_data['total_equity'] = financial_data['total_assets'] - financial_data['total_liabilities']
            financial_data['retained_earnings'] = financial_data['total_equity'] * 0.5  # Estimate 50%
            
            return financial_data, None
            
        except Exception as e:
            return None, f"Error Alpha Vantage: {str(e)}"
    
    def _safe_float(self, value):
        """Safely convert to float"""
        try:
            if value and value != 'None' and value != '-':
                return float(value)
        except:
            pass
        return 0
    
    def manual_input(self, data_dict, api_key=None):
        """Handle manual input data"""
        return data_dict, None

# ====================================================================
# CLASS: BANKRUPTCY PREDICTOR
# ====================================================================
class BankruptcyPredictor:
    def __init__(self):
        self.models = {
            'Altman Z-Score': self.altman_z_score,
            'Altman Modified': self.altman_modified,
            'Springate S-Score': self.springate_score,
            'Zmijewski X-Score': self.zmijewski_score,
            'Grover G-Score': self.grover_score
        }
        
        # Daftar emiten pailit sebagai referensi
        self.bankrupt_companies = [
            'MYRX.JK', 'KPAS.JK', 'FORZ.JK', 'COWL.JK', 'KPAL.JK', 
            'PRAS.JK', 'NIPS.JK', 'BEEF.JK', 'MAMI.JK', 'TOYS.JK',
            'SBAT.JK', 'WMPP.JK', 'ETWA.JK', 'HOTL.JK', 'RICY.JK',
            'TDPM.JK', 'KRAH.JK', 'SRIL.JK'
        ]

    def validate_and_clean_data(self, data):
        """Validasi dan bersihkan data finansial"""
        try:
            # Convert semua ke float
            for key in data:
                if data[key] is None:
                    data[key] = 0
                data[key] = float(data[key]) if data[key] else 0
            
            # Check minimum requirements
            if data.get('total_assets', 0) <= 0:
                return False, "Total Assets harus lebih besar dari 0"
            
            if data.get('current_assets', 0) <= 0:
                return False, "Current Assets harus lebih besar dari 0"
            
            # Auto-fix missing atau invalid data
            if data.get('current_liabilities', 0) <= 0:
                data['current_liabilities'] = data['current_assets'] * 0.3  # Estimate
            
            if data.get('total_liabilities', 0) <= 0:
                data['total_liabilities'] = data['total_assets'] * 0.5  # Estimate
            
            if data.get('total_equity', 0) <= 0:
                data['total_equity'] = data['total_assets'] - data['total_liabilities']
            
            if data.get('ebit', 0) == 0 and data.get('net_income', 0) != 0:
                data['ebit'] = data['net_income'] * 1.2  # Rough estimate
            
            if data.get('market_cap', 0) <= 0:
                data['market_cap'] = data.get('total_equity', data['total_assets'] * 0.4)
            
            return True, "Data valid"
            
        except Exception as e:
            return False, f"Error validasi: {str(e)}"

    def altman_z_score(self, data):
        """Menghitung Altman Z-Score Original"""
        try:
            is_valid, message = self.validate_and_clean_data(data)
            if not is_valid:
                return {'error': message}
            
            # Komponen Z-Score dengan safe division
            x1 = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            x2 = data.get('retained_earnings', 0) / data['total_assets']
            x3 = data.get('ebit', 0) / data['total_assets']
            x4 = data.get('market_cap', 0) / max(data.get('total_liabilities', 1), 1)
            x5 = data.get('total_revenue', 0) / data['total_assets']
            
            # Z-Score calculation
            z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
            
            # Interpretasi
            if z_score < 1.8:
                status = "Distress Zone"
                risk = "Tinggi"
                color = "🔴"
                recommendation = "Hindari investasi - Risiko kebangkrutan tinggi"
            elif z_score < 3.0:
                status = "Gray Zone" 
                risk = "Sedang"
                color = "🟡"
                recommendation = "Hati-hati - Perlu analisis lebih dalam"
            else:
                status = "Safe Zone"
                risk = "Rendah"
                color = "🟢"
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
                }
            }
        except Exception as e:
            return {'error': f"Error Altman: {str(e)}"}

    def altman_modified(self, data):
        """Menghitung Altman Z-Score Modified"""
        try:
            is_valid, message = self.validate_and_clean_data(data)
            if not is_valid:
                return {'error': message}
            
            x1 = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            x2 = data.get('retained_earnings', 0) / data['total_assets']
            x3 = data.get('ebit', 0) / data['total_assets']
            x4 = data.get('total_equity', 0) / max(data.get('total_liabilities', 1), 1)
            x5 = data.get('total_revenue', 0) / data['total_assets']
            
            z_score = 0.717*x1 + 0.847*x2 + 3.107*x3 + 0.42*x4 + 0.998*x5
            
            if z_score < 1.23:
                status = "Distress Zone"
                risk = "Tinggi"
                color = "🔴"
            elif z_score < 2.9:
                status = "Gray Zone"
                risk = "Sedang"
                color = "🟡"
            else:
                status = "Safe Zone"
                risk = "Rendah"
                color = "🟢"
            
            return {
                'score': round(z_score, 3),
                'status': status,
                'risk': risk,
                'color': color,
                'components': {
                    'X1': round(x1, 3),
                    'X2': round(x2, 3),
                    'X3': round(x3, 3),
                    'X4': round(x4, 3),
                    'X5': round(x5, 3)
                }
            }
        except Exception as e:
            return {'error': f"Error Altman Modified: {str(e)}"}

    def springate_score(self, data):
        """Menghitung Springate S-Score"""
        try:
            is_valid, message = self.validate_and_clean_data(data)
            if not is_valid:
                return {'error': message}
            
            a = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            b = data.get('ebit', 0) / data['total_assets']
            c = data.get('ebit', 0) / max(data['current_liabilities'], 1)
            d = data.get('total_revenue', 0) / data['total_assets']
            
            s_score = 1.03*a + 3.07*b + 0.66*c + 0.4*d
            
            if s_score < 0.862:
                status = "Bankrupt"
                risk = "Tinggi"
                color = "🔴"
            else:
                status = "Healthy"
                risk = "Rendah"
                color = "🟢"
            
            return {
                'score': round(s_score, 3),
                'status': status,
                'risk': risk,
                'color': color,
                'components': {
                    'A (WC/TA)': round(a, 3),
                    'B (EBIT/TA)': round(b, 3),
                    'C (EBIT/CL)': round(c, 3),
                    'D (Sales/TA)': round(d, 3)
                }
            }
        except Exception as e:
            return {'error': f"Error Springate: {str(e)}"}

    def zmijewski_score(self, data):
        """Menghitung Zmijewski X-Score"""
        try:
            is_valid, message = self.validate_and_clean_data(data)
            if not is_valid:
                return {'error': message}
            
            x1 = data.get('net_income', 0) / data['total_assets']
            x2 = data.get('total_liabilities', 0) / data['total_assets']
            x3 = data['current_assets'] / max(data['current_liabilities'], 1)
            
            x_score = -4.3 - 4.5*x1 + 5.7*x2 - 0.004*x3
            
            # Prevent overflow
            x_score = max(min(x_score, 50), -50)
            probability = np.exp(x_score) / (1 + np.exp(x_score))
            
            if probability > 0.5:
                status = "Financial Distress"
                risk = "Tinggi"
                color = "🔴"
            else:
                status = "Healthy"
                risk = "Rendah"
                color = "🟢"
            
            return {
                'score': round(x_score, 3),
                'probability': round(probability * 100, 1),
                'status': status,
                'risk': risk,
                'color': color,
                'components': {
                    'X1 (NI/TA)': round(x1, 3),
                    'X2 (TL/TA)': round(x2, 3),
                    'X3 (CA/CL)': round(x3, 3)
                }
            }
        except Exception as e:
            return {'error': f"Error Zmijewski: {str(e)}"}

    def grover_score(self, data):
        """Menghitung Grover G-Score"""
        try:
            is_valid, message = self.validate_and_clean_data(data)
            if not is_valid:
                return {'error': message}
            
            x1 = (data['current_assets'] - data['current_liabilities']) / data['total_assets']
            x2 = data.get('ebit', 0) / data['total_assets']
            x3 = data.get('net_income', 0) / data['total_assets']
            debt_ratio = data.get('total_liabilities', 0) / data['total_assets']
            
            g_score = 1.65*x1 + 3.404*x2 - 0.016*debt_ratio + 0.057
            
            if g_score <= -0.02:
                status = "Bankrupt"
                risk = "Tinggi"
                color = "🔴"
            elif g_score <= 0.01:
                status = "Gray Zone"
                risk = "Sedang"
                color = "🟡"
            else:
                status = "Healthy"
                risk = "Rendah"
                color = "🟢"
            
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
                }
            }
        except Exception as e:
            return {'error': f"Error Grover: {str(e)}"}

# ====================================================================
# MAIN APPLICATION
# ====================================================================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Aplikasi Prediksi Kebangkrutan Multi-Source</h1>
        <p>Analisis Keuangan dengan Data Real-time dari Yahoo Finance & Alpha Vantage</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize providers
    data_provider = DataProvider()
    predictor = BankruptcyPredictor()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        
        # Data source selection
        data_source = st.selectbox(
            "📊 Pilih Sumber Data:",
            ["YFinance (Gratis)", "Alpha Vantage (API Key)", "Input Manual"]
        )
        
        # API Key input if needed
        api_key = None
        if "Alpha Vantage" in data_source:
            st.subheader("🔑 Alpha Vantage API")
            api_key = st.text_input(
                "API Key:",
                type="password",
                help="Daftar gratis: https://www.alphavantage.co/support/#api-key"
            )
            st.info("📝 Free: 500 requests/day")
            
            if not api_key:
                st.warning("⚠️ API Key diperlukan untuk Alpha Vantage")
        
        # Input section based on source
        if data_source != "Input Manual":
            st.subheader("📈 Input Ticker")
            
            # Popular tickers
            popular_tickers = [
                "", "BBRI.JK", "BMRI.JK", "BBCA.JK", "TLKM.JK", 
                "UNVR.JK", "ASII.JK", "GGRM.JK", "KLBF.JK"
            ]
            
            col1, col2 = st.columns([2, 1])
            with col1:
                selected_ticker = st.selectbox("Pilih Ticker:", popular_tickers)
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                use_custom = st.checkbox("Custom")
            
            if use_custom or not selected_ticker:
                ticker_input = st.text_input(
                    "Custom Ticker:",
                    value="BBRI.JK" if not selected_ticker else selected_ticker,
                    placeholder="Contoh: BBRI.JK"
                )
            else:
                ticker_input = selected_ticker
            
            # Bankrupt companies reference
            st.subheader("🚨 Referensi Emiten Pailit")
            bankrupt_cols = st.columns(2)
            for i, company in enumerate(predictor.bankrupt_companies):
                with bankrupt_cols[i % 2]:
                    if st.button(company, key=f"bankrupt_{i}", use_container_width=True):
                        ticker_input = company
                        st.rerun()
            
            # Analyze button
            analyze_button = st.button(
                "🚀 Analisis Sekarang!", 
                type="primary", 
                use_container_width=True
            )
        
        else:
            # Manual input form
            st.subheader("✏️ Input Manual")
            with st.form("manual_form"):
                company_name = st.text_input("Nama Perusahaan", "Manual Input Co.")
                
                st.markdown("**📊 Data Keuangan (dalam Rupiah):**")
                current_assets = st.number_input("Current Assets", min_value=0.0, value=0.0, format="%.0f")
                current_liabilities = st.number_input("Current Liabilities", min_value=0.0, value=0.0, format="%.0f")
                total_assets = st.number_input("Total Assets", min_value=0.0, value=0.0, format="%.0f")
                total_liabilities = st.number_input("Total Liabilities", min_value=0.0, value=0.0, format="%.0f")
                total_revenue = st.number_input("Total Revenue", min_value=0.0, value=0.0, format="%.0f")
                ebit = st.number_input("EBIT", value=0.0, format="%.0f")
                net_income = st.number_input("Net Income", value=0.0, format="%.0f")
                retained_earnings = st.number_input("Retained Earnings", value=0.0, format="%.0f")
                market_cap = st.number_input("Market Cap", min_value=0.0, value=0.0, format="%.0f")
                
                analyze_button = st.form_submit_button("🧮 Hitung Prediksi", type="primary")
    
    # Main content
    if data_source == "Input Manual" and analyze_button:
        if total_assets > 0 and current_assets > 0:
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
                'market_cap': market_cap,
                'total_equity': total_assets - total_liabilities,
                'sector': 'Manual Input',
                'industry': 'Manual Input'
            }
            
            process_analysis(manual_data, predictor, "Manual Input")
        else:
            st.error("❌ Harap masukkan Total Assets dan Current Assets yang valid!")
    
    elif data_source != "Input Manual" and analyze_button:
        if ticker_input:
            if data_source == "Alpha Vantage (API Key)" and not api_key:
                st.error("❌ API Key Alpha Vantage diperlukan!")
                return
            
            # Get data
            with st.spinner(f"📡 Mengambil data dari {data_source}..."):
                if "YFinance" in data_source:
                    financial_data, error = data_provider.get_yfinance_data(ticker_input)
                elif "Alpha Vantage" in data_source:
                    financial_data, error = data_provider.get_alpha_vantage_data(ticker_input, api_key)
                
                if financial_data and not error:
                    process_analysis(financial_data, predictor, data_source, ticker_input)
                else:
                    st.error(f"❌ {error}")
                    st.info("💡 **Troubleshooting:**")
                    st.info("• Cek format ticker (contoh: BBRI.JK)")
                    st.info("• Coba sumber data lain")
                    st.info("• Periksa koneksi internet")
        else:
            st.error("❌ Harap masukkan ticker saham!")
    
    else:
        # Default display
        show_welcome_screen(predictor)

def process_analysis(financial_data, predictor, data_source, ticker=None):
    """Process and display bankruptcy analysis"""
    
    # Company info header
    st.subheader(f"🏢 {financial_data.get('company_name', 'Unknown Company')}")
    
    # Company metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💼 Sektor", financial_data.get('sector', 'N/A'))
        if ticker:
            st.metric("📊 Ticker", ticker)
    
    with col2:
        market_cap = financial_data.get('market_cap', 0)
        if market_cap > 1e12:
            st.metric("💰 Market Cap", f"Rp {market_cap/1e12:.1f}T")
        elif market_cap > 1e9:
            st.metric("💰 Market Cap", f"Rp {market_cap/1e9:.1f}B")
        else:
            st.metric("💰 Market Cap", f"Rp {market_cap/1e6:.1f}M")
    
    with col3:
        total_assets = financial_data.get('total_assets', 0)
        if total_assets > 1e12:
            st.metric("🏛️ Total Assets", f"Rp {total_assets/1e12:.1f}T")
        elif total_assets > 1e9:
            st.metric("🏛️ Total Assets", f"Rp {total_assets/1e9:.1f}B")
        else:
            st.metric("🏛️ Total Assets", f"Rp {total_assets/1e6:.1f}M")
    
    with col4:
        st.metric("📡 Data Source", data_source.split(" ")[0])
        if financial_data.get('current_assets') and financial_data.get('current_liabilities'):
            current_ratio = financial_data['current_assets'] / max(financial_data['current_liabilities'], 1)
            st.metric("📈 Current Ratio", f"{current_ratio:.2f}")
    
    # Bankruptcy analysis
    st.subheader("📊 Hasil Analisis Prediksi Kebangkrutan")
    
    results = {}
    error_models = []
    
    # Run all models
    for model_name, model_func in predictor.models.items():
        result = model_func(financial_data.copy())
        if 'error' not in result:
            results[model_name] = result
        else:
            error_models.append(f"{model_name}: {result['error']}")
    
    if results:
        # Display model results
        cols = st.columns(3)
        for i, (model_name, result) in enumerate(results.items()):
            with cols[i % 3]:
                # Risk-based styling
                risk_class = f"risk-{result['risk'].lower()}"
                
                st.markdown(f"""
                <div class="metric-card {risk_class}">
                    <h4>{result['color']} {model_name}</h4>
                    <h2>{result['score']}</h2>
                    <p><strong>Status:</strong> {result['status']}</p>
                    <p><strong>Risiko:</strong> {result['risk']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if 'probability' in result:
                    st.caption(f"Probabilitas: {result['probability']}%")
                
                # Component details
                with st.expander("📋 Detail Komponen"):
                    for comp, value in result['components'].items():
                        st.text(f"{comp}: {value}")
        
        # Visual summary
        st.subheader("📈 Ringkasan Visual")
        
        # Create summary data
        summary_data = []
        for model_name, result in results.items():
            summary_data.append({
                'Model': model_name,
                'Score': result['score'],
                'Risk': result['risk'],
                'Status': result['status']
            })
        
        df_summary = pd.DataFrame(summary_data)
        
        # Bar chart
        fig = px.bar(
            df_summary,
            x='Model',
            y='Score',
            color='Risk',
            color_discrete_map={'Rendah': '#27ae60', 'Sedang': '#f39c12', 'Tinggi': '#e74c3c'},
            title=f"Analisis Kebangkrutan - {financial_data.get('company_name', 'Company')}",
            text='Score'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=True
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk summary
        st.subheader("🎯 Ringkasan Risiko")
        risk_counts = df_summary['Risk'].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟢 Risiko Rendah", risk_counts.get('Rendah', 0))
        with col2:
            st.metric("🟡 Risiko Sedang", risk_counts.get('Sedang', 0))
        with col3:
            st.metric("🔴 Risiko Tinggi", risk_counts.get('Tinggi', 0))
        with col4:
            st.metric("📊 Total Model", len(results))
        
        # Overall assessment
        high_risk = risk_counts.get('Tinggi', 0)
        medium_risk = risk_counts.get('Sedang', 0)
        low_risk = risk_counts.get('Rendah', 0)
        
        st.subheader("🎯 Kesimpulan & Rekomendasi")
        
        if high_risk >= 3:
            st.error("⚠️ **PERINGATAN TINGGI**: Mayoritas model menunjukkan risiko kebangkrutan tinggi!")
            st.markdown("""
            **🚨 Rekomendasi:**
            - ❌ Hindari investasi pada saham ini
            - 🔍 Lakukan due diligence mendalam jika sudah berinvestasi
            - 📉 Pertimbangkan untuk menjual posisi yang ada
            - 💼 Konsultasi dengan financial advisor
            """)
        elif medium_risk >= 3:
            st.warning("⚠️ **PERHATIAN**: Beberapa model menunjukkan risiko sedang.")
            st.markdown("""
            **⚠️ Rekomendasi:**
            - 👁️ Monitor perkembangan secara berkala
            - 📊 Analisis lebih dalam sebelum investasi tambahan
            - 🔄 Diversifikasi portofolio
            - 📈 Perhatikan tren kinerja keuangan
            """)
        else:
            st.success("✅ **KONDISI BAIK**: Mayoritas model menunjukkan kondisi finansial yang sehat.")
            st.markdown("""
            **✅ Rekomendasi:**
            - 💹 Dapat dipertimbangkan untuk investasi
            - 📊 Lakukan analisis fundamental tambahan
            - 💰 Pertimbangkan sebagai bagian dari portofolio
            - 📈 Monitor kinerja secara berkala
            """)
        
        # Model explanations
        with st.expander("📚 Penjelasan Model"):
            st.markdown("""
            **Altman Z-Score:**
            - Safe Zone (> 3.0): Perusahaan sehat, risiko kebangkrutan rendah
            - Gray Zone (1.8-3.0): Perlu perhatian khusus
            - Distress Zone (< 1.8): Risiko kebangkrutan tinggi
            
            **Springate S-Score:**
            - Healthy (> 0.862): Kondisi keuangan baik
            - Bankrupt (≤ 0.862): Potensi kesulitan keuangan
            
            **Zmijewski X-Score:**
            - Menggunakan probabilitas kebangkrutan
            - > 50%: Financial distress, < 50%: Healthy
            
            **Grover G-Score:**
            - Healthy (> 0.01): Kondisi baik
            - Gray Zone (-0.02 to 0.01): Perlu monitoring
            - Bankrupt (≤ -0.02): Risiko tinggi
            """)
        
        # Show errors if any
        if error_models:
            st.subheader("⚠️ Model dengan Error")
            for error in error_models:
                st.warning(error)
    
    else:
        st.error("❌ Tidak ada model yang dapat dijalankan dengan data yang tersedia")
        if error_models:
            for error in error_models:
                st.error(error)

def show_welcome_screen(predictor):
    """Show welcome screen with instructions"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Cara Menggunakan Aplikasi")
        st.markdown("""
        **1. Pilih Sumber Data:**
        - 🆓 **YFinance**: Gratis, tanpa API key
        - 🔑 **Alpha Vantage**: Perlu API key gratis (500 requests/day)
        - ✏️ **Input Manual**: Masukkan data sendiri
        
        **2. Masukkan Ticker atau Data:**
        - Format ticker: `BBRI.JK`, `TLKM.JK`, dll.
        - Atau pilih dari daftar ticker populer
        
        **3. Analisis Otomatis:**
        - 5 Model prediksi kebangkrutan
        - Visualisasi interaktif
        - Rekomendasi investasi
        """)
        
        st.subheader("📊 Model yang Digunakan")
        models_info = {
            "Altman Z-Score": "Model klasik untuk prediksi kebangkrutan (1968)",
            "Altman Modified": "Versi modifikasi untuk perusahaan private",
            "Springate S-Score": "Model sederhana dengan 4 rasio keuangan", 
            "Zmijewski X-Score": "Menggunakan pendekatan probabilistik",
            "Grover G-Score": "Dikembangkan khusus untuk sektor jasa"
        }
        
        for model, desc in models_info.items():
            st.markdown(f"**{model}:** {desc}")
    
    with col2:
        st.subheader("🚨 Emiten Pailit (Referensi)")
        st.markdown("Daftar emiten yang pernah mengalami kepailitan di BEI:")
        
        # Display bankrupt companies in a nice format
        for i in range(0, len(predictor.bankrupt_companies), 3):
            companies_batch = predictor.bankrupt_companies[i:i+3]
            st.markdown(" • " + " • ".join(companies_batch))
        
        st.info("""
        💡 **Tips:**
        - Gunakan ticker ini untuk testing
        - Bandingkan dengan emiten sehat
        - Perhatikan pola hasil analisis
        """)
        
        st.subheader("🔑 API Key Gratis")
        st.markdown("""
        **Alpha Vantage:**
        - 🔗 [Daftar Gratis](https://www.alphavantage.co/support/#api-key)
        - 📊 500 requests/day
        - 🎯 Data finansial lengkap
        """)

if __name__ == "__main__":
    main()