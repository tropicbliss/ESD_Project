const  mongoose = require('mongoose');
const Schema = mongoose.Schema;

const groomerSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    picture_url: {
        type: String,
        required: true
    },
    capacity: {
        type: Number,
        required: true
    },
    address: {
        type: String,
        required: true
    },
    contact_no:{
        type: String,
        required: true
    },
    email:{
        type: String,
        required: true
    },
    pet_types:{
        type: [String],
        required: true
    }
}, {timestamps: true})

const Groomer = mongoose.model('Groomer', groomerSchema);
module.exports = Groomer;


