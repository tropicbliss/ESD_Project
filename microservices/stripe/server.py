#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import os
from flask import Flask, redirect, request,jsonify,render_template
import json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,RadioField
# from dotenv import load_dotenv

import stripe
# This is a public sample test API key.
# Don’t submit any personally identifiable information in requests made with this key.
# Sign in to see your own test API key embedded in code samples.
stripe.api_key = 'sk_test_51MjbeMLUyNHnHR56ghODyP72NgDWRampHyhFefBv9tP6xCc9ySabM2BipAaCnl6vfjDY6o97LWgeztMcyxy19SBF00yJjf0L6H'

# load_dotenv()
# stripe.api_key = os.getenv('STRIPE_API_KEY')

app = Flask(__name__,
            static_url_path='',
            static_folder='../../public/stripeTest')
app.config['SECRET_KEY'] = 'very_secret_deh'

YOUR_DOMAIN = 'http://localhost:4242'

class checkoutForm(FlaskForm):
    package = RadioField("svc_lvl")
    quantity = RadioField("days_stay")
    submit = SubmitField("go_checkout")

category = {
    1:"price_1Mkpj7LUyNHnHR562PNuXTIX",
    2: "price_1Mklu5LUyNHnHR56tJ5E1kR0",
    3: "price_1MkpjGLUyNHnHR56BZTSqRRV",
    4: "price_1MkpkBLUyNHnHR56ZpfdO6zp",
    5: "price_1MkluHLUyNHnHR566Fw51VfA",
    6: "price_1Mkpk3LUyNHnHR561qiXISpN",
    7: "price_1MkpjfLUyNHnHR56F0R9Jojl",
    8: "price_1MkpjYLUyNHnHR56Wiw6mTPN",
    9: "price_1MkluULUyNHnHR56ISQ59eIo"
}

@app.route('/test',methods=["GET","POST"])
def index():
    """
    Render the checkout form.
    """
    return render_template("checkout_form.html", checkout_form= checkoutForm())

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        if request.is_json:
            # Parse JSON data from request
            json_data = request.get_json()
            print(json_data)
            # Extract line items from JSON data
            line_items = []
            for item in json_data['cust_checkout']:
                line_item = {
                    'price': item['price_id'],
                    'quantity': item['quantity']
                }
                line_items.append(line_item)
        else:
            # Extract line items from form data
            print(request.form.get('price_id'))
            line_items = [{
                'price': request.form.get('price_id'),
                'quantity': request.form.get('quantity')
            }]
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
            discounts = [{"coupon":"d1LybAG0"}],
        )
        # Return session ID to client
        
    except stripe.error.StripeError as e:
        return jsonify(error=str(e)), 500

    if request.is_json:
        return jsonify(checkout_url=checkout_session.url)
    else:
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