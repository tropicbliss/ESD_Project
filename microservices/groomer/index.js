import express from "express";
import { z } from "zod";
import mongoose from "mongoose";
import { Groomer } from "./models.js";
import { every } from "lodash-es";

mongoose.connect(process.env.DATABASE_URL);

const app = express();

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

const PetType = z.enum([
  "Birds",
  "Hamsters",
  "Cats",
  "Dogs",
  "Rabbits",
  "GuineaPigs",
  "Chinchillas",
  "Mice",
  "Fishes",
]);

const priceList = [40, 50, 60, 80, 100, 120, 160, 180, 200];

app.post("/create", async (req, res) => {
  const json = req.body;
  const schema = z.object({
    name: z.string(),
    pictureUrl: z.string().url(),
    address: z.string(),
    contactNo: z.string(),
    email: z.string().email(),
    petType: z.array(PetType).min(1),
    basic: z.number().refine((num) => priceList.includes(num)),
    premium: z.number().refine((num) => priceList.includes(num)),
    luxury: z.number().refine((num) => priceList.includes(num)),
  });
  try {
    const parsed = schema.parse(json);
    const result = await Groomer.findOne(
      {
        name: parsed.name,
      },
      "-_id -__v"
    ).exec();
    if (result) {
      throw new Error();
    }
    const entry = new Groomer({
      ...parsed,
      acceptedPets: parsed.petType,
    });
    await entry.save();
    res.status(200);
    res.send();
  } catch (err) {
    res.status(400);
    res.send({ message: "message is invalid" });
    return;
  }
});

app.get("/search/keyword/:keyword", async (req, res) => {
  const { keyword } = req.params;
  try {
    const regex = new RegExp(keyword, "i");
    const result = await Groomer.find(
      {
        name: regex,
      },
      "-_id -__v"
    ).exec();
    if (result.length > 0) {
      res.status(200);
      res.send(result);
    } else {
      res.status(404);
      res.send({ message: "groomer not found" });
    }
  } catch (err) {
    res.status(400);
    res.send({ message: "internal server error" });
  }
});

app.get("/search/name/:name", async (req, res) => {
  const { name } = req.params;
  try {
    const result = await Groomer.find(
      {
        name,
      },
      "-_id -__v"
    ).exec();
    if (result.length > 0) {
      res.status(200);
      res.send(result);
    } else {
      res.status(404);
      res.send({ message: "groomer not found" });
    }
  } catch (err) {
    res.status(400);
    res.send({ message: "internal server error" });
  }
});

app.post("/accepts/:name", async (req, res) => {
  const { name } = req.params;
  const json = req.body;
  const schema = z.object({
    petTypes: z.array(PetType),
  });
  try {
    const parsed = schema.parse(json);
    const result = await Groomer.findOne(
      {
        name,
      },
      "-_id -__v"
    ).exec();
    if (result) {
      let isAllValid = every(parsed.petTypes, (pet) =>
        result.acceptedPets.includes(pet)
      );
      if (isAllValid) {
        res.status(200);
        res.send({
          basic: result.basic,
          premium: result.premium,
          luxury: result.luxury,
        });
      } else {
        res.status(400);
        res.send({ message: "pet type not accepted" });
      }
    } else {
      res.status(404);
      res.send({ message: "groomer not found" });
    }
  } catch (err) {
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
});

app.post("/update/:name", async (req, res) => {
  const { name } = req.params;
  const json = req.body;
  const schema = z.object({
    pictureUrl: z.string().url().nullable(),
    address: z.string().nullable(),
    contactNo: z.string().nullable(),
    email: z.string().email().nullable(),
    acceptedPets: z.array(PetType).min(1).nullable(),
    basic: z
      .number()
      .refine((num) => priceList.includes(num))
      .nullable(),
    premium: z
      .number()
      .refine((num) => priceList.includes(num))
      .nullable(),
    luxury: z
      .number()
      .refine((num) => priceList.includes(num))
      .nullable(),
  });
  try {
    const parsed = schema.parse(json);
    const query = Object.fromEntries(
      Object.entries(parsed).filter(([_, v]) => v !== null)
    );
    await Groomer.updateOne(
      { name },
      {
        ...query,
      }
    ).exec();
    res.status(200);
    res.send();
  } catch (err) {
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
});

app.post("/read", async (req, res) => {
  const json = req.body;
  const schema = z.object({
    petType: PetType.nullable(),
  });
  try {
    const parsed = schema.parse(json);
    if (parsed.petType) {
      const result = await Groomer.find(
        { acceptedPets: parsed.petType },
        "-_id -__v"
      ).exec();
      res.status(200);
      res.send({ result });
    } else {
      const result = await Groomer.find({}, "-_id -__v").exec();
      res.status(200);
      res.send({ result });
    }
  } catch (err) {
    console.error(err);
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
});

app.get("/delete/:name", async (req, res) => {
  const { name } = req.params;
  try {
    await Groomer.deleteOne({ name }).exec();
    res.status(200);
    res.send();
  } catch (err) {
    res.status(400);
    res.send({ message: "an error has occurred" });
  }
});

app.listen(Number(process.env.PORT), "0.0.0.0", () => {
  console.log(`Groomer listening on port ${process.env.PORT}`);
});
