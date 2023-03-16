const express = require('express');
const morgan = require('morgan');
const mongoose = require('mongoose');
<<<<<<< HEAD
=======
const hotelRoutes = require('./routes/Hotel/Authentication')

const app = express();

const dbURI = 'mongodb+srv://hui:test1234@groomer.3qa6m5d.mongodb.net/groomer?retryWrites=true&w=majority'

// useNewUrlParser: true, useUnifiedTopology: true} to stop deprecation warning
mongoose.connect(dbURI, {useNewUrlParser: true, useUnifiedTopology: true})
    .then((result) => app.listen(5000))
    .catch((error) => console.log(error))

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


app.use(hotelRoutes)







>>>>>>> 64243ee (hashed_pw created, error handling done)


const app = express();