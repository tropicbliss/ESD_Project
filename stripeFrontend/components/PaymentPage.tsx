import React from 'react';
import ReactDOM from 'react-dom';
import {Elements, PaymentElement} from '@stripe/react-stripe-js';
import {loadStripe} from '@stripe/stripe-js';
import CheckoutForm from './CheckOutForm';

type props = {
    PAYMENT_INTENT_CLIENT_SECRET: string
}
// Make sure to call `loadStripe` outside of a component’s render to avoid
// recreating the `Stripe` object on every render.
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);
function PaymentPage(props: props) {
  console.log("Look here dickhead")
  console.log(props.PAYMENT_INTENT_CLIENT_SECRET)
  const options = {
    // passing the client secret obtained in step 3
    clientSecret: props.PAYMENT_INTENT_CLIENT_SECRET!,
    // Fully customizable with appearance API.
    appearance: {/*...*/},
  };

  return (
    <Elements stripe={stripePromise} options={options}>
      <CheckoutForm />
    </Elements>
  );
};

export default PaymentPage