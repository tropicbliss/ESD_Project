const express = require('express');
const morgan = require('morgan');
const mongoose = require('mongoose');
const Hotel = require('./models/hotels');


const app = express();

const dbURI = 'mongodb+srv://hui:test1234@groomer.3qa6m5d.mongodb.net/groomer?retryWrites=true&w=majority'

// useNewUrlParser: true, useUnifiedTopology: true} to stop deprecation warning
mongoose.connect(dbURI, {useNewUrlParser: true, useUnifiedTopology: true})
    .then((result) => app.listen(5000))
    .catch((error) => console.log(error))


const createService = async (req, res) => {
  try {
    const { name, servicesList } = req.body;

    //create the price to Number of
    await Hotel.updateOne(
      { name },
      { $push: { services: { $each: servicesList } } }
    );

    res.status(201).json("Updated");
  } catch (error) {
    res.status(400).json(error);
  }
};

const memberTier = async (req, res) => {
  try {
    const { name, memberships } = req.body;

    //create the price to Number of
    await Hotel.updateOne(
      { name },
      { $push: { membership_tier: { $each: memberships } } }
    );

    res.status(201).json("Updated");
  } catch (error) {
    res.status(400).json(error);
  }
};



app.set('view engine', 'ejs');

// middleware & static files
app.use(express.static('public'));
app.use(express.urlencoded({extended: true}))
app.use(morgan('dev'));

app.get('/', (req, res) => {
  res.redirect('/hotels')
  });


app.get('/hotels', (req, res) => {
  res.render('hotels', { title: 'Partners' });
});


app.post('/hotels', (req, res) => {
  // console.log(req.body)
  const hotel = new Hotel(req.body);
  hotel.save()
      .then((result) =>{
          res.redirect('/hotels')
      })
      .catch((error) =>{
          console.log(error)
      })
      
})

const obj = {
  createService,
  memberTier
};

module.exports = obj;





