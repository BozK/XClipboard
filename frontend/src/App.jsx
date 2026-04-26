import { useState, useEffect } from "react";
import { LoginPage } from "./pages/LoginPage";
import { ClipsPage } from "./pages/ClipsPage";
import { apiClient } from "./api/client";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check if user has a valid session on app mount
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Try to fetch clips - if this works, user is authenticated
      await apiClient.getClips();
      setIsAuthenticated(true);
    } catch (err) {
      // If we get Unauthorized or any other error, user is not authenticated
      setIsAuthenticated(false);
    } finally {
      setIsChecking(false);
    }
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  if (isChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-xc-bg">
        <p className="text-xc-brown">Loading...</p>
      </div>
    );
  }

  return isAuthenticated ? (
    <ClipsPage onLogout={handleLogout} />
  ) : (
    <LoginPage onLoginSuccess={handleLoginSuccess} />
  );
}

export default App;
