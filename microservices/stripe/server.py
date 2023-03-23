#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import os
from flask import Flask, redirect, request, jsonify, render_template
import json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, SelectField, IntegerField
from wtforms.validators import InputRequired, NumberRange, ValidationError
from flask_cors import CORS

import stripe
# This is a public sample test API key.
# Don’t submit any personally identifiable information in requests made with this key.
# Sign in to see your own test API key embedded in code samples.
# stripe.api_key = 'sk_test_51MjbeMLUyNHnHR56ghODyP72NgDWRampHyhFefBv9tP6xCc9ySabM2BipAaCnl6vfjDY6o97LWgeztMcyxy19SBF00yJjf0L6H'

stripe.api_key = os.getenv('STRIPE_API_KEY')

app = Flask(__name__,
            static_url_path='',
            static_folder='../../public')
app.config['SECRET_KEY'] = 'very_secret_deh'
CORS(app)
# app.debug = True
# YOUR_DOMAIN = "http://localhost:4242"
YOUR_DOMAIN = os.getenv("YOUR_DOMAIN")


class checkoutForm(FlaskForm):
    package = RadioField("svc_lvl")
    quantity = RadioField("days_stay")
    submit = SubmitField("go_checkout")


class customForm(FlaskForm):
    options = [(None, '-'), ('30', '30'), ('40', '40'), ('50', '50')]
    basic = SelectField('Basic', choices=options, validators=[InputRequired()])
    premium = SelectField('Premium', choices=options,
                          validators=[InputRequired()])
    luxury = SelectField('Luxury', choices=options,
                         validators=[InputRequired()])
    custom_price = IntegerField('Custom Price', validators=[
                                InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')


category = {
    40: "price_1Mkpj7LUyNHnHR562PNuXTIX",
    50: "price_1Mklu5LUyNHnHR56tJ5E1kR0",
    60: "price_1MkpjGLUyNHnHR56BZTSqRRV",
    80: "price_1MkpkBLUyNHnHR56ZpfdO6zp",
    100: "price_1MkluHLUyNHnHR566Fw51VfA",
    120: "price_1Mkpk3LUyNHnHR561qiXISpN",
    160: "price_1MkpjfLUyNHnHR56F0R9Jojl",
    180: "price_1MkpjYLUyNHnHR56Wiw6mTPN",
    200: "price_1MkluULUyNHnHR56ISQ59eIo"
}
id = ""


@app.route('/checkout-form', methods=["GET", "POST"])
def index():
    """
    Render the checkout form.
    """
    return render_template("checkout_form.html", checkout_form=checkoutForm())


@app.route('/custom-price-form', methods=["GET", "POST"])
def cpf():
    form = customForm()
    if form.validate_on_submit():
        print("bye")
        # Handle form submission
        basic_price = int(form.basic.data)
        premium_price = int(form.premium.data)
        luxury_price = int(form.luxury.data)
        if isinstance(form.custom_price.data, str) and form.custom_price.data.isdigit():
            custom_price = int(form.custom_price.data)
        else:
            custom_price = None
        # Do something with the form data
        return render_template("base.html")
    return render_template("custom_form.html", form=form)


@app.route('/finish-liao',)
def finish_liao():
    global id
    payment_intent = stripe.checkout.Session.retrieve(id).payment_intent
    return jsonify(payment_intent=payment_intent)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        if request.is_json:
            # Parse JSON data from request
            json_data = request.get_json()
            # Extract line items from JSON data
            line_items = []
            for item in json_data['cust_checkout']:
                line_item = {
                    'price': category[item['price_id']],
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
            success_url=YOUR_DOMAIN + '/stripe_success/success.html',
            cancel_url=YOUR_DOMAIN + '/stripe_success/cancel.html',
            discounts=[{"coupon": "d1LybAG0"}],
        )
        # Return session ID to client

    except stripe.error.StripeError as e:
        return jsonify(error=str(e)), 500
    global id
    id = checkout_session.id
    if request.is_json:
        return jsonify(checkout_url=checkout_session.url, id=id)
    else:
        return redirect(checkout_session.url, code=303)


@app.route('/stripe_webhooks', methods=['POST'])
def webhook():
    event = None
    try:
        # Verify the signature of the incoming webhook request
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature', None)
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe.api_key
        )
    except ValueError as e:
        # Invalid payload or signature
        return jsonify(error=str(e)), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify(error=str(e)), 400

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        print(f"Payment succeeded: {event['data']['object']['id']}")
        return render_template('success_webhook.html', event_json=json.dumps(event))
    elif event.type == 'charge.failed':
        # Do something when a charge fails
        print(f"Charge failed for charge id: {event.data.object.id}")
        return render_template('success_webhook.html', event_json=json.dumps(event))
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True), 200


@app.route('/create-product', methods=['POST'])
def create_product():
    try:
        stripe.Product.create(
            name="Basic Dashboard",
            description="nothing much going on in life",
            default_price_data={
                "unit_amount": 1789,
                "currency": "sgd",
            },
            expand=["default_price"],
        )
    except Exception as e:
        return str(e)
    return redirect("success.html")


@app.route('/make-refund', methods=['POST'])
def make_refund():
    try:
        json_data = request.get_json()
        print(json_data)
        if "id" in json_data and json_data["id"]:
            retrievable = json_data["id"]
            print(retrievable)
            payment_intent = stripe.checkout.Session.retrieve(
                retrievable).payment_intent
        else:
            payment_intent = json_data["payment_intent"]
        print(payment_intent)
        stripe.Refund.create(payment_intent=payment_intent)
    except Exception as e:
        return str(e)
    return "success"

# @app.route('/edit-product', methods=['POST'])
# def edit_product():
#     stripe.Product.modify("id", name="Updated Product")

# @app.route('/create-price',methods=['POST'])
# def create_price():
#     stripe.Price.create(
#         product='{{PRODUCT_ID}}',
#         unit_amount=1000,
#         currency="usd",
#         recurring={"interval": "month"},
#     )


if __name__ == '__main__':
    app.run(port=os.getenv("PORT"), host="0.0.0.0")
    # app.run(port=4242)
