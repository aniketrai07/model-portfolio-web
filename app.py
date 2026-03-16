from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "model_portfolio.db"))


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_clients():
    conn = get_db_connection()
    clients = conn.execute(
        "SELECT * FROM clients ORDER BY client_name"
    ).fetchall()
    conn.close()
    return clients


def get_client_by_id(client_id):
    conn = get_db_connection()
    client = conn.execute(
        "SELECT * FROM clients WHERE client_id = ?",
        (client_id,)
    ).fetchone()
    conn.close()
    return client


def get_default_client():
    conn = get_db_connection()
    client = conn.execute(
        "SELECT * FROM clients ORDER BY client_id LIMIT 1"
    ).fetchone()
    conn.close()
    return client


def get_model_funds():
    conn = get_db_connection()
    funds = conn.execute(
        "SELECT * FROM model_funds ORDER BY fund_id"
    ).fetchall()
    conn.close()
    return funds


def update_model_targets(form_data):
    conn = get_db_connection()
    cursor = conn.cursor()

    funds = conn.execute("SELECT * FROM model_funds ORDER BY fund_id").fetchall()

    for fund in funds:
        fund_id = fund["fund_id"]
        field_name = f"target_{fund_id}"
        new_value = form_data.get(field_name)

        try:
            new_value = float(new_value)
        except:
            new_value = float(fund["allocation_pct"])

        cursor.execute(
            "UPDATE model_funds SET allocation_pct = ? WHERE fund_id = ?",
            (new_value, fund_id)
        )

    conn.commit()
    conn.close()


def get_client_holdings(client_id):
    conn = get_db_connection()
    holdings = conn.execute(
        "SELECT * FROM client_holdings WHERE client_id = ? ORDER BY fund_id",
        (client_id,)
    ).fetchall()
    conn.close()
    return holdings


def calculate_total_portfolio_value(holdings):
    total = 0
    for holding in holdings:
        total += holding["current_value"]
    return round(total, 2)


def calculate_rebalance(model_funds, holdings):
    total_value = calculate_total_portfolio_value(holdings)

    holdings_map = {}
    for h in holdings:
        holdings_map[h["fund_id"]] = h

    model_fund_ids = set()
    rebalance_data = []
    total_buy = 0
    total_sell = 0

    for fund in model_funds:
        fund_id = fund["fund_id"]
        fund_name = fund["fund_name"]
        target_pct = float(fund["allocation_pct"])

        model_fund_ids.add(fund_id)

        current_value = holdings_map[fund_id]["current_value"] if fund_id in holdings_map else 0
        current_pct = round((current_value / total_value) * 100, 2) if total_value > 0 else 0
        target_value = round((total_value * target_pct) / 100, 2)
        difference = round(target_value - current_value, 2)

        if difference > 0:
            action = "BUY"
            amount = round(difference, 2)
            total_buy += amount
        elif difference < 0:
            action = "SELL"
            amount = round(abs(difference), 2)
            total_sell += amount
        else:
            action = "HOLD"
            amount = 0

        rebalance_data.append({
            "fund_id": fund_id,
            "fund_name": fund_name,
            "current_value": round(current_value, 2),
            "current_pct": current_pct,
            "target_pct": round(target_pct, 2),
            "target_value": target_value,
            "difference": difference,
            "action": action,
            "amount": amount,
            "is_model_fund": 1
        })

    for holding in holdings:
        if holding["fund_id"] not in model_fund_ids:
            current_value = holding["current_value"]
            current_pct = round((current_value / total_value) * 100, 2) if total_value > 0 else 0

            rebalance_data.append({
                "fund_id": holding["fund_id"],
                "fund_name": holding["fund_name"],
                "current_value": round(current_value, 2),
                "current_pct": current_pct,
                "target_pct": 0,
                "target_value": 0,
                "difference": 0,
                "action": "REVIEW",
                "amount": round(current_value, 2),
                "is_model_fund": 0
            })

    total_buy = round(total_buy, 2)
    total_sell = round(total_sell, 2)
    net_cash_needed = round(total_buy - total_sell, 2)

    return {
        "total_value": total_value,
        "rebalance_data": rebalance_data,
        "total_buy": total_buy,
        "total_sell": total_sell,
        "net_cash_needed": net_cash_needed
    }


