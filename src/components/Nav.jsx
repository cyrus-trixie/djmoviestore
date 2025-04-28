import { useState } from "react";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="bg-[#111] text-white py-3 px-5 flex justify-between items-center shadow-md relative">
      {/* Logo / Title */}
      <h1 className="text-xl font-bold">🔥 Dj Movie Store 🔥</h1>


      {/* Mobile Menu Button */}
      <button 
        className="md:hidden text-2xl focus:outline-none" 
        onClick={() => setIsOpen(!isOpen)}
      >
        ☰
      </button> 

      {/* Mobile Menu Dropdown */}
      {isOpen && (
        <ul className="absolute top-14 right-5 w-40 bg-[#222] rounded-md shadow-lg md:hidden">
          <li><a href="#" className="block px-4 py-2 text-white hover:bg-red-500">Action</a></li>
          <li><a href="#" className="block px-4 py-2 text-white hover:bg-red-500">Series</a></li>
          <li><a href="#" className="block px-4 py-2 text-white hover:bg-red-500">Horror</a></li>
          <li><a href="#" className="block px-4 py-2 text-white hover:bg-red-500">Comedy</a></li>
        </ul>
      )}
    </nav>
  );
}
