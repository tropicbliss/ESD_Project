import { loadStripe, Stripe } from '@stripe/stripe-js'
import axios from 'axios'
import { NextApiRequest, NextApiResponse } from 'next'

type Req = {
    method:string,
    body: {
        paymentIntentId: string
    }
}


const handler = async (req: Req, res: NextApiResponse) => {
    try{
        console.log(req.body)
        const STRIPE_PRIVATE_KEY = process.env.STRIPE_API_KEY!
        const response = await axios.get(`https://api.stripe.com/v1/payment_intents/${req.body.paymentIntentId}`, {
            auth: {
                username: STRIPE_PRIVATE_KEY,
                password: ""
            }
        })
        console.log(response.data)
        res.status(200).send({clientSecret: response.data})
    } catch(err){
        console.log(err.message)
        res.status(400).send(err.message)
    }
    
}   

export default handler