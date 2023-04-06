const express = require("express");
const PORT = parseInt(process.env.PORT);

const app = express();
app.use(express.static("public"));

app.listen(Number(PORT), "0.0.0.0", () => {
  console.log(`Frontend listening on port ${PORT}`);
});
