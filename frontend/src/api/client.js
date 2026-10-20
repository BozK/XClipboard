// Login 429 copy. retryAfter is the Retry-After header, in seconds
function tooManyAttemptsMessage(retryAfter) {
  const seconds = Number(retryAfter);
  if (!seconds) return "Too many attempts — wait a few minutes";
  const minutes = Math.ceil(seconds / 60);
  return `Too many attempts — wait ${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
}

export const apiClient = {
  async login(username, password) {
    try {
      const response = await fetch(`/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error(tooManyAttemptsMessage(response.headers.get("Retry-After")));
        }
        let errorMessage = "Login failed";
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.detail || errorMessage;
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
      const response = await fetch(`/api/auth/logout`, {
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

  async getMe() {
    try {
      const response = await fetch(`/api/me`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized");
        }
        let errorMessage = "Failed to fetch user info";
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
        throw new Error("Failed to fetch user info - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to fetch user info - unable to connect");
      }
      throw err;
    }
  },

  async getClips() {
    try {
      const response = await fetch(`/api/clips`, {
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
      const response = await fetch(`/api/clip`, {
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

  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      // No Content-Type header: the browser sets the multipart boundary itself
      const response = await fetch(`/api/clip/file`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized");
        }
        let errorMessage = "Failed to upload file";
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.detail || errorMessage;
        } catch (e) {
          // Response wasn't valid JSON, use fallback message
        }
        throw new Error(errorMessage);
      }
      try {
        return await response.json();
      } catch (e) {
        throw new Error("Failed to upload file - invalid server response");
      }
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to upload file - unable to connect");
      }
      throw err;
    }
  },

  // Plain URLs for <img>/<a>: same origin, so the session cookie is sent automatically
  fileUrl(clipId, inline = false) {
    return `/api/clip/${clipId}/file${inline ? "?inline=true" : ""}`;
  },

  thumbUrl(clipId) {
    return `/api/clip/${clipId}/thumb`;
  },

  async deleteClip(clipId) {
    try {
      const response = await fetch(`/api/clip/${clipId}`, {
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
