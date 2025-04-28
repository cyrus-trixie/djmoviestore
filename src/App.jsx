import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

import Final from './components/Final';
import Banner from './components/Banner'

export default function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Banner />} />
                <Route path="/home" element={<Final />} />
            </Routes>
        </Router>
    );
}
