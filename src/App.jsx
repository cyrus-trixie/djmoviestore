import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

import Final from './components/Final';
import Banner from './components/Banner';

function App() {
    return (
        <Router>
            <div className="app-container">
                {/* You can add a common header, footer, or layout here */}
                <Routes>
                    <Route path="/" element={<Banner />} />
                    <Route path="/home" element={<Final />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
