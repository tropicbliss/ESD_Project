const express = require("express");
const PORT = 5000;

const app = express();
app.use(express.static("public"));

app.listen(Number(PORT), "127.0.0.1", () => {
  console.log(`Censorer listening on port ${PORT}`);
});
