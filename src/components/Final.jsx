import React, { useState, useEffect } from "react";
import Navbar from "./Nav";

const API_BASE_URL = "https://djmoviestore-backend.onrender.com";

const HeroBanner = ({ featuredMovie, onPlay }) => {
  if (!featuredMovie) return null;

  return (
    <div className="relative w-full h-96 mb-8">
      <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-transparent z-10"></div>
      <div className="absolute inset-0 bg-gradient-to-t from-[#121212] via-transparent to-transparent z-10"></div>
      <img
        src={featuredMovie.poster_url || '/default-poster.jpg'}
        alt={featuredMovie.title}
        className="absolute inset-0 w-full h-full object-cover"
      />
      <div className="relative z-20 flex flex-col justify-end h-full p-8 max-w-2xl">
        <h1 className="text-4xl font-bold mb-2 text-white drop-shadow-lg">{featuredMovie.title}</h1>
        <div className="flex flex-wrap items-center gap-2 mb-2">
          {featuredMovie.category_name && (
            <span className="inline-block bg-red-600 text-white text-sm px-2 py-1 rounded">
              {featuredMovie.category_name}
            </span>
          )}
          {featuredMovie.dj_name && (
            <span className="inline-block bg-purple-600 text-white text-sm px-2 py-1 rounded">
              DJ {featuredMovie.dj_name}
            </span>
          )}
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => onPlay(featuredMovie)}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-md flex items-center space-x-2 transition-colors duration-300"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
            <span>Play Now</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const MovieCategory = ({ title, movies, onMovieClick }) => {
  return (
    <div className="mb-12">
      <h2 className="text-2xl font-bold mb-6 text-white flex items-center">
        {title}
        <span className="ml-2 text-sm font-normal text-gray-400">
          {movies.length} movies
        </span>
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
        {movies.map((movie) => (
          <div
            key={movie.id}
            className="cursor-pointer transform hover:scale-105 transition-transform duration-300"
            onClick={() => onMovieClick(movie)}
          >
            <div className="relative rounded-lg overflow-hidden shadow-lg aspect-[2/3]">
              <img
                src={movie.poster_url || '/default-poster.jpg'}
                alt={movie.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-50 flex items-center justify-center transition-opacity duration-300">
                <div className="opacity-0 hover:opacity-100 transition-opacity duration-300">
                  <div className="p-2 bg-red-600 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
            <h3 className="mt-2 text-gray-200 font-medium truncate">{movie.title}</h3>
            <div className="flex flex-wrap gap-2">
              {movie.category_name && (
                <p className="text-gray-400 text-sm">{movie.category_name}</p>
              )}
              {movie.dj_name && (
                <p className="text-purple-400 text-sm">DJ {movie.dj_name}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function MovieApp() {
  const [movies, setMovies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [djs, setDjs] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [featuredMovie, setFeaturedMovie] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedDJ, setSelectedDJ] = useState(null);
  const [filteredMovies, setFilteredMovies] = useState([]);
  const [activeFilterTab, setActiveFilterTab] = useState("categories"); // 'categories' or 'djs'

  // Fetch all movies, categories and DJs
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch movies
        const moviesResponse = await fetch(`${API_BASE_URL}/movies`);
        const moviesData = await moviesResponse.json();

        // Fetch categories
        const categoriesResponse = await fetch(`${API_BASE_URL}/categories`);
        const categoriesData = await categoriesResponse.json();
        
        // Fetch DJs
        const djsResponse = await fetch(`${API_BASE_URL}/djs`);
        const djsData = await djsResponse.json();

        if (moviesData.success && categoriesData.success && djsData.success) {
          setMovies(moviesData.data);
          setFilteredMovies(moviesData.data);
          setCategories(categoriesData.data);
          setDjs(djsData.data);

          // Set featured movie (random from the list)
          if (moviesData.data.length > 0) {
            setFeaturedMovie(
              moviesData.data[Math.floor(Math.random() * moviesData.data.length)]
            );
          }
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter movies when category, DJ, or search changes
  useEffect(() => {
    const filterMovies = async () => {
      setIsLoading(true);
      try {
        let url = `${API_BASE_URL}/movies`;
        const params = new URLSearchParams();

        if (searchQuery) {
          params.append("search", searchQuery);
        }

        if (selectedCategory) {
          params.append("category_id", selectedCategory);
        }
        
        if (selectedDJ) {
          params.append("dj_id", selectedDJ);
        }

        if (params.toString()) {
          url += `?${params.toString()}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
          setFilteredMovies(data.data);
        }
      } catch (error) {
        console.error("Error filtering movies:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (movies.length > 0) {
      filterMovies();
    }
  }, [searchQuery, selectedCategory, selectedDJ, movies]);

  const playMovie = (movie) => {
    setSelectedMovie(movie);
    setIsPlaying(true);
  };

  const closePlayer = () => {
    setIsPlaying(false);
    setSelectedMovie(null);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    // The useEffect will handle the search automatically
  };

  const getFilterTitle = () => {
    if (selectedDJ) {
      const dj = djs.find(dj => dj.id === selectedDJ);
      return `DJ ${dj?.name || ""}`;
    }
    
    if (selectedCategory) {
      const category = categories.find(c => c.id === selectedCategory);
      return category?.name || "Category";
    }
    
    return "All Movies";
  };

  if (isLoading && movies.length === 0) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#121212] text-white">
      <Navbar />

      <div className="bg-[#1a1a1a] sticky top-0 z-30 px-6 py-4 shadow-lg">
        <div className="max-w-screen-xl mx-auto">
          <form onSubmit={handleSearch} className="flex items-center">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-gray-700 text-white px-4 py-2 rounded-md w-full"
              placeholder="Search for movies"
            />
            <button
              type="submit"
              className="bg-red-600 hover:bg-red-700 px-6 py-2 ml-4 rounded-md text-white"
            >
              Search
            </button>
          </form>

          <div className="flex justify-between mt-4 border-b border-gray-700 pb-2">
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveFilterTab("categories")}
                className={`px-4 py-1 rounded-t-lg ${
                  activeFilterTab === "categories" ? "bg-gray-800 border-b-2 border-red-600" : "bg-transparent"
                }`}
              >
                Categories
              </button>
              <button
                onClick={() => setActiveFilterTab("djs")}
                className={`px-4 py-1 rounded-t-lg ${
                  activeFilterTab === "djs" ? "bg-gray-800 border-b-2 border-purple-600" : "bg-transparent"
                }`}
              >
                DJs
              </button>
            </div>
            <button
              onClick={() => {
                setSelectedCategory(null);
                setSelectedDJ(null);
              }}
              className="text-sm text-gray-400 hover:text-white"
            >
              Clear Filters
            </button>
          </div>

          {activeFilterTab === "categories" && (
            <div className="flex space-x-4 mt-4 overflow-x-auto pb-2 scrollbar-hide">
              <button
                onClick={() => setSelectedCategory(null)}
                className={`px-4 py-1 rounded-full whitespace-nowrap ${
                  selectedCategory === null ? "bg-red-600" : "bg-gray-700 hover:bg-gray-600"
                }`}
              >
                All Categories
              </button>
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-4 py-1 rounded-full whitespace-nowrap ${
                    selectedCategory === category.id ? "bg-red-600" : "bg-gray-700 hover:bg-gray-600"
                  }`}
                >
                  {category.name}
                </button>
              ))}
            </div>
          )}

          {activeFilterTab === "djs" && (
            <div className="flex space-x-4 mt-4 overflow-x-auto pb-2 scrollbar-hide">
              <button
                onClick={() => setSelectedDJ(null)}
                className={`px-4 py-1 rounded-full whitespace-nowrap ${
                  selectedDJ === null ? "bg-purple-600" : "bg-gray-700 hover:bg-gray-600"
                }`}
              >
                All DJs
              </button>
              {djs.map((dj) => (
                <button
                  key={dj.id}
                  onClick={() => setSelectedDJ(dj.id)}
                  className={`px-4 py-1 rounded-full whitespace-nowrap ${
                    selectedDJ === dj.id ? "bg-purple-600" : "bg-gray-700 hover:bg-gray-600"
                  }`}
                >
                  DJ {dj.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {!selectedDJ && !selectedCategory && featuredMovie && <HeroBanner featuredMovie={featuredMovie} onPlay={playMovie} />}

      <div className="px-6 py-8 max-w-screen-xl mx-auto">
        <MovieCategory
          title={getFilterTitle()}
          movies={filteredMovies}
          onMovieClick={playMovie}
        />
      </div>

      {isPlaying && selectedMovie && (
        <div className="fixed inset-0 bg-black bg-opacity-70 z-50">
          <div className="flex justify-center items-center h-full">
            <div className="bg-[#121212] p-8 rounded-lg max-w-4xl w-full">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-white">{selectedMovie.title}</h3>
                <button
                  onClick={closePlayer}
                  className="text-white bg-gray-600 rounded-full p-2 hover:bg-gray-500"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="aspect-video w-full bg-black">
                <video
                  controls
                  autoPlay
                  className="w-full h-full"
                  src={selectedMovie.video_url}
                >
                  Your browser does not support the video tag.
                </video>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {selectedMovie.category_name && (
                  <span className="inline-block bg-red-600 text-white text-sm px-2 py-1 rounded">
                    {selectedMovie.category_name}
                  </span>
                )}
                {selectedMovie.dj_name && (
                  <span className="inline-block bg-purple-600 text-white text-sm px-2 py-1 rounded">
                    DJ {selectedMovie.dj_name}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}