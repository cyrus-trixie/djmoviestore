const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const app = express();

// Enable CORS for all routes to allow frontend access
app.use(cors());

// MySQL Database configuration
const DB_CONFIG = {
  host: 'localhost',
  user: 'root',
  password: '',
  database: 'movie_bot',
  port: 3306
};

// Helper function to get database connection
function getDbConnection() {
  return mysql.createConnection(DB_CONFIG);
}

// Helper function to convert database rows to dictionaries
function rowsToDict(rows) {
  const columns = ['id', 'title', 'video_url', 'poster_url', 'user_id', 'created_at']; // Update columns to match your table
  return rows.map(row => {
    let movie = {};
    columns.forEach((column, index) => {
      movie[column] = row[index]; // Assign each row's value to the corresponding column
    });
    return movie;
  });
}

// Route to get all movies or search by title
app.get('/movies', (req, res) => {
  const searchQuery = req.query.search || '';

  const connection = getDbConnection();
  let query = 'SELECT * FROM movies ORDER BY created_at DESC';

  if (searchQuery) {
    query = 'SELECT * FROM movies WHERE LOWER(title) LIKE ? ORDER BY created_at DESC';
  }

  connection.execute(query, [`%${searchQuery.toLowerCase()}%`], (err, rows) => {
    if (err) {
      console.error('Database error:', err);
      return res.status(500).json({ error: `Database error: ${err.message}` });
    }
    const movies = rowsToDict(rows);
    res.json(movies);
  });
});

// Route to get a single movie by ID
app.get('/movies/:movieId', (req, res) => {
  const movieId = req.params.movieId;

  const connection = getDbConnection();
  const query = 'SELECT * FROM movies WHERE id = ?';

  connection.execute(query, [movieId], (err, rows) => {
    if (err) {
      console.error('Database error:', err);
      return res.status(500).json({ error: `Database error: ${err.message}` });
    }

    if (rows.length > 0) {
      const movie = rowsToDict(rows)[0];
      res.json(movie);
    } else {
      res.status(404).json({ error: 'Movie not found' });
    }
  });
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  const connection = getDbConnection();
  connection.connect(err => {
    if (err) {
      console.error('⚠️ Warning: Could not connect to MySQL database. Check your configuration.');
    } else {
      console.log('✅ Successfully connected to MySQL database');
    }
  });

  console.log(`Server running on http://localhost:${PORT}`);
});
