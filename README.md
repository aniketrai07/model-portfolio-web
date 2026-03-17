# 📊 Model Portfolio Rebalancing App

A Flask-based web application that compares a client's current investments with a predefined model portfolio and generates automated **Buy / Sell / Review** recommendations.

---

## 🚀 Features

* 📈 Portfolio comparison (Current vs Model)
* 🔄 Automatic rebalancing suggestions (BUY / SELL / REVIEW)
* 👥 Multi-client support
* ⚙️ Editable target allocation (Model Portfolio)
* 💾 Save recommendations
* 🕘 Recommendation history tracking
* 📊 Clean and responsive UI (Bootstrap)

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** SQLite
* **Frontend:** HTML, CSS, Bootstrap
* **Deployment:** Render

---

## 📂 Project Structure

```
model-portfolio-app/
│
├── app.py
├── model_portfolio.db
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── investments.html
│   ├── targets.html
│   └── history.html
│
└── static/
    └── style.css
```

---

## ⚙️ How It Works

1. Select a client
2. App fetches current holdings from database
3. Model portfolio allocation is applied
4. System calculates:

   * Total Portfolio Value
   * Target Value
   * Difference
5. Generates actions:

   * **BUY** → Invest more
   * **SELL** → Reduce investment
   * **REVIEW** → Not in model portfolio
6. Save recommendations and view history

---

## ▶️ Run Locally

### 1. Clone repository

```bash
git clone https://github.com/YOUR_USERNAME/model-portfolio-app.git
cd model-portfolio-app
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run app

```bash
python app.py
```

### 4. Open in browser

```
http://127.0.0.1:5000
```

---

## 🌐 Deployment

This project is deployed on **Render**.

Live URL:

```
https://model-portfolio-web.onrender.com
```

---

## 🧠 Problem Solved

Manual portfolio comparison and rebalancing is time-consuming and error-prone.

This application automates:

* Portfolio analysis
* Allocation comparison
* Investment recommendations

---

## 🔮 Future Improvements

* 🔐 User authentication
* 📊 Graph & chart visualization
* 📄 Export to PDF
* 📧 Email notifications
* 🗄️ PostgreSQL integration

---

## 👨‍💻 Author

**Your Name**
GitHub: https://github.com/YOUR_USERNAME

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
