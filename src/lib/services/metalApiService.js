// src/lib/services/metalApiService.js
const API_URL = 'https://tcpliage-backend.onrender.com';

/**
 * Handles API interactions for the metal part designer
 */
export default {
  API_URL, // Expose for reuse

  /**
   * Get list of company services
   */
  getServices: async () => {
    try {
      const response = await fetch(`${API_URL}/api/services/`);
      if (!response.ok) {
        throw new Error('Failed to fetch services');
      }
      return await response.json();
    } catch (error) {
      console.error('API error:', error);
      return []; // Return empty array on error
    }
  },

  /**
   * Submit a design to the backend for quotation
   */
  submitDesign: async (design) => {
    try {
      const response = await fetch(`${API_URL}/api/metal-piece/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(design),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Error submitting design");
      }

      return await response.json();
    } catch (error) {
      console.error("API error:", error);
      throw error;
    }
  },

  /**
   * Get material options from the server
   */
  getMaterials: async () => {
    try {
      const response = await fetch(`${API_URL}/api/materials-list/`);
      if (!response.ok) {
        throw new Error("Failed to fetch materials");
      }
      return await response.json();
    } catch (error) {
      console.error("API error:", error);
      return [
        {
          id: "steel",
          name: "Steel",
          description: "Strong and durable, good for structural applications",
          density: 7.85,
          maxThickness: 20,
          minThickness: 0.5,
          image: "/images/materials/steel.jpg",
        },
      ];
    }
  },

  /**
   * Get available finishes for a specific material
   */
  getFinishes: async (materialId) => {
    try {
      const response = await fetch(
        `${API_URL}/api/finishes-for-material/?materialId=${materialId}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch finishes");
      }
      return await response.json();
    } catch (error) {
      console.error("API error:", error);
      return [
        {
          id: "none",
          name: "No Finish",
          description: "Raw metal without any coating or treatment",
        },
      ];
    }
  },
};