#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import os
from flask import Flask, redirect, request

import stripe
# This is a public sample test API key.
# Don’t submit any personally identifiable information in requests made with this key.
# Sign in to see your own test API key embedded in code samples.
stripe.api_key = 'sk_test_51MjbeMLUyNHnHR56ghODyP72NgDWRampHyhFefBv9tP6xCc9ySabM2BipAaCnl6vfjDY6o97LWgeztMcyxy19SBF00yJjf0L6H'

app = Flask(__name__,
            static_url_path='',
            static_folder='public')

YOUR_DOMAIN = 'http://localhost:4242'

customer_3_items = [
    {'product_id': 'price_1MjcO8LUyNHnHR56qLlSI1Xa', 'quantity': 1},
    {'product_id': 'price_1Mk5bgLUyNHnHR56sV912KTa', 'quantity': 1},
    {'product_id': 'price_1Mk5c7LUyNHnHR561ur9ZA4w', 'quantity': 1},
]

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        this_line_items = []
        for key in request.form:
            if key.startswith('checkbox_') and request.form.get(key) is not None:
                this_line_items.append({
                    'price': request.form.get(key),
                    'quantity': 1,
                })
        print(this_line_items)
        checkout_session = stripe.checkout.Session.create(
            line_items = this_line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/make-refund', methods=['POST'])
def make_refund():
    try:
        stripe.Refund.create(payment_intent="pi_3Mk6SlLUyNHnHR5619vpIbxf")
    except Exception as e:
        return str(e)
    return redirect("success.html")

@app.route('/create-product', methods=['POST'])
def create_product():
    try:
        stripe.Product.create(
        name="Basic Dashboard",
        default_price_data={
            "unit_amount": 1000,
            "currency": "usd",
            "recurring": {"interval": "month"},
        },
        expand=["default_price"],
        )
    except Exception as e:
        return str(e)
    return redirect("success.html")

@app.route('/edit-product', methods=['POST'])
def edit_product():
    stripe.Product.modify("id", name="Updated Product")

@app.route('/create-price',methods=['POST'])
def create_price():
    stripe.Price.create(
        product='{{PRODUCT_ID}}',
        unit_amount=1000,
        currency="usd",
        recurring={"interval": "month"},
    )

if __name__ == '__main__':
    app.run(port=4242)