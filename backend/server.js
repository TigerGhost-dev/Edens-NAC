require("dotenv").config();
const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("Eden's NAC Backend Running");
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

const authRoutes = require("./routes/auth");
app.use("/api/auth", authRoutes);

const deviceRoutes = require("./routes/devices");
app.use("/api/devices", deviceRoutes);
