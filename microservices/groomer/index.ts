import { PetType, PrismaClient } from "@prisma/client";
import express from "express";
import { every } from "lodash";
import { z } from "zod";

const app = express();

const prisma = new PrismaClient();

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

const priceList = [40, 50, 60, 80, 100, 120, 160, 180, 200]

app.post("/create", async (req, res) => {
  const json = req.body;
  const schema = z.object({
    name: z.string(),
    pictureUrl: z.string().url(),
    capacity: z.number().int().finite().safe().min(1),
    address: z.string(),
    contactNo: z.string(),
    email: z.string().email(),
    petType: z.array(z.nativeEnum(PetType)).min(1),
    basic: z.number().refine((num) => priceList.includes(num)),
    premium: z.number().refine((num) => priceList.includes(num)),
    luxury: z.number().refine((num) => priceList.includes(num))
  });
  try {
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
          create: parsed.petType.map((pet) => {
            return { petType: pet }
          })
        },
        basic: parsed.basic,
        premium: parsed.premium,
        luxury: parsed.luxury
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
        pictureUrl: true,
        basic: true,
        premium: true,
        luxury: true
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
        pictureUrl: true,
        basic: true,
        premium: true,
        luxury: true
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
        basic: true,
        premium: true,
        luxury: true
      }
    });
    if (result) {
      const pets = result.acceptedPets.map((pet) => pet.petType.toString());
      let isAllValid = every(parsed.petTypes, (pet) => pets.includes(pet));
      if (isAllValid) {
        res.status(200)
        res.send({ basic: result.basic, premium: result.premium, luxury: result.luxury })
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
    capacity: z.number().int().finite().safe().optional(),
    address: z.string().optional(),
    contactNo: z.string().optional(),
    email: z.string().email().optional(),
    acceptedPets: z.array(z.nativeEnum(PetType)).min(1).optional(),
    basic: z.number().refine((num) => priceList.includes(num)).optional(),
    premium: z.number().refine((num) => priceList.includes(num)).optional(),
    luxury: z.number().refine((num) => priceList.includes(num)).optional()
  })
  try {
    const parsed = schema.parse(json)
    const updatedAcceptedPets = parsed.acceptedPets?.map((pet) => {
      return { petType: pet }
    });
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
        acceptedPets: updatedAcceptedPets ? {
          deleteMany: {},
          create: updatedAcceptedPets
        } : undefined,
        basic: parsed.basic,
        premium: parsed.premium,
        luxury: parsed.luxury
      },
      select: {
        acceptedPets: true,
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
        pictureUrl: true,
        basic: true,
        premium: true,
        luxury: true
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

app.listen(Number(process.env.PORT), "0.0.0.0", () => {
  console.log(`Groomer listening on port ${process.env.PORT}`);
});
