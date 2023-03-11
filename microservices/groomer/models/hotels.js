const mongoose = require("mongoose");

const hotelSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, "A Hotel Must Have a Name"],
  },
  address: {
    type: String, 
    PIN: {
      type: Number,
      minlength: 6,
      maxlength: 6,
    },
    landmark: String,
  },
  contact_no: {
    type: String,
    minLength: 10,
    maxlength: 10,
    unqiue: true,
  },

  email: {
    type: String,
    required: [true, "A Hotel must have an email address for business emails"],
    unqiue: true,
  },
  password: {
    type: String,
  },
  
  petsAllowed: [String],
 
  services: [String],

  images: [
    {
      public_id: String,
      secure_url: String,
    },
  ],
  membership_tier: [String],
    
  otp: {
    type: "String",
  },
  otpValidUpto: Date,
});

//creating a model for hotel
const Hotel = mongoose.model("hotel", hotelSchema);
module.exports = Hotel;
