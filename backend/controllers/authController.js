const pool = require("../config/db");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");

exports.register = async (req, res) => {
  const { username, password } = req.body;

  const hashed = await bcrypt.hash(password, 10);

  try {
    const result = await pool.query(
      "INSERT INTO users (username, password) VALUES ($1, $2) RETURNING *",
      [username, hashed]
    );

    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: "User exists or DB error" });
  }
};

exports.login = async (req, res) => {
  const { username, password } = req.body;

  const result = await pool.query(
    "SELECT * FROM users WHERE username=$1",
    [username]
  );

  if (result.rows.length === 0)
    return res.status(401).json({ error: "User not found" });

  const user = result.rows[0];

  const match = await bcrypt.compare(password, user.password);

  if (!match)
    return res.status(401).json({ error: "Wrong password" });

  const token = jwt.sign({ id: user.id }, "secret", { expiresIn: "1h" });

  res.json({ token });
};
