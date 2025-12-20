import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard/Dashboard";
import AttendancePage from "./components/Attendance/AttendancePage";
import { faceDetectionService } from "./services/faceDetectionService";

function App() {
  // Preload face detection models on app startup
  useEffect(() => {
    faceDetectionService.ensureModelsLoaded().catch((err) => {
      console.warn("Face detection preload failed, will retry on use:", err);
    });
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/attendance" element={<AttendancePage />} />
      </Routes>
    </Router>
  );
}

export default App;
