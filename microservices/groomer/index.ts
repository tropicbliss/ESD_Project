import { PetType, PrismaClient } from "@prisma/client";
import express from "express";
import { every } from "lodash";
import { z } from "zod";

const app = express();

const prisma = new PrismaClient();

// const PORT = parseInt(process.env.PORT);

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
    res.send({ message: "internal server error" });
  }
})

app.get("/search/name/:name", async (req, res) => {
  const { name } = req.params;
  try {
    const result = await prisma.groomer.findFirst({
      where: {
        name
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
    });
    if (result) {
      const pets = result.acceptedPets.map((pet) => pet.petType.toString());
      const json = { ...result, acceptedPets: pets };
      res.status(200)
      res.send(json)
    } else {
      res.status(404);
      res.send({ message: "groomer not found" })
    }
  } catch (err) {
    res.status(400);
    res.send({ message: "internal server error" });
  }
})

app.post("/accepts/:name", async (req, res) => {
  const { name } = req.params;
  const json = req.body;
  const schema = z.object({
    petTypes: z.array(z.nativeEnum(PetType))
  })
  try {
    const parsed = schema.parse(json);
    const result = await prisma.groomer.findFirst({
      where: {
        name
      },
      select: {
        acceptedPets: true,
      }
    });
    if (result) {
      const pets = result.acceptedPets.map((pet) => pet.petType.toString());
      let isAllValid = every(parsed.petTypes, (pet) => pets.includes(pet));
      if (isAllValid) {
        res.status(200)
        res.send()
      } else {
        res.status(400)
        res.send({ message: "pet type not accepted" })
      }
    } else {
      res.status(404);
      res.send({ message: "groomer not found" })
    }
  } catch (err) {
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
})

app.post("/update/:name", async (req, res) => {
  const { name } = req.params;
  const json = req.body
  const schema = z.object({
    pictureUrl: z.string().url().optional(),
    capacity: z.number().min(1).optional(),
    address: z.string().optional(),
    contactNo: z.string().optional(),
    email: z.string().email().optional(),
    acceptedPets: z.array(z.nativeEnum(PetType)).optional()
  })
  try {
    const parsed = schema.parse(json)
    await prisma.groomer.update({
      where: {
        name,
      },
      data: {
        address: parsed.address,
        capacity: parsed.capacity,
        contactNo: parsed.contactNo,
        email: parsed.email,
        pictureUrl: parsed.pictureUrl,
        acceptedPets: parsed.acceptedPets ? {
        } : undefined
      }
    })
    res.status(200)
    res.send()
  } catch (err) {
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
})

app.post("/read", async (req, res) => {
  const json = req.body;
  const schema = z.object({
    petType: z.nativeEnum(PetType).optional()
  })
  try {
    const parsed = schema.parse(json);
    const result = await prisma.groomer.findMany({
      where: {
        acceptedPets: {
          some: {
            petType: {
              equals: parsed.petType
            }
          }
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
    });
    const j = result.map((groomer) => {
      let pets = groomer.acceptedPets.map((pet) => pet.petType.toString());
      return { ...groomer, acceptedPets: pets }
    })
    res.status(200)
    res.send(j)
  } catch (err) {
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
})

app.listen(5000, () => {
  console.log(`Censorer listening on port ${5000}`);
});
