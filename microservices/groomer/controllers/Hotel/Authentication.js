const Hotel = require('../../models/hotels')
const bcrypt = require("bcryptjs");
 
const hotel_post = async(req,res) => {
    console.log(req.body)
    let {name, email, contact_no, address} = req.body;
    
    try{
        if(!name || !email || !contact_no || !address){
            console.log("Insufficient details found!")
        }
        const re1 = new RegExp("^[a-zA-Z ]+$");
        const re2 = new RegExp("^[a-zA-Z0-9._]+@[a-zA-Z.]+$");
        const re3 = new RegExp("^[0-9]{8}$");
        console.log(typeof(contact_no))

        if (!re1.test(name)) throw "Please Enter a Valid Hotel Name";
        if (!re2.test(email)) throw "Please Enter a Valid Email Address of Hotel";
        if (!re3.test(contact_no)) throw "Please Enter a Valid Phone Number of 8 Digits!";

        const checkEmail = await Hotel.findOne({ email: email })
        const checkContact = await Hotel.findOne({contact_no : contact_no})
        console.log(checkEmail)
        console.log(checkContact)
        if(checkEmail){
            console.log('Hotel alrdy exists');
            throw "Hotel Already Registered with this email address! Please Login to Continue!";
        }
        if(checkContact){
            console.log("Contact already exists");
            throw "Hotel Already Registered with this contact number! Please Login to Continue!";
        }
        
        const salt = await bcrypt.genSaltSync(15);
        const encryptedPwd = await bcrypt.hash(req.body.pwd, salt);

        console.log(encryptedPwd);

        let newHotel  = new Hotel({
            name : req.body.name,
            email: req.body.email,
            contact_no : req.body.contact_no,
            address : req.body.address,
            pwd : encryptedPwd,
            petsAllowed : req.body.petsAllowed,
            services : req.body.services,
            memberships: req.body.memberships
        })

        newHotel = await newHotel.save();
        res.status(201).json("Created");
    } 
    catch (error) {
        console.log(error);
        return res.status(400).json(error);
    }
}



module.exports = {
    hotel_post
}




