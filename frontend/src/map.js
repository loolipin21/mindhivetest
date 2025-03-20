import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import { getAllOutlets, getChatbotResponse, selectChatbotLocation } from "./api";
import "mapbox-gl/dist/mapbox-gl.css";
import * as turf from "@turf/turf";
import { Input, Card, List, Button } from "antd";
import { SearchOutlined, SendOutlined } from "@ant-design/icons";
import "antd/dist/reset.css";

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
mapboxgl.accessToken = MAPBOX_TOKEN;

function MapComponent() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const [outlets, setOutlets] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [selectedOutlet, setSelectedOutlet] = useState(null);
  const [nearbyOutlets, setNearbyOutlets] = useState([]);
  const [markers, setMarkers] = useState([]);
  const [chatQuery, setChatQuery] = useState(""); // Stores user input
  const [chatResponse, setChatResponse] = useState("");
  const [options, setOptions] = useState([]);
  const [userId] = useState(`user_${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    async function fetchData() {
      const data = await getAllOutlets();
      setOutlets(data);
    }
    fetchData();
  }, []);

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/streets-v11",
        center: [101.6869, 3.139],
        zoom: 11,
      });

      mapRef.current.addControl(new mapboxgl.NavigationControl());
    }
  }, []);

  useEffect(() => {
    if (searchQuery.trim().length > 0) {
      const filtered = outlets
        .filter((outlet) =>
          outlet.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
        .slice(0, 3);
      setSuggestions(filtered);
    } else {
      setSuggestions([]);
    }
  }, [searchQuery, outlets]);

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  const clearMapLayers = () => {
    if (!mapRef.current) return;
    const layers = mapRef.current.getStyle().layers;
    if (layers) {
      layers.forEach((layer) => {
        if (layer.id.startsWith("catchment-circle")) {
          if (mapRef.current.getLayer(layer.id)) {
            mapRef.current.removeLayer(layer.id);
          }
          if (mapRef.current.getSource(layer.id)) {
            mapRef.current.removeSource(layer.id);
          }
        }
      });
    }
    if (mapRef.current.getSource("catchment-circle")) {
      mapRef.current.removeLayer("catchment-circle-layer");
      mapRef.current.removeSource("catchment-circle");
    }
  };

  const drawCircle = (center) => {
    if (!mapRef.current) return;
    if (mapRef.current.getSource("catchment-circle")) {
      mapRef.current.removeLayer("catchment-circle-layer");
      mapRef.current.removeSource("catchment-circle");
    }
    const radiusInMeters = 5000;
    const options = { steps: 64, units: "meters" };
    const circleFeature = turf.circle(center, radiusInMeters, options);
    mapRef.current.addSource("catchment-circle", {
      type: "geojson",
      data: circleFeature,
    });
    mapRef.current.addLayer({
      id: "catchment-circle-layer",
      type: "fill",
      source: "catchment-circle",
      layout: {},
      paint: {
        "fill-color": "#007bff",
        "fill-opacity": 0.2,
        "fill-outline-color": "#007bff",
      },
    });
  };

  const handleSelectOutlet = (outlet) => {
    if (!mapRef.current) {
      console.error("Map instance is not initialized.");
      return;
    }
    markers.forEach((marker) => marker.remove());
    setMarkers([]);

    setSelectedOutlet(outlet);
    setSearchQuery(outlet.name);
    setSuggestions([]);

    const { latitude, longitude } = outlet;
    mapRef.current.flyTo({
      center: [parseFloat(longitude), parseFloat(latitude)],
      zoom: 14,
    });

    const nearby = outlets.filter((other) => {
      const distance = calculateDistance(
        parseFloat(latitude),
        parseFloat(longitude),
        parseFloat(other.latitude),
        parseFloat(other.longitude)
      );
      return distance <= 5 && other.id !== outlet.id;
    });
    setNearbyOutlets(nearby);

    clearMapLayers();

    const mainMarker = new mapboxgl.Marker({ color: "red" })
      .setLngLat([parseFloat(longitude), parseFloat(latitude)])
      .setPopup(
        new mapboxgl.Popup().setHTML(`
          <h3 class="text-lg font-semibold">${outlet.name}</h3>
          <p class="text-sm">${outlet.address}</p>
        `)
      )
      .addTo(mapRef.current);
    setMarkers([mainMarker]);

    const newMarkers = nearby.map((nearbyOutlet) => {
      const marker = new mapboxgl.Marker({ color: "blue" })
        .setLngLat([
          parseFloat(nearbyOutlet.longitude),
          parseFloat(nearbyOutlet.latitude),
        ])
        .setPopup(
          new mapboxgl.Popup().setHTML(`
            <h3 class="text-lg font-semibold">${nearbyOutlet.name}</h3>
            <p class="text-sm">${nearbyOutlet.address}</p>
          `)
        )
        .addTo(mapRef.current);
      return marker;
    });
    setMarkers((prev) => [...prev, ...newMarkers]);

    if (mapRef.current.isStyleLoaded()) {
      drawCircle([parseFloat(longitude), parseFloat(latitude)]);
    } else {
      mapRef.current.once("style.load", () => {
        drawCircle([parseFloat(longitude), parseFloat(latitude)]);
      });
    }
  };

  const handleChatSubmit = async () => {
    if (!chatQuery.trim()) return;
  
    if (options && options.length > 0 && !isNaN(chatQuery)) {
      const choice = parseInt(chatQuery, 10);
      if (choice >= 1 && choice <= options.length) {
        await handleSelection(choice);
        setChatQuery("");
        return;
      } else {
        setChatResponse("Invalid selection. Please choose a valid number.");
        setChatQuery("");
        return;
      }
    }
  
    try {
      const response = await getChatbotResponse(chatQuery, userId);
      const receivedOptions = response.options || [];
      if (response.status === "multiple") {
        setOptions(receivedOptions); 
        setChatResponse(response.message);
      } else {
        setOptions([]);
        setChatResponse(response.message);
      }
    } catch (error) {
      setChatResponse("Error processing your request.");
    }
    setChatQuery("");
  };
  
  
  const handleSelection = async (choiceIndex) => {
    console.log(`🔍 User selected choice: ${choiceIndex}`);

    if (choiceIndex < 1 || choiceIndex > options.length) {
        setChatResponse("Invalid selection. Please choose a valid number.");
        return;
    }

    try {
        console.log(`📡 Sending request to selectChatbotLocation: userId=${userId}, choice=${choiceIndex}`);
        
        const response = await selectChatbotLocation(userId, choiceIndex);
        console.log("📩 API Response:", response);

        if (response.status === "success" && response.operating_hours) {
            setChatResponse(`✅ ${response.outlet} is open:\n📅 ${response.operating_hours}`);
        } else {
            setChatResponse(response.message);
        }

        setOptions([]); // Clear options after selection
    } catch (error) {
        console.error("❌ Error processing selection:", error);
        setChatResponse("Error processing your request.");
    }
};


  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-6">
      <header className="text-center mb-6 w-full">
        <h1 className="text-3xl font-bold text-gray-800">Subway Outlets Map</h1>
        <p className="text-lg text-gray-600">
          Find Subway locations and view nearby outlets within a 5KM radius.
        </p>
      </header>

      <div className="w-full max-w-4xl">
        <Card className="mb-4 shadow-md">
          <Input.Search
            placeholder="Search Subway Outlets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="large"
            prefix={<SearchOutlined />}
            onSearch={() => {}}
          />
          {suggestions.length > 0 && (
            <List
              dataSource={suggestions}
              renderItem={(outlet) => (
                <List.Item
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSelectOutlet(outlet)}
                >
                  {outlet.name}
                </List.Item>
              )}
              className="mt-2"
            />
          )}
        </Card>
        <Card className="mb-4 shadow-md p-4">
          <h2 className="text-xl font-bold text-gray-800 mb-2">Chat with Subway Assistant</h2>
          <Input
            placeholder="Ask about Subway outlets..."
            value={chatQuery}
            onChange={(e) => setChatQuery(e.target.value)}
            size="large"
            suffix={
              <Button type="primary" icon={<SendOutlined />} onClick={handleChatSubmit} />
            }
          />

          {/* Display Chatbot Response */}
          {chatResponse && (
            <div className="mt-3 p-3 bg-gray-100 rounded-lg text-gray-800 whitespace-pre-line">
              <strong>Response:</strong> <br />
              {chatResponse}
            </div>
          )}

          {/* Display Multiple Choices if Needed */}
          {options && options.length > 0 && (
            <div className="mt-3 p-3 bg-white border rounded-lg">
              <strong>Select a location:</strong>
              <List
                dataSource={options}
                renderItem={(option, index) => (
                  <List.Item>
                    <Button
                      type="link"
                      onClick={() => handleSelection(index + 1)}
                    >
                      {index + 1}. {option}
                    </Button>
                  </List.Item>
                )}
              />
            </div>
          )}
        </Card>

        <Card className="shadow-lg" bodyStyle={{ padding: 0, height: "500px" }}>
          <div
            ref={mapContainerRef}
            className="w-full h-full rounded-lg"
            style={{ minHeight: "500px" }}
          />
        </Card>
      </div>
    </div>
  );
}

export default MapComponent;
