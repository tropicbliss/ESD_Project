import { loadStripe, Stripe } from '@stripe/stripe-js'
import axios from 'axios'
import { NextApiRequest, NextApiResponse } from 'next'

type Req = {
    method:string,
    body: {
        amount: number,
        currency: string
    }
}


const handler = async (req: Req, res: NextApiResponse) => {
    try{
        const STRIPE_PRIVATE_KEY = process.env.STRIPE_API_KEY!
        const response = await axios.post("https://api.stripe.com/v1/payment_intents", req.body, {
            auth: {
                username: STRIPE_PRIVATE_KEY,
                password: ""
            }, headers: {
                'Content-Type': "application/x-www-form-urlencoded"
            }
        })
        console.log(response.data)
        res.status(200).send({clientSecret: response.data.client_secret})
    } catch(err){
        console.log(err.message)
        res.status(400).send(err.message)
    }
    
}   

export default handler