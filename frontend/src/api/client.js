export const apiClient = {
  async login(username, password) {
    try {
      const response = await fetch(`/auth/login`, {
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
      const response = await fetch(`/auth/logout`, {
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
      const response = await fetch(`/clips`, {
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
      const response = await fetch(`/clip`, {
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

  async deleteClip(clipId) {
    try {
      const response = await fetch(`/clip/${clipId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized");
        }
        if (response.status === 404) {
          throw new Error("Clip not found");
        }
        let errorMessage = "Failed to delete clip";
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
        throw new Error("Failed to delete clip - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to delete clip - unable to connect");
      }
      throw err;
    }
  },
};
