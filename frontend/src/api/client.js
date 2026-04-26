const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiClient = {
  async login(username, password) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        let errorMessage = "Login failed";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Response wasn't valid JSON, use fallback message
        }
        throw new Error(errorMessage);
      }

      try {
        const data = await response.json();
        return data;
      } catch (e) {
        throw new Error("Login failed - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Login failed - unable to connect");
      }
      throw err;
    }
  },

  async logout() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        let errorMessage = "Logout failed";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Response wasn't valid JSON, use fallback message
        }
        throw new Error(errorMessage);
      }
      try {
        return await response.json();
      } catch (e) {
        throw new Error("Logout failed - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Logout failed - unable to connect");
      }
      throw err;
    }
  },

  async getClips() {
    try {
      const response = await fetch(`${API_BASE_URL}/clips`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized");
        }
        let errorMessage = "Failed to fetch clips";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Response wasn't valid JSON, use fallback message
        }
        throw new Error(errorMessage);
      }
      try {
        return await response.json();
      } catch (e) {
        throw new Error("Failed to fetch clips - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to fetch clips - unable to connect");
      }
      throw err;
    }
  },

  async createClip(text) {
    try {
      const response = await fetch(`${API_BASE_URL}/clip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ clip_text: text }),
      });
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized");
        }
        let errorMessage = "Failed to create clip";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // Response wasn't valid JSON, use fallback message
        }
        throw new Error(errorMessage);
      }
      try {
        return await response.json();
      } catch (e) {
        throw new Error("Failed to create clip - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to create clip - unable to connect");
      }
      throw err;
    }
  },
};