def save_rebalance_to_db(client_id, result):
    conn = get_db_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO rebalance_sessions
        (client_id, created_at, portfolio_value, total_to_buy, total_to_sell, net_cash_needed, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        created_at,
        result["total_value"],
        result["total_buy"],
        result["total_sell"],
        result["net_cash_needed"],
        "PENDING"
    ))

    session_id = cursor.lastrowid

    for item in result["rebalance_data"]:
        post_rebalance_pct = item["target_pct"] if item["is_model_fund"] == 1 else 0

        cursor.execute("""
            INSERT INTO rebalance_items
            (session_id, fund_id, fund_name, action, amount, current_pct, target_pct, post_rebalance_pct, is_model_fund)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            item["fund_id"],
            item["fund_name"],
            item["action"],
            item["amount"],
            item["current_pct"],
            item["target_pct"],
            post_rebalance_pct,
            item["is_model_fund"]
        ))

    conn.commit()
    conn.close()

def get_rebalance_history():
    conn = get_db_connection()

    sessions = conn.execute("""
        SELECT * FROM rebalance_sessions
        ORDER BY session_id DESC
    """).fetchall()

    history = []

    for session in sessions:
        rebalance_items = conn.execute("""
            SELECT * FROM rebalance_items
            WHERE session_id = ?
            ORDER BY item_id ASC
        """, (session["session_id"],)).fetchall()

        history.append({
            "session_id": session["session_id"],
            "client_id": session["client_id"],
            "created_at": session["created_at"],
            "portfolio_value": session["portfolio_value"],
            "total_to_buy": session["total_to_buy"],
            "total_to_sell": session["total_to_sell"],
            "net_cash_needed": session["net_cash_needed"],
            "status": session["status"],
            "rebalance_items": rebalance_items
        })

    conn.close()
    return history


@app.route("/")
def index():
    clients = get_all_clients()

    selected_client_id = request.args.get("client_id")
    if not selected_client_id:
        default_client = get_default_client()
        selected_client_id = default_client["client_id"] if default_client else None

    if not selected_client_id:
        return "No client found"

    client = get_client_by_id(selected_client_id)
    if not client:
        return "Client not found"

    model_funds = get_model_funds()
    holdings = get_client_holdings(client["client_id"])
    result = calculate_rebalance(model_funds, holdings)

    return render_template(
        "index.html",
        clients=clients,
        client=client,
        total_value=result["total_value"],
        rebalance_data=result["rebalance_data"],
        total_buy=result["total_buy"],
        total_sell=result["total_sell"],
        net_cash_needed=result["net_cash_needed"]
    )


@app.route("/save-recommendation", methods=["POST"])
def save_recommendation():
    client_id = request.form.get("client_id")
    if not client_id:
        return "Client not found"

    client = get_client_by_id(client_id)
    if not client:
        return "Client not found"

    model_funds = get_model_funds()
    holdings = get_client_holdings(client["client_id"])
    result = calculate_rebalance(model_funds, holdings)

    save_rebalance_to_db(client["client_id"], result)

    return redirect(url_for("history"))


@app.route("/investments")
def investments():
    clients = get_all_clients()

    selected_client_id = request.args.get("client_id")
    if not selected_client_id:
        default_client = get_default_client()
        selected_client_id = default_client["client_id"] if default_client else None

    if not selected_client_id:
        return "No client found"

    client = get_client_by_id(selected_client_id)
    if not client:
        return "Client not found"

    holdings = get_client_holdings(client["client_id"])

    return render_template(
        "investments.html",
        clients=clients,
        client=client,
        holdings=holdings
    )


@app.route("/targets", methods=["GET", "POST"])
def targets():
    if request.method == "POST":
        update_model_targets(request.form)
        return redirect(url_for("targets"))

    funds = get_model_funds()
    return render_template("targets.html", funds=funds)


@app.route("/history")
def history():
    sessions = get_rebalance_history()
    return render_template("history.html", sessions=sessions)


if __name__ == "__main__":
    app.run(debug=True)