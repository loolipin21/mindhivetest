import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL ;

// Fetch all outlets
export const getAllOutlets = async () => {
  try {
    const response = await axios.get(`${API_URL}/outlets/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching outlets:", error);
    return [];
  }
};

// Search outlets by name
export const searchOutletByName = async (name) => {
  try {
    const response = await axios.get(`${API_URL}/outlets/search/?name=${name}`);
    return response.data;
  } catch (error) {
    console.error("Error searching outlet:", error);
    return [];
  }
};

// Get outlets by city
export const getOutletsByCity = async (city) => {
  try {
    const response = await axios.get(`${API_URL}/outlets/city/?city=${city}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching city outlets:", error);
    return [];
  }
};

// Find nearby outlets
export const getNearbyOutlets = async (lat, lon, radius = 0.05) => {
  try {
    const response = await axios.get(`${API_URL}/outlets/nearby/?lat=${lat}&lon=${lon}&radius=${radius}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching nearby outlets:", error);
    return [];
  }
};

export const getChatbotResponse = async (query, userId) => {
  try {
    const response = await axios.get(
      `${API_URL}/search/?query=${encodeURIComponent(query)}&user_id=${userId}`
    );
    return response.data;
  } catch (error) {
    console.error("Chatbot error:", error);
    return { status: "error", message: "Error processing your request." };
  }
};


export const selectChatbotLocation = async (userId, choice) => {
  try {
    const response = await axios.get(`${API_URL}/select/?user_id=${userId}&choice=${choice}`);
    return response.data;
  } catch (error) {
    console.error("Error selecting location:", error);
    return { status: "error", message: "Error processing your request." };
  }
};