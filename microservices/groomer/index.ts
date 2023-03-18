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
    await prisma.groomer.create({
      data: {
        address: parsed.address,
        capacity: parsed.capacity,
        contactNo: parsed.contactNo,
        email: parsed.email,
        name: parsed.name,
        pictureUrl: parsed.pictureUrl,
        acceptedPets: {
          create: {
            petType: parsed.petType
          }
        }
      }
    })
    res.status(200);
    res.send()
  } catch (err) {
    res.status(400);
    res.send({ message: "message is invalid" });
    return;
  }
});

app.get("/search/keyword/:keyword", async (req, res) => {
  const { keyword } = req.params;
  try {
    const result = await prisma.groomer.findMany({
      where: {
        name: {
          contains: keyword
        }
      },
      select: {
        acceptedPets: true,
        address: true,
        capacity: true,
        contactNo: true,
        email: true,
        name: true,
        pictureUrl: true
      }
    })
    if (result) {
      const json = result.map((groomer) => {
        const pets = groomer.acceptedPets.map((pet) => pet.petType.toString());
        return { ...groomer, acceptedPets: pets }
      })
      res.status(200)
      res.send(json)
    } else {
      res.status(404);
      res.send()
    }
  } catch (err) {
    res.status(400);
    res.send({ message: "message is invalid" });
  }
})

app.listen(5000, () => {
  console.log(`Censorer listening on port ${5000}`);
});
