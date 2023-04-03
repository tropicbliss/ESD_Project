import mongoose from 'mongoose'

const groomerSchema = new mongoose.Schema({
	name: String,
	pictureUrl: String,
	address: String,
	contactNo: String,
	email: String,
	basic: Number,
	premium: Number,
	luxury: Number,
	acceptedPets: [String],
})

export const Groomer = mongoose.model('Groomer', groomerSchema, 'groomer')
