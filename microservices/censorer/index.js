const express = require("express");
const bodyParser = require("body-parser");
const Filter = require("bad-words");

const PORT = parseInt(process.env.PORT);

const app = express();
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

const filter = new Filter();

app.post("/", (req, res) => {
  const canonicalMsg = req.body.message;
  if (canonicalMsg === undefined) {
    res.status(400);
    res.send({ message: "message is invalid" });
    return;
  }
  let sanitised;
  if (filter.isProfane(canonicalMsg)) {
    sanitised = filter.clean(canonicalMsg);
  } else {
    sanitised = canonicalMsg;
  }
  console.log(`${canonicalMsg} -> ${sanitised}`);
  res.send({ sanitised });
});

app.listen(PORT, () => {
  console.log(`Censorer listening on port ${PORT}`);
});
