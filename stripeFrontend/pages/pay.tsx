import PaymentPage from "@/components/PaymentPage"
import axios from "axios"
import { useEffect, useState } from "react"

const Pay = () => {
    const [clientSecret, setClientSecret] = useState<string>("")
    useEffect(() => {
        const callApi = async () => {
            const response = await axios.post(`/api/createPaymentIntent`, {amount: 50, currency: "sgd"})
            console.log(`Client Secret from API: ${response.data.clientSecret}`)
            setClientSecret(response.data.clientSecret)
        }
        callApi()
        
    }, [])

    return (
        <div>
            <h1>Pay me Bitch</h1>
            {
                clientSecret != "" ? <PaymentPage PAYMENT_INTENT_CLIENT_SECRET={clientSecret}></PaymentPage> : <h1>Dickhead</h1>
            }
            
        </div>
    )
}

export default Pay