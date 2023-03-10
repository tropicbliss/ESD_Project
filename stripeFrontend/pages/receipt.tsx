import axios from "axios"
import { useRouter } from "next/router"
import { useEffect, useState } from "react"

const Receipt = () => {
    const router = useRouter()
    
    const [receipt, setReceipt] = useState<string>("")
    useEffect(() => {
        const callApi = async () => {
            const paymentIntentId = router.query.payment_intent
            if(!paymentIntentId){
                return
            }
            console.log("Router info")
            console.log(router.query)
            const response = await axios.post('/api/getPaymentInfo', {
                paymentIntentId: paymentIntentId
            })

            setReceipt(JSON.stringify(response.data))
        }
        callApi()
    }, [router])

    return <div>
        <h1>Receipt</h1>
        {receipt}
    </div>
}
export default Receipt