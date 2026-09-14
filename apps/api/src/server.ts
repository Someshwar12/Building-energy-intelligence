import express from "express";
import cors from "cors";

import { config } from "./config/env.js";
import { router } from "./routes/index.js";

const app = express();

app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "building-energy-api",
  });
});

app.use("/api", router);

app.listen(config.port, () => {
  console.log(
    `Building Energy API listening on http://127.0.0.1:${config.port}`,
  );
});