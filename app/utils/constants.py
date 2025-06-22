# ====================================================================
# 📄 app/utils/constants.py
# ====================================================================
"""
Constants dan konfigurasi untuk aplikasi prediksi kebangkrutan
"""

# Daftar emiten pailit di BEI
BANKRUPT_COMPANIES = [
    'MYRX.JK', 'KPAS.JK', 'FORZ.JK', 'COWL.JK', 'KPAL.JK', 
    'PRAS.JK', 'NIPS.JK', 'BEEF.JK', 'MAMI.JK', 'TOYS.JK',
    'SBAT.JK', 'WMPP.JK', 'ETWA.JK', 'HOTL.JK', 'RICY.JK',
    'TDPM.JK', 'KRAH.JK', 'SRIL.JK'
]

# Popular tickers untuk testing
POPULAR_TICKERS = [
    "BBRI.JK", "BMRI.JK", "BBCA.JK", "TLKM.JK", "UNVR.JK",
    "ASII.JK", "GGRM.JK", "KLBF.JK", "ICBP.JK", "SMGR.JK",
    "INTP.JK", "JSMR.JK", "PTBA.JK", "ADRO.JK", "ITMG.JK"
]

# Model thresholds
ALTMAN_THRESHOLDS = {
    'distress': 1.8,
    'safe': 3.0
}

SPRINGATE_THRESHOLD = 0.862
ZMIJEWSKI_THRESHOLD = 0.5
GROVER_THRESHOLDS = {
    'bankrupt': -0.02,
    'gray': 0.01
}

# UI Colors
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

# ====================================================================
# 📄 data/bankrupt_companies.csv
# ====================================================================
ticker,company_name,bankruptcy_date,reason,sector
MYRX.JK,PT Hanson International Tbk,2020-09-15,Kasus Jiwasraya,Financial Services
KPAS.JK,PT Cottonindo Ariesta Tbk,2019-03-20,PKPU Gagal,Textile
FORZ.JK,PT Forza Land Indonesia Tbk,2021-07-10,Gagal Bayar Utang,Real Estate
COWL.JK,PT Cowell Development Tbk,2021-05-25,Likuiditas Bermasalah,Real Estate
KPAL.JK,PT Steadfast Marine Tbk,2020-11-30,Industri Pelayaran Terpuruk,Transportation
PRAS.JK,PT Prima Alloy Steel Universal Tbk,2019-08-15,Penurunan Permintaan,Steel
NIPS.JK,PT Nipress Tbk,2020-02-20,Masalah Operasional,Manufacturing
BEEF.JK,PT Estika Tata Tiara Tbk,2018-12-10,Sektor Peternakan Terpuruk,Agriculture
MAMI.JK,PT Mas Murni Indonesia Tbk,2019-06-05,Persaingan Ketat,Jewelry
TOYS.JK,PT Tiga Pilar Sejahtera Food Tbk,2019-01-15,Masalah Korporasi,Consumer Goods

