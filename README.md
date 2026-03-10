# Crypto Web App

## Setup Instructions

1. **Install dependencies:**
   pip install -r requirements.txt

2. **Run the server:**
   cd app
   python manage.py runserver

## Page Structure

- `app/templates/`
  - `base.html`
- `app/pages/`
  - `home.html`
- `app/users/`
  - `signup.html`
  - `login.html`
  - `account_overview.html`
- `app/crypto/`
  - `mining.html`
  - `trading.html`
  - `blockchain_viewer.html`
- `app/exchange/`
  - `exchange.html`

## Database Structure

- `Users`
  - `User`
- `Crypto`
  - `Cryptocurrency`
  - `Blockchain`
  - `Block`
  - `Transaction`
  - `TxInput`
  - `TxOutput`
  - `Wallet`
