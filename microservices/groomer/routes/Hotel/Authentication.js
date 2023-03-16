const express = require("express");
// const HotelController = require('../../controllers/Authentication.js')
const hotelController = require('../../controllers/Hotel/Authentication');
const router = express.Router();

router.post('/hotels', hotelController.hotel_post)

module.exports = router;