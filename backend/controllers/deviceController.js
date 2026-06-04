const { scanDevices } = require("../services/deviceService");

exports.getDevices = async (req, res) => {
  try {
    const devices = await scanDevices();
    res.json(devices);
  } catch (err) {
    res.status(500).json({ error: "Scan failed" });
  }
};
