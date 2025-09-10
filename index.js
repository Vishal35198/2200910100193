import express from "express";

const app = express();
const PORT = 3000;

// Middleware to parse JSON request bodies
app.use(express.json());

// Default route
app.get("/", (req, res) => {
  res.send("Hello Vishal 🚀 — Your Express backend is running!");
});

// Example API: GET users
app.get("/api/users", (req, res) => {
  res.json([
    { id: 1, name: "Vishal" },
    { id: 2, name: "AI Enthusiast" }
  ]);
});

// Example API: POST user
app.post("/api/users", (req, res) => {
  const newUser = req.body;
  res.status(201).json({ message: "User created ✅", user: newUser });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Backend running at http://localhost:${PORT}`);
});
