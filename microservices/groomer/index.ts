import { PetType, PrismaClient } from "@prisma/client";
import express from "express";
import { z } from "zod";

const app = express();

const prisma = new PrismaClient();

// const PORT = parseInt(process.env.PORT);

// middleware & static files
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

app.post("/create", async (req, res) => {
  const json = req.body;
  try {
    const schema = z.object({
      name: z.string(),
      pictureUrl: z.string().url(),
      capacity: z.number().min(1),
      address: z.string(),
      contactNo: z.string(),
      email: z.string().email(),
      petType: z.nativeEnum(PetType)
    });
    const parsed = schema.parse(json);
  } catch (err) {
    console.error(err);
    res.status(400);
    res.send({ message: "message is invalid" });
    return;
  }
  res.status(200);
  res.send()
});

app.listen(5000, () => {
  console.log(`Censorer listening on port ${5000}`);
});
