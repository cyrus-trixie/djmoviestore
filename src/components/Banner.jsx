import img from '../assets/movie.jpg';
import { Link } from 'react-router-dom';
export default function Banner() {
  return (
    <div 
      className="relative flex justify-center items-center h-screen bg-black bg-cover bg-center"
      style={{ backgroundImage: `url(${img})` }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black opacity-90"></div>

      {/* Content */}
      <div className="relative z-10 text-white text-center max-w-md">
        <h1 className="text-3xl font-bold">🔥 Dj Movies Store🔥</h1>
        <p className="text-sm opacity-90">
          Relive the legend! Watch Classic Kiswahili-Narrated Action & Comedy.
        </p>
        
        <Link to='/home'>
        <button className="bg-red-700 text-white px-5 py-2 rounded-md mt-4 hover:bg-red-800 transition">
            Start Watching
          </button>
        </Link>
         
        
      </div>
    </div>
  );
}
