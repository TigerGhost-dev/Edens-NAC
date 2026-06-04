const { exec } = require("child_process");
const pool = require("../config/db");

exports.scanDevices = () => {
  return new Promise((resolve, reject) => {
    exec("sudo arp-scan --interface=wlan0 --localnet", async (err, stdout) => {
      if (err) return reject(err);

      const lines = stdout.split("\n");
      const devices = [];

      for (let line of lines) {
        const parts = line.split(/\s+/);
        if (parts.length >= 2 && parts[0].includes("192.168.50")) {
          const ip = parts[0];
          const mac = parts[1];

          devices.push({ ip, mac });

          // Store in DB
          await pool.query(
            `INSERT INTO devices (mac_address, ip_address)
             VALUES ($1, $2)
             ON CONFLICT (mac_address)
             DO UPDATE SET ip_address=$2, last_seen=NOW()`,
            [mac, ip]
          );
        }
      }

      resolve(devices);
    });
  });
};