# ====================================================================
# 📄 scripts/setup.py
# ====================================================================
#!/usr/bin/env python3
"""
Setup script untuk aplikasi prediksi kebangkrutan
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Buat direktori yang diperlukan"""
    directories = [
        'app/models',
        'app/data_providers', 
        'app/utils',
        'app/components',
        'app/assets',
        'data/cache',
        'tests',
        'docs/images',
        'config',
        'scripts',
        '.streamlit'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Buat file __init__.py untuk Python packages
        if directory.startswith('app/'):
            (Path(directory) / '__init__.py').touch()
    
    print("✅ Direktori berhasil dibuat")

def create_env_file():
    """Buat file .env dari template"""
    env_content = """# API Keys (isi dengan key yang sesungguhnya)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FMP_API_KEY=your_fmp_key_here

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
CACHE_TTL=3600

# Streamlit Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ File .env berhasil dibuat")

def create_gitignore():
    """Buat file .gitignore"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# Environment Variables
.env
.env.local
.env.production

# Streamlit
.streamlit/secrets.toml

# Data & Logs
data/cache/*
!data/cache/.gitkeep
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Type checking
.mypy_cache/
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ File .gitignore berhasil dibuat")

def install_requirements():
    """Install Python requirements"""
    requirements = [
        "streamlit>=1.28.0",
        "yfinance>=0.2.18", 
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "plotly>=5.15.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0"
    ]
    
    try:
        for req in requirements:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        print("✅ Requirements berhasil diinstall")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")

def create_cache_gitkeep():
    """Buat file .gitkeep untuk folder cache"""
    cache_dir = Path('data/cache')
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / '.gitkeep').touch()

def main():
    """Main setup function"""
    print("🚀 Setting up Bankruptcy Prediction App...")
    
    create_directories()
    create_env_file()
    create_gitignore()
    create_cache_gitkeep()
    
    print("\n📦 Installing Python requirements...")
    install_requirements()
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file dengan API keys Anda")
    print("2. Run: streamlit run app/main.py")
    print("3. Open browser ke http://localhost:8501")

if __name__ == "__main__":
    main()

# ====================================================================
# 📄 tests/test_models.py
# ====================================================================
"""
Unit tests untuk bankruptcy prediction models
"""

import pytest
import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.main import BankruptcyPredictor

class TestBankruptcyModels:
    """Test cases untuk model prediksi kebangkrutan"""
    
    @pytest.fixture
    def sample_healthy_data(self):
        """Sample data untuk perusahaan sehat"""
        return {
            'current_assets': 1000000,
            'current_liabilities': 500000,
            'total_assets': 2000000,
            'total_liabilities': 800000,
            'total_revenue': 1500000,
            'ebit': 200000,
            'net_income': 150000,
            'retained_earnings': 300000,
            'market_cap': 1500000,
            'total_equity': 1200000
        }
    
    @pytest.fixture
    def sample_distressed_data(self):
        """Sample data untuk perusahaan bermasalah"""
        return {
            'current_assets': 500000,
            'current_liabilities': 800000,
            'total_assets': 1000000,
            'total_liabilities': 1200000,
            'total_revenue': 200000,
            'ebit': -50000,
            'net_income': -100000,
            'retained_earnings': -200000,
            'market_cap': 100000,
            'total_equity': -200000
        }
    
    def test_altman_healthy_company(self, sample_healthy_data):
        """Test Altman Z-Score untuk perusahaan sehat"""
        result = BankruptcyPredictor.altman_z_score(sample_healthy_data)
        
        assert 'error' not in result
        assert 'score' in result
        assert result['risk'] in ['Rendah', 'Sedang']
        assert isinstance(result['score'], (int, float))
    
    def test_altman_distressed_company(self, sample_distressed_data):
        """Test Altman Z-Score untuk perusahaan bermasalah"""
        result = BankruptcyPredictor.altman_z_score(sample_distressed_data)
        
        assert 'error' not in result
        assert 'score' in result
        assert result['risk'] in ['Tinggi', 'Sedang']
    
    def test_springate_model(self, sample_healthy_data):
        """Test Springate S-Score"""
        result = BankruptcyPredictor.springate_score(sample_healthy_data)
        
        assert 'error' not in result
        assert 'score' in result
        assert 'status' in result
        assert result['status'] in ['Healthy', 'Bankrupt']
    
    def test_zmijewski_model(self, sample_healthy_data):
        """Test Zmijewski X-Score"""
        result = BankruptcyPredictor.zmijewski_score(sample_healthy_data)
        
        assert 'error' not in result
        assert 'score' in result
        assert 'probability' in result
        assert 0 <= result['probability'] <= 100
    
    def test_grover_model(self, sample_healthy_data):
        """Test Grover G-Score"""
        result = BankruptcyPredictor.grover_score(sample_healthy_data)
        
        assert 'error' not in result
        assert 'score' in result
        assert 'status' in result
    
    def test_data_validation(self):
        """Test validasi data"""
        # Test data kosong
        empty_data = {}
        is_valid, message = BankruptcyPredictor.validate_data(empty_data)
        assert not is_valid
        
        # Test data dengan total_assets = 0
        invalid_data = {'total_assets': 0}
        is_valid, message = BankruptcyPredictor.validate_data(invalid_data)
        assert not is_valid
    
    def test_error_handling(self):
        """Test error handling untuk data invalid"""
        invalid_data = {'total_assets': 'invalid'}
        
        result = BankruptcyPredictor.altman_z_score(invalid_data)
        assert 'error' in result

# ====================================================================
# 📄 README.md (Detail)
# ====================================================================

# 🏦 Aplikasi Prediksi Kebangkrutan Multi-Model

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Aplikasi web berbasis Streamlit untuk prediksi kebangkrutan perusahaan menggunakan 4 model finansial dengan data real-time dari berbagai sumber API gratis.

## 🎯 Features

- **4 Model Prediksi**: Altman Z-Score, Springate, Zmijewski, Grover
- **Multiple Data Sources**: Yahoo Finance (gratis), Alpha Vantage (API)
- **Real-time Analysis**: Data terbaru dari API
- **Interactive UI**: Modern Streamlit interface dengan visualisasi
- **Risk Assessment**: Color-coded results dengan rekomendasi investasi
- **Manual Input**: Fleksibilitas input data sendiri

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip atau conda

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd bankruptcy-prediction-app

# 2. Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
python scripts/setup.py

# 5. Run application
streamlit run app/main.py
```

### Manual Setup (Alternative)

```bash
# Install requirements manually
pip install streamlit yfinance pandas numpy plotly requests python-dotenv

# Create basic structure
mkdir -p app data tests
touch app/__init__.py

# Copy main.py file to app/main.py
# Run application
streamlit run app/main.py
```

## 📁 Project Structure

```
bankruptcy-prediction-app/
├── app/
│   ├── main.py              # ✅ Main Streamlit application
│   ├── utils/
│   │   └── constants.py     # Constants dan konfigurasi
│   └── __init__.py
├── data/
│   ├── bankrupt_companies.csv
│   └── cache/
├── tests/
│   └── test_models.py       # Unit tests
├── scripts/
│   └── setup.py             # Setup script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .gitignore
└── README.md
```

## 🎮 Usage

### 1. **Data Sources**

**Yahoo Finance (Default - Gratis)**
- Tidak perlu API key
- Data real-time saham Indonesia
- Cocok untuk testing dan usage harian

**Alpha Vantage (API Key Required)**
- Daftar gratis: https://www.alphavantage.co/support/#api-key
- 500 requests/day gratis
- Data lebih lengkap dan akurat

### 2. **Input Methods**

**Ticker Input**
```
Format: XXXX.JK
Contoh: BBRI.JK, TLKM.JK, UNVR.JK
```

**Manual Input**
- Current Assets, Current Liabilities
- Total Assets, Total Liabilities  
- Revenue, EBIT, Net Income
- Retained Earnings, Market Cap

### 3. **Model Results**

**Altman Z-Score**
- Safe Zone (> 3.0): 🟢 Rendah
- Gray Zone (1.8-3.0): 🟡 Sedang  
- Distress Zone (< 1.8): 🔴 Tinggi

**Springate S-Score**
- Healthy (> 0.862): 🟢 Rendah
- Bankrupt (≤ 0.862): 🔴 Tinggi

**Zmijewski X-Score**
- Probabilitas ≤ 50%: 🟢 Rendah
- Probabilitas > 50%: 🔴 Tinggi

**Grover G-Score**
- Healthy (> 0.01): 🟢 Rendah
- Gray Zone (-0.02 to 0.01): 🟡 Sedang
- Bankrupt (≤ -0.02): 🔴 Tinggi

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

## 📊 Sample Data

**Emiten Sehat untuk Testing:**
- BBRI.JK (Bank BRI)
- UNVR.JK (Unilever)
- TLKM.JK (Telkom)

**Emiten Pailit untuk Referensi:**
- MYRX.JK (Hanson International)
- FORZ.JK (Forza Land)
- KPAS.JK (Cottonindo Ariesta)

## 🔧 Configuration

### Environment Variables (.env)
```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here

# App Settings  
DEBUG=false
LOG_LEVEL=INFO
```

### Streamlit Config (.streamlit/config.toml)
```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- **Edward Altman** - Altman Z-Score model
- **Gordon Springate** - Springate S-Score model  
- **Mark Zmijewski** - Zmijewski X-Score model
- **Jeffrey Grover** - Grover G-Score model
- **Yahoo Finance** - Free financial data API
- **Alpha Vantage** - Financial data API

## 📞 Support

Jika ada pertanyaan atau issues:
1. Check [troubleshooting guide](docs/TROUBLESHOOTING.md)
2. Open GitHub issue
3. Contact: your-email@example.com

---

**⚠️ Disclaimer**: Aplikasi ini untuk tujuan edukatif dan analisis awal. Keputusan investasi sebaiknya mempertimbangkan berbagai faktor lain dan konsultasi dengan ahli keuangan profesional.