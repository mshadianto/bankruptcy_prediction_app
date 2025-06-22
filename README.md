# 🏦 Aplikasi Prediksi Kebangkrutan Multi-Model

Aplikasi Streamlit untuk prediksi kebangkrutan perusahaan menggunakan 5 model finansial dengan data real-time dari berbagai sumber gratis.

## 🚀 Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd bankruptcy-prediction-app

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run application
streamlit run app/main.py
```

## 📊 Features

- 🎯 **5 Model Prediksi**: Altman, Springate, Zmijewski, Grover
- 📈 **Multiple Data Sources**: YFinance, Alpha Vantage, Manual Input
- 🎨 **Interactive UI**: Modern Streamlit interface
- 📊 **Visual Analytics**: Charts dan risk assessment
- 🔍 **Real-time Analysis**: Data terbaru dari API

## 🛠️ Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
make test

# Format code
make format

# Run linting
make lint
```

## 📁 Project Structure

See project structure in folder tree above.

## 🔑 API Keys

Get free API keys from:
- [Alpha Vantage](https://www.alphavantage.co/support/#api-key) - 500 requests/day
- [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs) - 250 requests/day

## 📄 License

MIT License - see LICENSE file for details.
